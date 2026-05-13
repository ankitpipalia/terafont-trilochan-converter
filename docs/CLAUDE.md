# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ Read this first

If you're picking up work on the converter for **accuracy / bug-fixing**, start with `HANDOFF.md`. It has the full session history, what's been verified, what's still open, and a prioritized plan. `NEXT_PROMPT.md` is the user's intended kick-off prompt for that work.

## Project Overview

A static single-page web app that converts Gujarati text between Unicode (Shruti/Noto) and the legacy TeraFont Trilochan encoding. No build system, no package manager — open `index.html` directly in a browser or serve via any static file server.

```bash
# Serve locally
python3 -m http.server 8080
# Then open http://localhost:8080
```

## Architecture

Three files do all the work:

- **`converter.js`** — all conversion logic plus UI event wiring
- **`index.html`** — single-page UI, loads converter.js and style.css
- **`style.css`** — glassmorphism dark-theme styles, responsive layout
- **`TRILOCHA.TTF`** — the TeraFont Trilochan font, served directly and declared via `@font-face` in style.css; also offered as a download

### Conversion logic (`converter.js`)

The converter is built around four lookup tables plus a syllable-aware main loop:

1. **`unicodeToTeraMap`** — single-character Unicode → TeraFont mapping (vowels, consonants, matras, digits, ASCII punctuation that has TeraFont glyphs).
2. **`halfForms`** — half-form glyphs for consonants that use them when followed by `્` + consonant (e.g., ન→g, સ→:, લ→<, બ→a, ભ→e, ચ→r, ધ→w).
3. **`conjunctPatterns`** — only special-shape ligatures and a few `consonant + matra` combos that aren't derivable from the rules (ક્ષ→1F, જ્ઞ→7, ત્ર→+, શ્ર→z, રૂ→~, જી→Ò). Sorted longest-first; these are checked before everything else.
4. **`retroflex`** — set of retroflex consonants (ટ ઠ ડ ઢ ણ) that use `=` instead of `|` for subscript-r.
5. **`teraToUnicodeMap`** — auto-built at startup by inverting `conjunctPatterns` then `unicodeToTeraMap`. Used only by the reverse direction.

**Cluster handling rule** (in `encodeCluster`):

- `c1 + ્ + c2` where `c2 === 'ર'` → `tera(c1) + '|'` (or `'='` if `c1` is retroflex)
- else if `c1` has a half-form → `halfForm(c1) + tera(c2)`
- else → `tera(c1) + tera(c2)` (virama is dropped — no `Í` prefix)

**Encoding quirks:**

- **Short-i matra (`િ`)**: placed BEFORE the consonant glyph in TeraFont. The main loop detects this with a lookahead — for cluster + short-i it emits `l` before the cluster glyphs.
- **Reph (`ર્`)**: emitted as `"` AFTER the full syllable. `preprocessReph` replaces `ર + ્ + consonant` with a private-use marker; the main loop scans the syllable (consonant cluster + matras), converts it, then appends `"`.
- **Subscript-r continuation**: in 3-consonant clusters like `સ્ત્ર`, after `સ્ત` is emitted as `:T`, the orphan `્ + ર` is emitted as `=`.

`convertCluster` is a helper that mirrors the main loop and is called only from inside the reph handler. **If you change main-loop logic, also update `convertCluster`** or behavior inside reph syllables will diverge.

### UI wiring

All DOM wiring is in the `DOMContentLoaded` handler at the bottom of `converter.js`. Mode switching (`unicodeToTera` / `teraToUnicode`) updates labels and `fontFamily` on both textareas so the correct font is applied for display.

### Testing

`converter.js` exports its main functions via CommonJS, so you can test in Node:

```bash
node -e "global.document={addEventListener:()=>{}}; const {convertUnicodeToTera}=require('./converter.js'); console.log(convertUnicodeToTera('ગુજરાત'));"
```

Three test scripts exist:

- **`test_golden.js`** — 106 focused word-level regression tests. **Must always pass 106/106.**
- **`test_examples.js`** — full-file diff against the four `example-*.txt` files. Informational only; never expected to fully pass because expected files contain manual decorative edits.
- **`test_word_diff.js`** — multiset token diff. Best for finding real converter bugs amongst whitespace noise.

```bash
node test_golden.js     # regression suite — must always pass
node test_word_diff.js  # find new bugs
```

The `example-*.txt` files contain Gujarati Unicode input + manually converted expected TeraFont output. **They are the canonical truth** — when online converters or APIs disagree, examples win.
