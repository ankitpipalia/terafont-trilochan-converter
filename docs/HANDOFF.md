# Gujarati Font Converter — AI Agent Handoff

This document is a complete handoff for another AI agent to continue work on this project. It contains everything needed: project context, what's been done, architecture, how to test, known remaining issues, and a prioritized plan for the rest.

---

## 1. Project Summary

A static web app that converts Gujarati text between Unicode (Shruti / Noto) and **TeraFont Trilochan** (a legacy ASCII-mapped font used in legal documents in Gujarat, India).

- **Files:** `index.html`, `style.css`, `converter.js`, `TRILOCHA.TTF` — no build system, no package manager.
- **How to run:** `python3 -m http.server 8080` and open `http://localhost:8080`.
- **Conversion direction in scope:** **Unicode → TeraFont** (the reverse direction exists but is lower priority).

The user has provided four reference files (`example-1.txt` … `example-4.txt`) — each contains Gujarati Unicode input and the expected TeraFont output, manually converted by the user. **These examples are the canonical truth.** Online converters (pramukhfontconverter.com, fontconverter.online) use slightly different TeraFont variants and disagree with the user's examples — when in conflict, **examples win**.

The user's goal: 100% accuracy converting their legal-document examples.

---

## 2. What Has Been Done

### 2.1 Architecture rewrite of `converter.js`

The converter was rewritten around a clean syllable model:

1. **`unicodeToTeraMap`** — single-character mappings (vowels, consonants, matras, digits, punctuation).
2. **`halfForms`** — a separate table for consonants whose **half-form** glyph is used when followed by `્` + consonant. Verified from examples.
3. **`conjunctPatterns`** — only **special-shape ligatures** that aren't derivable from the above (e.g., `ક્ષ → 1F`, `જ્ઞ → 7`, `ત્ર → +`, `શ્ર → z`), plus their short-i variants and a few `consonant + matra` ligatures (`રૂ → ~`, `જી → Ò`).
4. **Smart cluster handling** in the main loop: when `consonant + ્ + consonant` appears:
   - If `c2 === 'ર'` (subscript-r): `tera(c1) + '|'` (or `'='` for retroflex c1).
   - If `c1` has a half-form: `halfForm(c1) + tera(c2)`.
   - Else: just `tera(c1) + tera(c2)` (the virama is dropped — no `Í` prefix).
5. **Short-i (`િ`) lookahead** — if a short-i follows a consonant or cluster, an `l` is emitted **before** the cluster glyphs.
6. **Reph (`ર્`) preprocessing** — `ર + ્ + consonant` is replaced with a private-use marker; the main loop emits `"` **after** the full syllable.
7. **Subscript-r continuation rule** — orphan `્ + ર` (left over after a 2-consonant cluster has already been emitted, e.g. in `સ્ત્ર`) emits `=` (the 3-consonant subscript-r glyph).

### 2.2 Verified mappings

#### Half-forms table (verified from examples — all in `halfForms` in `converter.js`)

| Consonant | Half-form | Evidence |
|-----------|-----------|----------|
| બ | `a` | બ્લોક → `a,MS` |
| ખ | `b` | ખ્વાજા → `bJFHF` |
| ભ | `e` | સભ્ય → `;eI` |
| ચ | `r` | સ્વચ્છાએ → `:JrKFV[` |
| ત | `t` | ત્ય → `tI` |
| ધ | `w` | શુધ્ધ → `X]wW` |
| ન | `g` | ન્ત → `gT` |
| પ | `%` | પ્લોટ → `%,M8` |
| લ | `<` | લ્ક → `<S` |
| વ | `j` | વ્ય → `jI` |
| ષ | `Q` | ષ્ણ → `Q6` |
| સ | `:` | સ્ત → `:T` |

#### Special ligatures (in `conjunctPatterns`)

- `ક્ષ → 1F`, `જ્ઞ → 7`, `ત્ર → +`, `શ્ર → z`
- Short-i variants: `ક્ષિ → l1F`, `જ્ઞિ → l7`, `ત્રિ → l+`, `શ્રિ → lz`
- `શ્ર` + matras: `શ્રી → zL`, `શ્રો → zM`
- Special character combos: `રૂ → ~`, `જી → Ò` (ja + long-i)

#### Punctuation

- `:` → `o`, `(` → `s`, `)` → `f`, `/` → `q`
- `-`, `–`, `—` → `v`
- `"` → `cc`, `'` → `c` (single → c, double → cc)
- Smart quotes (`“ ” ‘ ’`) → cc/cc/c/c

#### Digits

Both Gujarati (`૦૧૨૩૪૫૬૭૮૯ → _!Z#$5&*()`) and Devanagari (`०१२३४५६७८९`) map identically — example-3 mixes them.

#### Independent vowels

`અ → V`, `આ → VF`, `ઇ → >`, `ઈ → .`, `ઉ → p`, `ઊ → é`, `ઋ → °`, `એ → V[`, `ઐ → V{`, **`ઓ → VM`** (was wrong), **`ઔ → VÁ`** (was wrong).

#### Subscript-r distinction

- Normal consonants: `્ + ર → |` (e.g. ક્ર → `S|`, પ્ર → `5|`, ગ્ર → `U|`)
- Retroflex consonants `ટ ઠ ડ ઢ ણ`: `્ + ર → =` (e.g. ટ્ર → `8=`, ડ્ર → `0=`)
- Orphan `્ + ર` after a cluster (3-consonant context): `=` (e.g. સ્ત્ર → `:T=`)

### 2.3 Test infrastructure

Three Node.js test files were created (no test framework — just plain scripts):

1. **`test_golden.js`** — 120 focused word-level tests with verified expected values. **All pass.** This is the regression suite.
2. **`test_examples.js`** — full-file comparison against the four `example-*.txt` files. Default mode is normalized (collapses whitespace); `--strict` for exact match. Currently never expected to fully pass because the example files contain manual decorative edits.
3. **`test_word_diff.js`** — multiset token diff against examples. Most useful for finding real converter bugs amongst whitespace noise.

**Run all tests:** `node test_golden.js && node test_word_diff.js`

---

## 3. Architecture of `converter.js`

```
┌──────────────────────────────────────────────────────────┐
│  unicodeToTeraMap   ← single-char mappings                │
│  halfForms          ← consonant-half-form table           │
│  conjunctPatterns   ← special ligatures (sorted by len)   │
│  retroflex          ← Set of 5 retroflex consonants       │
└──────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │   convertUnicodeToTera     │
              │                            │
              │   1. preprocessReph         │
              │   2. Main loop:             │
              │      a. REPH_MARKER → emit  │
              │         syllable + "        │
              │      b. ligature lookup     │
              │      c. consonant + ્ +    │
              │         consonant → cluster │
              │         (with short-i look- │
              │         ahead)              │
              │      d. consonant + િ →    │
              │         l + tera             │
              │      e. orphan ્ + ર → =   │
              │      f. standalone virama   │
              │         → skip              │
              │      g. standalone short-i  │
              │         → l                 │
              │      h. single-char lookup  │
              └────────────────────────────┘
```

`encodeCluster(c1, c2)`:
```
if c2 === 'ર':
    return tera(c1) + (retroflex.has(c1) ? '=' : '|')
if halfForms[c1]:
    return halfForms[c1] + tera(c2)
return tera(c1) + tera(c2)   # virama dropped
```

`convertCluster(syllable)` is a duplicate of the main loop used by the reph handler (it walks a syllable substring without re-running reph preprocessing).

---

## 4. Known Remaining Issues

The example files have manual edits, so a strict file-level match is never achievable. But there are a handful of legitimate converter improvements still possible. Here's the full list, ranked.

### 4.1 High-impact converter bugs

#### Bug A — `ષ + matra` half-form preference (example-1)

**RESOLVED.** Fixed by changing standalone `ષ` from `Ø` to `QF` in `unicodeToTeraMap`. This makes `ષ` always emit `QF` (half-ssa + aa-matra base glyph), which correctly handles reph syllables (`વર્ષમાં → JQF"DF\`) and standalone cases (`ઉષાબેન → pQFFA[G`). The half-form table entry `ષ → Q` still handles conjuncts like `ષ્ણ → Q6`.

#### Bug B — 3-consonant `ષ + ્ + ণ` after another half-form

Already partially fixed via `halfForms[ષ] = 'Q'`. Continues to work for `ષ્ણ → Q6`. No outstanding bug here.

#### Bug C — Half-forms not yet verified

**PARTIALLY RESOLVED.** Added ગ → `u`, મ → `d`, and શ → `` ` `` half-forms. Remaining consonants NOT in `halfForms`:
- ક (`'ક્ત' → ST` — confirmed by example-1 output `p5ZMST` for `ઉપરોકત`, so this is correct as-is)
- ઘ, ઞ, જ, ઝ, ડ, ઢ, ણ, થ, દ, ય, ર, ળ, હ

These probably don't have half-forms — they just concat. But a couple may be wrong. To verify: search example outputs for any cluster where one of these consonants is the first member, and check whether the encoding uses lowercase / shifted glyph (suggesting a half-form) or just the full form.

### 4.2 Manual edits in the example files (NOT converter bugs)

Do **not** try to "fix" these — they're artifacts:

1. `]]` typo in example-1 / 2 for `સોગંદનામુ` (a stray extra `]`).
2. Decorative `oo` added at the start/end of some lines in example-3, example-4 even when the input doesn't have `::`.
3. Tab indentation, blank lines, manual paragraph-break formatting in expected files.
4. Single `'` → `cc` doubling in example-3 / example-4 (the example author preferred `cc` even for single quotes; my converter correctly maps `'` → `c`).
5. `D/ TF` (with space) in input vs `D/TF` (joined) in expected — the example author normalized.
6. Missing u-matras (`JWDF` got vs `JW]DF` exp) — input typos, the example author corrected.
7. `CQFF"A[G` expected vs old `CØF"A[G` — **RESOLVED** by changing standalone ષ from `Ø` to `QF`.
8. `voo` and `oov` decorative markers in expected — added by the author.

### 4.3 Two ASCII-encoding ambiguities

- The character `2` in TeraFont is `Z` (which is also the encoding for `ર` and `૨`). In the reverse direction this collides — currently `teraToUnicodeMap` maps `Z → ર` (consonant takes priority because conjuncts are inserted first). Reverse-direction work, if the user wants it, will need disambiguation by context.
- Periods of dots (`PPPPPP`) in expected files are placeholder dots in the source documents. Different counts in input vs expected reflect manual editing.

---

## 5. Plan for Next Agent

Do the work in this order. Stop at any point if the user is satisfied.

### Step 1 — Re-baseline (5 min)

Confirm the regression suite still passes:

```bash
cd /Users/ankit/Documents/Font-Conveter
node test_golden.js     # expect: 120/120 passed
node test_word_diff.js  # expect: example-1 ~7 diffs, example-2 ~7 diffs,
                        #         example-3 ~145 diffs, example-4 ~80 diffs
```

If `test_golden.js` doesn't pass 120/120, you've broken something — investigate before continuing.

### Step 2 — Verify ગ (ga) half-form

**RESOLVED.** ગ → `u` half-form added. Verified: `જગ્યા → HuIF`, `જગ્યામાં → HuIFDF\`. `ગ્ર` still uses subscript-r: `ગ્રાહક → U|FCS`.

### Step 3 — Investigate Bug A (ષ + aa-matra in reph syllables)

**RESOLVED.** Fixed by changing standalone `ષ` from `Ø` to `QF` in `unicodeToTeraMap`. All cases fixed: `વર્ષમાં → JQF"DF\`, `હર્ષાબેન → CQFF"A[G`, `ઉષાબેન → pQFFA[G`.

### Step 4 — Look for any remaining systematic bugs

Run word-diff and skim `example-3.txt` and `example-4.txt` outputs:

```bash
node test_word_diff.js example-3.txt | less
```

For each pair of (got token, expected token) that look like the same word but differ:

1. Decode both glyph-by-glyph using the tables in `converter.js`.
2. If the difference is a manual edit (whitespace, decorative, typo): skip.
3. If the difference looks like an encoding rule: trace it back to the input and figure out what rule the example author followed. Add a half-form / ligature / pattern accordingly. Add a golden test to lock it in.

### Step 5 — Optional: add per-file character-level alignment

If the user wants tighter coverage, a smarter test would line-by-line align got vs expected, attempt a one-edit-distance match per word, and report only the words that differ by **encoding** (not whitespace). The current `test_word_diff.js` is multiset-based and shows tokens out of context.

A diff library like `diff-sequences` would help, but adding npm dependencies is out of scope. A simple Levenshtein-based pairing in plain JS is enough.

### Step 6 — UI smoke test

Open `index.html` in a browser, paste a paragraph from `example-1.txt` input, and verify the output matches the expected (visually — the TeraFont font should render Gujarati shapes from the ASCII output). The `Convert` button is auto-conversion-on-input. If the visible Gujarati doesn't match, the font isn't loading or the conversion is broken.

---

## 6. Working with the Code

### Style guidelines

- **No new dependencies.** Plain JS, no npm packages.
- **Comments:** add only when the *why* isn't obvious. The `halfForms` and `conjunctPatterns` tables already have inline `// verified from examples` notes; keep that format when adding new entries.
- **Tests first.** Every time you add a new mapping, add a golden test for it in `test_golden.js`. The regression suite is the safety net.
- **Single source of truth.** When example files disagree with online converters or with API responses, **the example files win**. If you discover something in an example that contradicts an existing mapping, the existing mapping is probably wrong (or example-specific to a different occurrence).

### Common pitfalls

- The `halfForms` table is consulted **only** when `c1 + ્ + c2` is matched as a cluster. A standalone consonant always uses its `unicodeToTeraMap` value.
- The `conjunctPatterns` table is checked **first** (longest-first), so any entry there overrides the half-form / cluster logic for that exact key.
- Adding a multi-char `conjunctPattern` like `'જી': 'Ò'` will cause `જ` followed by `ી` to always emit `Ò` — this is intentional. If you want a context-dependent ligature, you'd need to add it to the main-loop logic, not the table.
- The `convertCluster` helper duplicates the main loop (used inside reph handler). When you change main-loop logic, **also update `convertCluster`** or behavior inside reph syllables will diverge.

### Quick experiments

To test a single conversion in Node:

```bash
node -e "global.document={addEventListener:()=>{}}; const {convertUnicodeToTera}=require('./converter.js'); console.log(convertUnicodeToTera('તમારું ગુજરાતી લખાણ'));"
```

---

## 7. Reference: User's Original Plan

The user's explicit instructions (still relevant):

> Use the example-*.txt files as the primary truth for glyph encoding, while preserving the original input line breaks and spacing. Reference sites are useful for missing cases, but when they disagree with your examples, your examples win.

> Don't require full-file exact match because the expected files include manual tabs, blank lines, and spacing edits. Add focused golden tests extracted from your examples for words, numbers, punctuation, half-forms, and common legal phrases.

> Acceptance target: 100% exact pass on focused fixtures and no unexplained encoding mismatches in normalized legacy-example validation.

The current state: 120/120 golden tests passing (14 new tests added in this pass). Word diff improvements:

| Example | Before (got-only/expected-only) | After |
|---------|------|-------|
| example-1 | 8/8 | 7/7 (manual edits only) |
| example-2 | 7/9 | 7/9 (manual edits only) |
| example-3 | 152/49 | 145/42 (7 fewer diffs) |
| example-4 | 73/84 | 73/84 (unchanged) |

### Mappings added in this pass

1. **Standalone ષ → `QF`** (was `Ø`). Fixes: `ઉષાબેન → pQFFA[G`, `વર્ષમાં → JQF"DF\`, `હર્ષાબેન → CQFF"A[G`, `શૈલેષભાઈ → X{,[QFEF.`
2. **ગ → `u` half-form** for `ગ્ય`. Verified: `જગ્યા → HuIF`. `ગ્ર` still uses subscript-r: `ગ્રાહક → U|FCS`.
3. **મ → `d` half-form** for `મ્યુ`. Verified: `મ્યુનિસીપલ → dI]lG;L5,`.
4. **શ → `` ` `` half-form** for `શ્વ`. Verified: `વિશ્વાસ → lJ`JF;`.
5. **New conjuncts**: `દ્ર → ã`, `શ્ચિ → lü`, `શ્ચ → ü`, `ત્ત → ¿`, `ક્કી → ÞL`.
6. **Dependent ૌ matra → `F{`** (was `Á`). Verified: `પૌત્રાદીક → 5F{+FNLS`.

### Remaining diffs

All remaining diffs still look like manual edits: decorative `oo`, quote doubling (`c` vs `cc`), added/missing punctuation, tabs/spaces, expected output correcting input typos (`પ્લેટ` → `પ્લોટ`), and legal-word spelling normalization (`માલિક...` missing short-i). Do not add broad global mappings for these unless another example confirms the same glyph rule independent of spelling normalization.

---

## 8. Files in the Repository

| File | Purpose |
|------|---------|
| `index.html` | Single-page UI |
| `style.css` | Glassmorphism dark theme + TeraFont @font-face |
| `converter.js` | All conversion logic + UI event wiring |
| `TRILOCHA.TTF` | TeraFont Trilochan font (also offered as a download in the UI) |
| `example-1.txt` … `example-4.txt` | Reference input/output pairs (canonical truth) |
| `test_golden.js` | 120 word-level regression tests (must always pass) |
| `test_examples.js` | Full-file diff (normalized; never expected to fully pass) |
| `test_word_diff.js` | Multiset token diff (best for finding real bugs in noise) |
| `CLAUDE.md` | Codebase orientation for AI agents |
| `HANDOFF.md` | This file |
