"""
Gujarati Font Converter — Python port of converter.js

Converts between Unicode (Shruti / Noto) and TeraFont Trilochan encoding.

All mapping tables and conversion logic are verbatim copies of the verified
converter.js values. 123 golden tests lock correctness.
"""

# ============================================
# Character Mapping Tables
# ============================================

unicode_to_tera_map = {
    # Independent vowels
    '\u0a85': 'V', '\u0a86': 'VF',
    '\u0a87': '>', '\u0a88': '.',
    '\u0a89': 'p', '\u0a8a': '\u00e9',
    '\u0a8b': '\u00b0',
    '\u0a8f': 'V[', '\u0a90': 'V{',
    '\u0a93': 'VM',
    '\u0a94': 'V\u00c1',

    # Vowel signs / matras
    '\u0abe': 'F', '\u0abf': 'l', '\u0ac0': 'L',
    '\u0ac1': ']', '\u0ac2': '}',
    '\u0ac3': '\'',
    '\u0ac7': '[', '\u0ac8': '{',
    '\u0acb': 'M', '\u0acc': 'F{',
    '\u0a82': '\\', '\u0a83': 'o',
    '\u0a81': '\u00a5',

    # Consonants
    '\u0a95': 'S', '\u0a96': 'B', '\u0a97': 'U', '\u0a98': '3', '\u0a99': '\u00a2',
    '\u0a9a': 'R', '\u0a9b': 'K', '\u0a9c': 'H', '\u0a9d': 'h', '\u0a9e': '\u00bf',
    '\u0a9f': '8', '\u0aa0': '9', '\u0aa1': '0', '\u0aa2': '-', '\u0aa3': '6',
    '\u0aa4': 'T', '\u0aa5': 'Y', '\u0aa6': 'N', '\u0aa7': 'W', '\u0aa8': 'G',
    '\u0aaa': '5', '\u0aab': 'O', '\u0aac': 'A', '\u0aad': 'E', '\u0aae': 'D',
    '\u0aaf': 'I', '\u0ab0': 'Z', '\u0ab2': ',', '\u0ab3': '/', '\u0ab5': 'J',
    '\u0ab6': 'X', '\u0ab7': 'QF',
    '\u0ab8': ';', '\u0ab9': 'C',

    # Gujarati digits
    '\u0ae6': '_', '\u0ae7': '!', '\u0ae8': 'Z', '\u0ae9': '#', '\u0aea': '$',
    '\u0aeb': '5', '\u0aec': '&', '\u0aed': '*', '\u0aee': '(', '\u0aef': ')',

    # Devanagari digits
    '\u0966': '_', '\u0967': '!', '\u0968': 'Z', '\u0969': '#', '\u096a': '$',
    '\u096b': '5', '\u096c': '&', '\u096d': '*', '\u096e': '(', '\u096f': ')',

    # Punctuation / symbols
    '\u0964': 'P',
    '\u0965': 'PP',
    '\u0ad0': '\u203a',
}

half_forms = {
    '\u0aac': 'a',     # ba-half: બ્લોક → a,MS
    '\u0a96': 'b',     # kha-half: ખ્વ → bJ
    '\u0aad': 'e',     # bha-half: સભ્ય → ;eI
    '\u0a9a': 'r',     # cha-half: સ્વચ્છ → :JrK
    '\u0aa4': 't',     # ta-half: ત્ય → tI
    '\u0aa7': 'w',     # dha-half: શુધ્ધ → X]wW
    '\u0aa8': 'g',     # na-half: ન્ત → gT
    '\u0aaa': '%',     # pa-half: પ્લ → %,
    '\u0ab2': '<',     # la-half: લ્ક → <S
    '\u0ab5': 'j',     # va-half: વ્ય → jI
    '\u0ab7': 'Q',     # ssa-half: ષ્ણ → Q6
    '\u0ab8': ':',     # sa-half: સ્ત → :T
}

conjunct_patterns = {
    '\u0a95\u0acd\u0ab7': '1F',     # ક્ષ
    '\u0a9c\u0acd\u0a9e': '7',       # જ્ઞ
    '\u0aa4\u0acd\u0ab0': '+',       # ત્ર
    '\u0ab6\u0acd\u0ab0': 'z',       # શ્ર

    '\u0a95\u0acd\u0ab7\u0abf': 'l1F',  # ક્ષિ
    '\u0a9c\u0acd\u0a9e\u0abf': 'l7',   # જ્ઞિ
    '\u0aa4\u0acd\u0ab0\u0abf': 'l+',   # ત્રિ
    '\u0ab6\u0acd\u0ab0\u0abf': 'lz',   # શ્રિ

    '\u0ab6\u0acd\u0ab0\u0ac0': 'zL',   # શ્રી
    '\u0ab6\u0acd\u0ab0\u0acb': 'zM',   # શ્રો

    '\u0ab0\u0ac2': '~',         # રૂ
    '\u0a9c\u0ac0': '\u00d2',    # જી
}

matras = '\u0abe\u0abf\u0ac0\u0ac1\u0ac2\u0ac3\u0ac7\u0ac8\u0acb\u0acc\u0a82\u0a83'

REPH_MARKER = '\u0001'

CONSONANTS = '\u0a95\u0a96\u0a97\u0a98\u0a99\u0a9a\u0a9b\u0a9c\u0a9d\u0a9e\u0a9f\u0aa0\u0aa1\u0aa2\u0aa3\u0aa4\u0aa5\u0aa6\u0aa7\u0aa8\u0aaa\u0aab\u0aac\u0aad\u0aae\u0aaf\u0ab0\u0ab2\u0ab3\u0ab5\u0ab6\u0ab7\u0ab8\u0ab9'

retroflex = set(['\u0a9f', '\u0aa0', '\u0aa1', '\u0aa2', '\u0aa3'])

sorted_conjuncts = sorted(conjunct_patterns.keys(), key=len, reverse=True)

# Build reverse map (tera → unicode)
tera_to_unicode_map = {}
for unicode_char, tera in conjunct_patterns.items():
    if tera and len(tera) > 0 and tera not in tera_to_unicode_map:
        tera_to_unicode_map[tera] = unicode_char
for unicode_char, tera in unicode_to_tera_map.items():
    if tera and len(tera) > 0 and tera not in tera_to_unicode_map:
        tera_to_unicode_map[tera] = unicode_char


def tera_of(char):
    """Return TeraFont glyph for a Unicode char, or the char itself if unmapped."""
    return unicode_to_tera_map.get(char, char)


def is_consonant(char):
    """Check if a character is a Gujarati consonant."""
    return char in CONSONANTS


def encode_cluster(c1, c2):
    """Encode a 2-consonant cluster (c1 + virama + c2) → TeraFont string."""
    if c2 == '\u0ab0':  # ર (ra)
        sub = '=' if c1 in retroflex else '|'
        return tera_of(c1) + sub
    if c1 in half_forms:
        return half_forms[c1] + tera_of(c2)
    return tera_of(c1) + tera_of(c2)


def convert_cluster(syllable):
    """Convert a syllable (consonant cluster + matras) used by the reph handler.
    Mirrors the main loop but operates on a known syllable substring."""
    result = ''
    i = 0
    while i < len(syllable):
        # Try ligatures
        matched = False
        for pattern in sorted_conjuncts:
            if syllable[i:i + len(pattern)] == pattern:
                result += conjunct_patterns[pattern]
                i += len(pattern)
                matched = True
                break
        if matched:
            continue

        c0 = syllable[i]
        c1 = syllable[i + 1] if i + 1 < len(syllable) else ''
        c2 = syllable[i + 2] if i + 2 < len(syllable) else ''
        c3 = syllable[i + 3] if i + 3 < len(syllable) else ''

        # Consonant cluster: consonant + virama + consonant
        if is_consonant(c0) and c1 == '\u0acd' and is_consonant(c2):
            tera_cluster = encode_cluster(c0, c2)
            if c3 == '\u0abf':  # short-i after cluster
                result += 'l' + tera_cluster
                i += 4
            else:
                result += tera_cluster
                i += 3
            continue

        # Short-i: consonant + િ → l + tera(consonant)
        if is_consonant(c0) and c1 == '\u0abf':
            result += 'l' + tera_of(c0)
            i += 2
            continue

        # Orphan virama + ર → = (subscript-r continuation in 3-cons clusters)
        if c0 == '\u0acd' and c1 == '\u0ab0':
            result += '='
            i += 2
            continue
        if c0 == '\u0acd':
            i += 1
            continue
        if c0 == '\u0abf':
            result += 'l'
            i += 1
            continue

        result += tera_of(c0)
        i += 1
    return result


def preprocess_reph(text):
    """Replace `ર + ્ + consonant` (reph) with a private marker so the main
    loop can emit the reph mark `"` AFTER the syllable instead of before."""
    result = ''
    i = 0
    while i < len(text):
        if text[i] == '\u0ab0' and i + 1 < len(text) and text[i + 1] == '\u0acd':
            next_char = text[i + 2] if i + 2 < len(text) else ''
            if is_consonant(next_char) and next_char != '\u0ab0':
                result += REPH_MARKER
                i += 2  # skip ર + ્; the consonant is processed normally
                continue
        result += text[i]
        i += 1
    return result


def convert_unicode_to_tera(text):
    """Convert a Unicode Gujarati string to TeraFont Trilochan encoding."""
    if not text:
        return ''

    text = preprocess_reph(text)

    result = ''
    i = 0

    while i < len(text):
        # ── Reph marker: scan one full syllable, then append " ─────────
        if text[i] == REPH_MARKER:
            j = i + 1
            # Skip the consonant cluster
            if j < len(text) and is_consonant(text[j]):
                j += 1
            while j + 1 < len(text) and text[j] == '\u0acd' and is_consonant(text[j + 1]):
                j += 2
            # Skip any matras
            while j < len(text) and text[j] in matras:
                j += 1
            syllable = text[i + 1:j]
            result += convert_cluster(syllable) + '"'
            i = j
            continue

        # ── Try ligature patterns (longest first) ─────────────────────
        matched = False
        for pattern in sorted_conjuncts:
            if text[i:i + len(pattern)] == pattern:
                result += conjunct_patterns[pattern]
                i += len(pattern)
                matched = True
                break
        if matched:
            continue

        c0 = text[i]
        c1 = text[i + 1] if i + 1 < len(text) else ''
        c2 = text[i + 2] if i + 2 < len(text) else ''
        c3 = text[i + 3] if i + 3 < len(text) else ''

        # ── Consonant cluster: consonant + ્ + consonant ──────────────
        if is_consonant(c0) and c1 == '\u0acd' and is_consonant(c2):
            tera_cluster = encode_cluster(c0, c2)
            # Short-i after the cluster → 'l' goes BEFORE the cluster
            if c3 == '\u0abf':
                result += 'l' + tera_cluster
                i += 4
            else:
                result += tera_cluster
                i += 3
            continue

        # ── Short-i: consonant + િ → l + tera(consonant) ──────────────
        if is_consonant(c0) and c1 == '\u0abf':
            result += 'l' + tera_of(c0)
            i += 2
            continue

        # ── Orphan virama + ર: emit = (subscript-r continuation) ──────
        if c0 == '\u0acd' and c1 == '\u0ab0':
            result += '='
            i += 2
            continue

        # ── Standalone virama (no consonant follows) ──────────────────
        if c0 == '\u0acd':
            i += 1
            continue

        # ── Standalone short-i ────────────────────────────────────────
        if c0 == '\u0abf':
            result += 'l'
            i += 1
            continue

        # ── Single-character lookup ───────────────────────────────────
        result += tera_of(c0)
        i += 1

    return result


def convert_tera_to_unicode(text):
    """Convert a TeraFont Trilochan string to Unicode Gujarati."""
    if not text:
        return ''

    result = ''
    i = 0
    tera_keys = sorted(tera_to_unicode_map.keys(), key=len, reverse=True)

    while i < len(text):
        matched = False
        for key in tera_keys:
            if text[i:i + len(key)] == key:
                result += tera_to_unicode_map[key]
                i += len(key)
                matched = True
                break
        if not matched:
            result += text[i]
            i += 1

    return result
