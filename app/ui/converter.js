/**
 * Gujarati Font Converter
 * Converts between Unicode (Shruti / Noto) and TeraFont Trilochan encoding.
 *
 * Encoding rules for TeraFont Trilochan (verified against example-*.txt):
 * 1. Short-i matra (િ) is placed BEFORE the consonant glyph in output.
 * 2. Reph (ર્) is emitted as " AFTER the full syllable (incl. matras).
 * 3. Subscript-r (consonant + ્ + ર) → tera(consonant) + |.
 * 4. Some consonants have HALF-FORMS used when followed by virama+consonant
 *    (e.g., ન→g, સ→:, લ→<, પ→%, ખ→b, ત→t, વ→j, ગ→u, ષ→Q).
 * 5. Without a known half-form the virama is simply dropped: ક્ત → ST.
 * 6. A handful of clusters have their own ligature glyphs:
 *    ક્ષ→1F, જ્ઞ→7, ત્ર→+, શ્ર→z.
 * 7. ASCII punctuation maps to TeraFont-keyboard glyphs:
 *    `:`→o, `(`→s, `)`→f, `/`→q, `-`/`–`/`—`→v, `"`→cc.
 */

// ============================================
// Character Mapping Tables
// ============================================

const unicodeToTeraMap = {
    // Independent vowels
    'અ': 'V', 'આ': 'VF',
    'ઇ': '>', 'ઈ': '.',
    'ઉ': 'p', 'ઊ': 'é',
    'ઋ': '°',
    'એ': 'V[', 'ઐ': 'V{',
    'ઓ': 'VM',  // independent O = અ + ો (verified from examples: ઓનરશીપ → VMGZXL5)
    'ઔ': 'VÁ', // independent Au = અ + ૌ

    // Vowel signs / matras
    'ા': 'F', 'િ': 'l', 'ી': 'L',
    'ુ': ']', 'ૂ': '}',
    'ૃ': '\'',
    'ે': '[', 'ૈ': '{',
    'ો': 'M', 'ૌ': 'F{', // dependent ૌ = F{ (verified: પૌત્રાદીક → 5F{+FNLS)
    'ં': '\\', 'ઃ': 'o',
    'ઁ': '¥',  // chandrabindu

    // Consonants
    'ક': 'S', 'ખ': 'B', 'ગ': 'U', 'ઘ': '3', 'ઙ': '¢',
    'ચ': 'R', 'છ': 'K', 'જ': 'H', 'ઝ': 'h', 'ઞ': '¿',
    'ટ': '8', 'ઠ': '9', 'ડ': '0', 'ઢ': '-', 'ણ': '6',
    'ત': 'T', 'થ': 'Y', 'દ': 'N', 'ધ': 'W', 'ન': 'G',
    'પ': '5', 'ફ': 'O', 'બ': 'A', 'ભ': 'E', 'મ': 'D',
    'ય': 'I', 'ર': 'Z', 'લ': ',', 'ળ': '/', 'વ': 'J',
    'શ': 'X', 'ષ': 'QF', // standalone ssa = QF base glyph + aa-matra (verified: ઉષાબેન → pQFFA[G)
    'સ': ';', 'હ': 'C',

    // Gujarati digits
    '૦': '_', '૧': '!', '૨': 'Z', '૩': '#', '૪': '$',
    '૫': '5', '૬': '&', '૭': '*', '૮': '(', '૯': ')',

    // Devanagari digits (sometimes mixed in with Gujarati input)
    '०': '_', '१': '!', '२': 'Z', '३': '#', '४': '$',
    '५': '5', '६': '&', '७': '*', '८': '(', '९': ')',

    // Gujarati/Devanagari punctuation (not ASCII)
    '।': 'P',     // Gujarati/Devanagari danda
    '॥': 'PP',    // double danda
    'ૐ': '›',     // OM symbol

    // NOTE: ASCII punctuation (:, (, ), /, -, ", ', etc.) and English
    // letters are intentionally NOT mapped — they pass through unchanged
    // so mixed-script documents (Gujarati + English/symbols) work cleanly.
};

/**
  * Half-forms: a consonant followed by virama+consonant uses these glyphs.
  * Verified from example-*.txt:
  *   ખ→b (ખ્વ→bJ),  ગ→u (ગ્ય→uI),  ત→t (ત્ય→tI),  ન→g (ન્ત→gT),
  *   મ→d (મ્યુ→dI]), પ→% (પ્લ→%,),  લ→< (લ્ક→<S),  વ→j (વ્ય→jI),
  *   ષ→Q (ષ્ણ→Q6),  સ→: (સ્ત→:T),  શ→` (શ્વ→`J).
  * Consonants not in this table simply have the virama dropped:
  *   ક્ત → ST, ભ્ય → EI, etc.
  */
  const halfForms = {
      'બ': 'a',     // ba-half: બ્લોક → a,MS
      'ખ': 'b',     // kha-half: ખ્વ → bJ
      'ગ': 'u',     // ga-half: ગ્ય → uI (verified: જગ્યા → HuIF)
      'ભ': 'e',     // bha-half: સભ્ય → ;eI
      'મ': 'd',     // ma-half: મ્યુ → dI] (verified: મ્યુનિસીપલ → dI]lG;L5,)
      'ચ': 'r',     // cha-half: સ્વચ્છ → :JrK
      'ત': 't',     // ta-half: ત્ય → tI
      'ધ': 'w',     // dha-half: શુધ્ધ → X]wW
      'ન': 'g',     // na-half: ન્ત → gT
      'પ': '%',     // pa-half: પ્લ → %,
      'લ': '<',     // la-half: લ્ક → <S
      'વ': 'j',     // va-half: વ્ય → jI
      'શ': '`',     // sha-half: શ્વ → `J (verified: વિશ્વાસ → lJ`JF;)
      'ષ': 'Q',     // ssa-half: ષ્ણ → Q6
      'સ': ':',     // sa-half: સ્ત → :T
  };

/**
 * Special multi-character ligature patterns. Matched longest-first.
 * Includes:
 *  - Special-shape ligatures (ક્ષ, જ્ઞ, ત્ર, શ્ર)
 *  - Their short-i variants (where 'l' must precede the cluster glyphs)
 *  - શ્ર + matra ligatures (the matra glyph is fused with the cluster)
 *  - One-off character-level combos (રૂ → ~).
 */
const conjunctPatterns = {
    // Special ligatures
    'ક્ષ': '1F',
    'જ્ઞ': '7',
    'ત્ર': '+',
    'શ્ર': 'z',

    // Short-i variants of ligatures (l + ligature)
    'ક્ષિ': 'l1F',
    'જ્ઞિ': 'l7',
    'ત્રિ': 'l+',
    'શ્રિ': 'lz',

    // શ્ર + matras (cluster + matra fused)
    'શ્રી': 'zL',
    'શ્રો': 'zM',

    // Other verified conjuncts
    'શ્ચિ': 'lü', // પશ્ચિમે → 5lüD[
    'શ્ચ': 'ü',
    'દ્ર': 'ã',   // દ્રવ્યો → ãjIM
    'ત્ત': '¿',   // ઉત્તરે → p¿Z[
    'ક્કી': 'ÞL', // નક્કી → GÞL

    // Consonant + matra ligatures (special fused glyphs in TeraFont)
    'રૂ': '~',         // ru → single glyph
    'જી': 'Ò',         // ja + long-i → single glyph (verified: જીવરાજ → ÒJZFH)
};

// Matras (used by reph syllable scanner)
const matras = 'ાિીુૂૃેૈોૌંઃ';

// Private-use marker inserted by preprocessReph
const REPH_MARKER = '';

// ============================================
// Conversion Functions: Unicode → TeraFont
// ============================================

const sortedConjuncts = Object.keys(conjunctPatterns).sort((a, b) => b.length - a.length);

function teraOf(char) {
    return unicodeToTeraMap[char] !== undefined ? unicodeToTeraMap[char] : char;
}

function isConsonant(char) {
    return 'કખગઘઙચછજઝઞટઠડઢણતથદધનપફબભમયરલળવશષસહ'.includes(char);
}

/**
 * Convert a Unicode Gujarati string to TeraFont Trilochan encoding.
 */
function convertUnicodeToTera(text) {
    if (!text) return '';

    // Pre-process reph: replace ર+્ before a consonant with REPH_MARKER.
    text = preprocessReph(text);

    let result = '';
    let i = 0;

    while (i < text.length) {
        // ── Reph marker: scan one full syllable, then append " ─────────
        if (text[i] === REPH_MARKER) {
            let j = i + 1;
            // Skip the consonant cluster (consonant, then any virama-joined consonants)
            if (j < text.length && isConsonant(text[j])) j++;
            while (j + 1 < text.length && text[j] === '્' && isConsonant(text[j + 1])) j += 2;
            // Skip any matras
            while (j < text.length && matras.includes(text[j])) j++;
            const syllable = text.substring(i + 1, j);
            result += convertCluster(syllable) + '"';
            i = j;
            continue;
        }

        // ── Try ligature patterns (longest first) ─────────────────────
        let matched = false;
        for (const pattern of sortedConjuncts) {
            if (text.substring(i, i + pattern.length) === pattern) {
                result += conjunctPatterns[pattern];
                i += pattern.length;
                matched = true;
                break;
            }
        }
        if (matched) continue;

        const c0 = text[i];
        const c1 = text[i + 1] || '';
        const c2 = text[i + 2] || '';
        const c3 = text[i + 3] || '';

        // ── Consonant cluster: consonant + ્ + consonant ──────────────
        if (isConsonant(c0) && c1 === '્' && isConsonant(c2)) {
            const teraCluster = encodeCluster(c0, c2);
            // Short-i after the cluster → 'l' goes BEFORE the cluster
            if (c3 === 'િ') {
                result += 'l' + teraCluster;
                i += 4;
            } else {
                result += teraCluster;
                i += 3;
            }
            continue;
        }

        // ── Short-i: consonant + િ → l + tera(consonant) ──────────────
        if (isConsonant(c0) && c1 === 'િ') {
            result += 'l' + teraOf(c0);
            i += 2;
            continue;
        }

        // ── Orphan virama + ર: emit `=` (subscript-r continuation in
        //    3-consonant clusters, e.g. સ્ત્ર → :8= where ્ર is left
        //    over after :8 was emitted for સ્ત).
        if (c0 === '્' && c1 === 'ર') {
            result += '=';
            i += 2;
            continue;
        }

        // ── Standalone virama (no consonant follows) ──────────────────
        if (c0 === '્') {
            i++;
            continue;
        }

        // ── Standalone short-i ────────────────────────────────────────
        if (c0 === 'િ') {
            result += 'l';
            i++;
            continue;
        }

        // ── Single-character lookup ───────────────────────────────────
        result += teraOf(c0);
        i++;
    }

    return result;
}

/**
 * Retroflex consonants — when followed by virama+ra the subscript-r is
 * encoded with `=` (a different glyph) instead of the regular `|`.
 *   Example: ટ્ર → 8=  (vs. ક્ર → S|)
 */
const retroflex = new Set(['ટ', 'ઠ', 'ડ', 'ઢ', 'ણ']);

/**
 * Encode a 2-consonant cluster (c1 + ્ + c2) → TeraFont string.
 * Rules:
 *  - c2 === 'ર' (subscript-r):  tera(c1) + '=' if c1 retroflex, else '|'
 *  - c1 has half-form: halfForm(c1) + tera(c2)
 *  - otherwise: just tera(c1) + tera(c2) (virama dropped)
 */
function encodeCluster(c1, c2) {
    if (c2 === 'ર') {
        const sub = retroflex.has(c1) ? '=' : '|';
        return teraOf(c1) + sub;
    }
    if (halfForms[c1]) {
        return halfForms[c1] + teraOf(c2);
    }
    return teraOf(c1) + teraOf(c2);
}

/**
 * Convert a syllable (consonant cluster + matras) used by the reph handler.
 * Mirrors the main loop but operates on a known syllable substring.
 */
function convertCluster(syllable) {
    let result = '';
    let i = 0;
    while (i < syllable.length) {
        // Try ligatures
        let matched = false;
        for (const pattern of sortedConjuncts) {
            if (syllable.substring(i, i + pattern.length) === pattern) {
                result += conjunctPatterns[pattern];
                i += pattern.length;
                matched = true;
                break;
            }
        }
        if (matched) continue;

        const c0 = syllable[i];
        const c1 = syllable[i + 1] || '';
        const c2 = syllable[i + 2] || '';
        const c3 = syllable[i + 3] || '';

        if (isConsonant(c0) && c1 === '્' && isConsonant(c2)) {
            const teraCluster = encodeCluster(c0, c2);
            if (c3 === 'િ') {
                result += 'l' + teraCluster;
                i += 4;
            } else {
                result += teraCluster;
                i += 3;
            }
            continue;
        }

        if (isConsonant(c0) && c1 === 'િ') {
            result += 'l' + teraOf(c0);
            i += 2;
            continue;
        }

        if (c0 === '્' && c1 === 'ર') { result += '='; i += 2; continue; }
        if (c0 === '્') { i++; continue; }
        if (c0 === 'િ') { result += 'l'; i++; continue; }

        result += teraOf(c0);
        i++;
    }
    return result;
}

/**
 * Replace `ર + ્ + consonant` (reph) with a private marker so the main loop
 * can emit the reph mark `"` AFTER the syllable instead of before.
 */
function preprocessReph(text) {
    let result = '';
    let i = 0;
    while (i < text.length) {
        if (text[i] === 'ર' && text[i + 1] === '્' && i + 2 < text.length) {
            const next = text[i + 2];
            if (isConsonant(next) && next !== 'ર') {
                result += REPH_MARKER;
                i += 2; // skip ર + ્; the consonant is processed normally
                continue;
            }
        }
        result += text[i];
        i++;
    }
    return result;
}

// ============================================
// Reverse Mapping: TeraFont → Unicode
// ============================================

const teraToUnicodeMap = {};
// Insert ligatures first so they take priority over single-char mappings.
for (const [unicode, tera] of Object.entries(conjunctPatterns)) {
    if (tera && tera.length > 0 && !teraToUnicodeMap[tera]) {
        teraToUnicodeMap[tera] = unicode;
    }
}
for (const [unicode, tera] of Object.entries(unicodeToTeraMap)) {
    if (tera && tera.length > 0 && !teraToUnicodeMap[tera]) {
        teraToUnicodeMap[tera] = unicode;
    }
}

function convertTeraToUnicode(text) {
    if (!text) return '';
    let result = '';
    let i = 0;
    const teraKeys = Object.keys(teraToUnicodeMap).sort((a, b) => b.length - a.length);
    while (i < text.length) {
        let matched = false;
        for (const key of teraKeys) {
            if (text.substring(i, i + key.length) === key) {
                result += teraToUnicodeMap[key];
                i += key.length;
                matched = true;
                break;
            }
        }
        if (!matched) {
            result += text[i];
            i++;
        }
    }
    return result;
}

// ============================================
// CommonJS export (so tests can require this file in Node)
// ============================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        convertUnicodeToTera,
        convertTeraToUnicode,
        unicodeToTeraMap,
        conjunctPatterns,
        halfForms,
        teraToUnicodeMap,
    };
}

// ============================================
// UI Event Handlers (browser only)
// ============================================

if (typeof document !== 'undefined' && document.addEventListener) {
    document.addEventListener('DOMContentLoaded', initApp);
}

function initApp() {
    // ───── DOM refs ──────────────────────────────────────────────────
    const $ = (id) => document.getElementById(id);
    const inputText = $('inputText'),  outputText = $('outputText');
    const inputPanel = $('inputPanel');
    const convertBtn = $('convertBtn'), clearInputBtn = $('clearInput');
    const copyOutputBtn = $('copyOutput'), downloadOutputBtn = $('downloadOutputBtn');
    const swapBtn = $('swapBtn'), pasteBtn = $('pasteBtn');
    const modeU2T = $('modeUnicodeToTera'), modeT2U = $('modeTeraToUnicode'), modeAuto = $('modeAuto');
    const inputLabel = $('inputLabel'), outputLabel = $('outputLabel');
    const themeToggle = $('themeToggle'), shortcutsBtn = $('shortcutsBtn');
    const shortcutsModal = $('shortcutsModal');
    const uploadBtn = $('uploadBtn'), fileInput = $('fileInput');
    const loadSampleBtn = $('loadSampleBtn'), printBtn = $('printBtn');
    const downloadTxtBtn = $('downloadTxtBtn');
    const findReplaceBtn = $('findReplaceBtn'), findReplaceBar = $('findReplaceBar');
    const findInput = $('findInput'), replaceInput = $('replaceInput');
    const findNextBtn = $('findNextBtn'), replaceOneBtn = $('replaceOneBtn');
    const replaceAllBtn = $('replaceAllBtn'), closeFindBtn = $('closeFindBtn');
    const toast = $('toast');
    const inputChars = $('inputChars'), inputWords = $('inputWords'), inputLines = $('inputLines');
    const outputChars = $('outputChars'), outputWords = $('outputWords'), outputReadtime = $('outputReadtime');

    let currentMode = localStorage.getItem('conv_mode') || 'unicodeToTera';
    let lastFindIndex = 0;

    // ───── Theme ─────────────────────────────────────────────────────
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeToggle.addEventListener('click', () => {
        const cur = document.documentElement.getAttribute('data-theme');
        const next = cur === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        showToast(`${next === 'dark' ? '🌙' : '☀️'} ${next.charAt(0).toUpperCase() + next.slice(1)} theme`, 'info');
    });

    // ───── Stats ─────────────────────────────────────────────────────
    function countWords(s) {
        if (!s.trim()) return 0;
        return s.trim().split(/\s+/).length;
    }

    function readTime(s) {
        const words = countWords(s);
        const mins = Math.max(1, Math.round(words / 200)); // 200 wpm
        return `${mins}m`;
    }

    function updateStats() {
        const ival = inputText.value, oval = outputText.value;
        inputChars.textContent = ival.length.toLocaleString();
        inputWords.textContent = countWords(ival).toLocaleString();
        inputLines.textContent = (ival ? ival.split('\n').length : 0).toLocaleString();
        outputChars.textContent = oval.length.toLocaleString();
        outputWords.textContent = countWords(oval).toLocaleString();
        outputReadtime.textContent = oval ? readTime(oval) : '0m';
    }

    // ───── Toast ─────────────────────────────────────────────────────
    let toastTimer;
    function showToast(message, type = 'success') {
        clearTimeout(toastTimer);
        toast.querySelector('.toast-message').textContent = message;
        toast.className = 'toast show ' + type;
        toastTimer = setTimeout(() => { toast.className = 'toast'; }, 2500);
    }

    // ───── Auto-detect mode ──────────────────────────────────────────
    function detectMode(text) {
        if (!text) return 'unicodeToTera';
        // Gujarati Unicode block: U+0A80 to U+0AFF
        const hasGujaratiUnicode = /[઀-૿]/.test(text);
        if (hasGujaratiUnicode) return 'unicodeToTera';
        // If text has typical TeraFont-only chars (Ø, é, Á, etc.) or just ASCII
        return 'teraToUnicode';
    }

    // ───── Conversion ────────────────────────────────────────────────
    function doConvert() {
        const input = inputText.value;
        if (!input) { outputText.value = ''; updateStats(); return; }
        const mode = currentMode === 'auto' ? detectMode(input) : currentMode;
        const output = mode === 'unicodeToTera'
            ? convertUnicodeToTera(input)
            : convertTeraToUnicode(input);
        outputText.value = output;
        updateStats();
    }
    // Expose for ocr.js preview conversion
    window.doConvert = doConvert;

    function convertWithFeedback() {
        if (!inputText.value.trim()) {
            showToast('Type or paste some text first', 'error');
            return;
        }
        doConvert();
        showToast('✓ Converted', 'success');
    }

    // ───── Mode switching ────────────────────────────────────────────
    function setMode(mode, opts = {}) {
        currentMode = mode;
        localStorage.setItem('conv_mode', mode);
        [modeU2T, modeT2U, modeAuto].forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-selected', 'false');
        });

        const effective = mode === 'auto' ? detectMode(inputText.value) : mode;

        if (mode === 'unicodeToTera') {
            modeU2T.classList.add('active'); modeU2T.setAttribute('aria-selected', 'true');
        } else if (mode === 'teraToUnicode') {
            modeT2U.classList.add('active'); modeT2U.setAttribute('aria-selected', 'true');
        } else {
            modeAuto.classList.add('active'); modeAuto.setAttribute('aria-selected', 'true');
        }

        if (effective === 'unicodeToTera') {
            inputLabel.textContent = 'Unicode Gujarati Text';
            outputLabel.textContent = 'TeraFont Trilochan Output';
            inputText.style.fontFamily = "var(--font-gujarati)";
            outputText.style.fontFamily = "var(--font-tera)";
        } else {
            inputLabel.textContent = 'TeraFont Trilochan Text';
            outputLabel.textContent = 'Unicode Gujarati Output';
            inputText.style.fontFamily = "var(--font-tera)";
            outputText.style.fontFamily = "var(--font-gujarati)";
        }

        if (!opts.skipConvert) doConvert();
    }

    modeU2T.addEventListener('click', () => setMode('unicodeToTera'));
    modeT2U.addEventListener('click', () => setMode('teraToUnicode'));
    modeAuto.addEventListener('click', () => setMode('auto'));

    // ───── Live convert as user types ────────────────────────────────
    let convertTimer;
    inputText.addEventListener('input', () => {
        if (currentMode === 'auto') setMode('auto', { skipConvert: true });
        clearTimeout(convertTimer);
        convertTimer = setTimeout(doConvert, 30); // tiny debounce for large texts
    });

    convertBtn.addEventListener('click', convertWithFeedback);

    // ───── Clear / Paste ─────────────────────────────────────────────
    clearInputBtn.addEventListener('click', () => {
        inputText.value = ''; outputText.value = '';
        updateStats(); inputText.focus();
    });

    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                inputText.value = text;
                doConvert();
                showToast('Pasted from clipboard', 'success');
            }
        } catch {
            showToast('Clipboard access denied', 'error');
        }
    });

    // ───── Copy output ───────────────────────────────────────────────
    async function copyOutput() {
        if (!outputText.value) { showToast('Nothing to copy', 'error'); return; }
        try {
            await navigator.clipboard.writeText(outputText.value);
            showToast('✓ Copied to clipboard', 'success');
        } catch {
            outputText.select(); document.execCommand('copy');
            showToast('✓ Copied to clipboard', 'success');
        }
    }
    copyOutputBtn.addEventListener('click', copyOutput);

    // ───── Swap ──────────────────────────────────────────────────────
    swapBtn.addEventListener('click', () => {
        const t = inputText.value;
        inputText.value = outputText.value;
        outputText.value = t;
        // Flip mode so the conversion direction makes sense after swap
        if (currentMode === 'unicodeToTera') setMode('teraToUnicode', { skipConvert: true });
        else if (currentMode === 'teraToUnicode') setMode('unicodeToTera', { skipConvert: true });
        doConvert();
        showToast('Swapped input ↔ output', 'info');
    });

    // ───── File upload (button + drag-drop) ──────────────────────────
    function isDocx(name) { return /\.docx$/i.test(name); }

    async function loadFile(file) {
        if (!file) return;
        if (file.size > 25 * 1024 * 1024) {
            showToast('File too large (max 25 MB)', 'error');
            return;
        }

        // DOCX → go through Python API (needs python-docx)
        if (isDocx(file.name)) {
            if (!(typeof window.pywebview !== 'undefined' && window.pywebview.api)) {
                showToast('.docx upload requires the desktop app', 'error');
                return;
            }
            // Pywebview can't pass file content from <input>, so trigger the
            // native picker via the API instead. (Drop-to-DOCX requires Python access.)
            try {
                const path = await window.pywebview.api.pick_document();
                if (!path) return;
                const res = await window.pywebview.api.read_docx(path);
                if (res.error) { showToast(`Open failed: ${res.error}`, 'error'); return; }
                inputText.value = res.text;
                if (currentMode === 'auto') setMode('auto', { skipConvert: true });
                doConvert();
                showToast(`Loaded ${file.name}`, 'success');
            } catch (err) {
                showToast(`Open failed: ${err}`, 'error');
            }
            return;
        }

        // Plain text fast path
        const reader = new FileReader();
        reader.onload = (e) => {
            inputText.value = e.target.result;
            if (currentMode === 'auto') setMode('auto', { skipConvert: true });
            doConvert();
            showToast(`Loaded ${file.name}`, 'success');
        };
        reader.onerror = () => showToast('Failed to read file', 'error');
        reader.readAsText(file);
    }

    uploadBtn.addEventListener('click', async () => {
        // In desktop mode prefer the native picker so DOCX works
        if (typeof window.pywebview !== 'undefined' && window.pywebview.api) {
            try {
                const path = await window.pywebview.api.pick_document();
                if (!path) return;
                if (isDocx(path)) {
                    const res = await window.pywebview.api.read_docx(path);
                    if (res.error) { showToast(`Open failed: ${res.error}`, 'error'); return; }
                    inputText.value = res.text;
                } else {
                    const res = await window.pywebview.api.read_text_file(path);
                    if (res.error) { showToast(`Open failed: ${res.error}`, 'error'); return; }
                    inputText.value = res.text;
                }
                if (currentMode === 'auto') setMode('auto', { skipConvert: true });
                doConvert();
                showToast(`Loaded ${path.split(/[\\/]/).pop()}`, 'success');
            } catch (err) {
                showToast(`Open failed: ${err}`, 'error');
            }
        } else {
            fileInput.click();  // browser fallback
        }
    });
    fileInput.addEventListener('change', (e) => loadFile(e.target.files[0]));

    // Drag-drop on input panel
    ['dragenter', 'dragover'].forEach(ev =>
        inputPanel.addEventListener(ev, (e) => { e.preventDefault(); inputPanel.classList.add('drag-over'); }));
    ['dragleave', 'drop'].forEach(ev =>
        inputPanel.addEventListener(ev, (e) => { e.preventDefault(); inputPanel.classList.remove('drag-over'); }));
    inputPanel.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        if (file) loadFile(file);
    });

    // ───── Download ──────────────────────────────────────────────────
    function downloadText(content, filename) {
        if (!content) { showToast('Nothing to download', 'error'); return; }
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast(`Downloaded ${filename}`, 'success');
    }

    function downloadOutput() {
        const ts = new Date().toISOString().slice(0, 10);
        const ext = currentMode === 'teraToUnicode' ? 'unicode' : 'tera';
        downloadText(outputText.value, `gujarati-${ext}-${ts}.txt`);
    }

    downloadTxtBtn.addEventListener('click', downloadOutput);
    downloadOutputBtn.addEventListener('click', downloadOutput);

    // ───── Export as DOCX / PDF ──────────────────────────────────────
    const exportDocxBtn = $('exportDocxBtn');
    const exportPdfBtn = $('exportPdfBtn');

    function hasApi() { return typeof window.pywebview !== 'undefined' && window.pywebview.api; }

    async function exportAs(format) {
        if (!outputText.value.trim()) { showToast('Nothing to export', 'error'); return; }
        if (!hasApi()) {
            showToast(`${format.toUpperCase()} export requires the desktop app`, 'error');
            return;
        }
        const ts = new Date().toISOString().slice(0, 10);
        const filename = `gujarati-${ts}.${format}`;
        const fn = format === 'docx'
            ? window.pywebview.api.export_docx
            : window.pywebview.api.export_pdf;
        try {
            const res = await fn(outputText.value, filename);
            if (res && res.error) {
                showToast(`Export failed: ${res.error}`, 'error');
            } else if (res && res.path) {
                showToast(`Saved ${res.path.split(/[\\/]/).pop()}`, 'success');
            }
        } catch (err) {
            showToast(`Export failed: ${err}`, 'error');
        }
    }

    if (exportDocxBtn) exportDocxBtn.addEventListener('click', () => exportAs('docx'));
    if (exportPdfBtn)  exportPdfBtn.addEventListener('click',  () => exportAs('pdf'));

    // Hide export buttons that aren't available in this build
    setTimeout(async () => {
        if (!hasApi()) return; // browser mode — leave both buttons visible (they'll error gracefully)
        try {
            const caps = await window.pywebview.api.doc_capabilities();
            if (exportDocxBtn && !caps.docx) exportDocxBtn.style.display = 'none';
            if (exportPdfBtn  && !caps.pdf)  exportPdfBtn.style.display = 'none';
        } catch {}
    }, 300);

    // ───── Print ─────────────────────────────────────────────────────
    printBtn.addEventListener('click', () => window.print());

    // ───── Sample text ───────────────────────────────────────────────
    const SAMPLE = `નમસ્તે! આ એક નમૂનો છે ગુજરાતી ફોન્ટ કન્વર્ટરનો.

મારું નામ રાજેશ છે. હું રાજકોટમાં રહું છું. આજે તારીખ ૨૦/૧૧/૨૦૨૬ છે.

ગુજરાત રાજ્યના રજીસ્ટ્રેશન ઓફિસમાં મારી નોકરી છે. ધર્મે હિન્દુ, વ્યવસાય નોકરી.

This is mixed English text — it will pass through unchanged.

કૃષ્ણ, રામ, શ્રી, જય ગુજરાત! 🇮🇳`;

    loadSampleBtn.addEventListener('click', () => {
        inputText.value = SAMPLE;
        if (currentMode === 'auto') setMode('auto', { skipConvert: true });
        doConvert();
        showToast('Sample loaded', 'info');
    });

    // ───── Find & Replace ────────────────────────────────────────────
    function toggleFindBar(show) {
        findReplaceBar.hidden = !show;
        if (show) { findInput.focus(); findInput.select(); }
    }
    findReplaceBtn.addEventListener('click', () => toggleFindBar(findReplaceBar.hidden));
    closeFindBtn.addEventListener('click', () => toggleFindBar(false));

    function findNext() {
        const needle = findInput.value;
        if (!needle) return;
        const text = inputText.value;
        let idx = text.indexOf(needle, lastFindIndex);
        if (idx === -1 && lastFindIndex > 0) {
            idx = text.indexOf(needle); // wrap
        }
        if (idx === -1) {
            showToast('Not found', 'error');
            lastFindIndex = 0;
            return;
        }
        inputText.focus();
        inputText.setSelectionRange(idx, idx + needle.length);
        lastFindIndex = idx + needle.length;
        // Scroll into view
        const lineHeight = parseInt(getComputedStyle(inputText).lineHeight) || 24;
        const linesBefore = text.substring(0, idx).split('\n').length;
        inputText.scrollTop = Math.max(0, (linesBefore - 5) * lineHeight);
    }
    findNextBtn.addEventListener('click', findNext);
    findInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); findNext(); }
    });

    replaceOneBtn.addEventListener('click', () => {
        const needle = findInput.value, repl = replaceInput.value;
        if (!needle) return;
        const sel = inputText.value.substring(inputText.selectionStart, inputText.selectionEnd);
        if (sel === needle) {
            const s = inputText.selectionStart;
            inputText.setRangeText(repl, s, s + needle.length, 'end');
            doConvert();
        }
        findNext();
    });

    replaceAllBtn.addEventListener('click', () => {
        const needle = findInput.value, repl = replaceInput.value;
        if (!needle) return;
        const before = inputText.value;
        const after = before.split(needle).join(repl);
        const count = (before.length - after.length) / Math.max(1, (needle.length - repl.length));
        const actualCount = before.split(needle).length - 1;
        inputText.value = after;
        doConvert();
        showToast(`Replaced ${actualCount} occurrence${actualCount === 1 ? '' : 's'}`, 'success');
    });

    // ───── Shortcuts modal ───────────────────────────────────────────
    function openModal() { shortcutsModal.hidden = false; }
    function closeModal() { shortcutsModal.hidden = true; }
    shortcutsBtn.addEventListener('click', openModal);
    shortcutsModal.querySelector('.modal-overlay').addEventListener('click', closeModal);
    shortcutsModal.querySelector('.close-modal').addEventListener('click', closeModal);

    // ───── Keyboard shortcuts ────────────────────────────────────────
    document.addEventListener('keydown', (e) => {
        const isCtrl = e.ctrlKey || e.metaKey;
        const isInTextarea = e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT';

        if (isCtrl && e.key === 'Enter') { e.preventDefault(); convertWithFeedback(); return; }
        if (isCtrl && e.key.toLowerCase() === 'o') { e.preventDefault(); fileInput.click(); return; }
        if (isCtrl && e.key.toLowerCase() === 's') { e.preventDefault(); downloadOutput(); return; }
        if (isCtrl && e.key.toLowerCase() === 'p') { e.preventDefault(); window.print(); return; }
        if (isCtrl && e.key.toLowerCase() === 'f') { e.preventDefault(); toggleFindBar(true); return; }
        if (isCtrl && e.shiftKey && e.key.toLowerCase() === 'c') { e.preventDefault(); copyOutput(); return; }
        if (isCtrl && e.key.toLowerCase() === 'k') { e.preventDefault(); swapBtn.click(); return; }
        if (isCtrl && e.key === '/') { e.preventDefault(); themeToggle.click(); return; }

        if (e.key === 'Escape') {
            if (!shortcutsModal.hidden) { closeModal(); return; }
            if (!findReplaceBar.hidden) { toggleFindBar(false); return; }
            if (isInTextarea && inputText.value) {
                inputText.value = ''; outputText.value = ''; updateStats();
            }
        }

        if (e.key === '?' && !isInTextarea) { openModal(); }
    });

    // ───── Initial setup ─────────────────────────────────────────────
    setMode(currentMode, { skipConvert: true });
    updateStats();

    // Show a welcoming hint if textarea is empty (only once per session)
    if (!inputText.value && !sessionStorage.getItem('welcomed')) {
        sessionStorage.setItem('welcomed', '1');
        setTimeout(() => showToast('Tip: drag a .txt file or press ? for shortcuts', 'info'), 600);
    }
}
