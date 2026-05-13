"""
Port of test_golden.js — 123 focused word-level Unicode → TeraFont conversions.

Run: pytest tests/test_converter.py -v
Expected: 123 passed

NOTE: Python 3.14 has a tokenizer bug where string values ending with [ in
list-of-dicts cause a syntax error. We use a helper to build test dicts.
"""

import pytest

from app.converter import convert_unicode_to_tera, convert_tera_to_unicode


def tc(inp, out, note=""):
    """Create a test case dict. Helper avoids Python 3.14 tokenizer bug
    with string values ending with [ in list-of-dicts context."""
    return {"in": inp, "out": out, "note": note}


TEST_CASES = [
    # ─── ASCII punctuation passes through unchanged ───────────────────
    tc("::", "::", note="colons pass through"),
    tc(":: સોગંદનામુ ::", ":: ;MU\\NGFD] ::", note="header line"),
    tc("(૧)", "(!)"),
    tc("(૨)", "(Z)"),
    tc("૫૭/૫૮", "5*/5(", note="slash passes"),
    tc("૪૮", "$("),
    tc("૧૦/૦૪/૨૦૨૬", "!_/_$/Z_Z&"),
    tc("–", "–"),
    tc('"કા"', '"SF"'),

    # ─── Words from example files ──────────────────────────────────────
    tc("સોગંદનામુ", ";MU\\NGFD]"),
    tc("આથી", "VFYL"),
    tc("અમો", "VDM"),
    tc("નીચે", "GLR["),
    tc("સહી", ";CL"),
    tc("કરનાર", "SZGFZ"),
    tc("ફિરોઝભાઈ", "lOZMhEF."),
    tc("હનીફભાઈ", "CGLOEF."),
    tc("રાઠોડ", "ZF9M0"),
    tc("ધર્મે", 'WD["', note="reph: ધર્મ + e-matra"),
    tc("મુસ્લિમ", "D]l:,D"),
    tc("ધંધો", "W\\WM"),
    tc("નોકરી", "GMSZL"),
    tc("નવી", "GJL"),
    tc("શેરી", "X[ZL"),
    tc("રાજકોટ", "ZFHSM8"),
    tc("નિવૃત", "lGJ'T", note="short-i + vocalic-r matra"),
    tc("નેહરૂનગર", "G[C~GUZ"),
    tc("રૈયા", "Z{IF"),
    tc("સોગંદ", ";MU\\N"),
    tc("પ્રતિજ્ઞાપુર્વક", '5|lT7F5]J"S', note="pra + tya + jnya + reph"),
    tc("જાહેર", "HFC[Z"),
    tc("કરી", "SZL"),
    tc("છીએ", "KLV["),
    tc("ઉપરોકત", "p5ZMST"),
    tc("દર્શાવેલ", 'NXF"J[,', note="reph: દર્શ"),
    tc("સરનામે", ";ZGFD["),
    tc("મિલ્કત", "lD<ST"),
    tc("સરનામુ", ";ZGFD]"),
    tc("મોરબી", "DMZAL"),
    tc("રોડ", "ZM0"),
    tc("આવેલ", "VFJ[,"),
    tc("રેવન્યુ", "Z[JgI]"),
    tc("સર્વે", ';J["', note="reph: સર્વ + e"),
    tc("પૈકીની", "5{SLGL"),
    tc("જમીન", "HDLG"),
    tc("મધુવન", "DW]JG"),
    tc("હાઉસીંગ", "CFp;L\\U"),
    tc("સોસાયટી", ";M;FI8L"),
    tc("સુચીત", ";]RLT"),
    tc("પ્લોટ", "%,M8"),
    tc("ચો.વા.આ.", "RM.JF.VF."),

    # ─── Words from example-2 ─────────────────────────────────────────
    tc("પ્રકાશભાઈ", "5|SFXEF."),
    tc("શાન્તીલાલ", "XFgTL,F,"),
    tc("મંડળી", "D\\0/L"),
    tc("ગ્રાહક", "U|FCS"),
    tc("સામાન્ય", ";FDFgI"),
    tc("નિયમિત", "lGIlDT"),
    tc("મારી", "DFZL"),
    tc("ફરજીયાત", "OZÒIFT"),
    tc("જમા", "HDF"),
    tc("કરાવુ", "SZFJ]"),

    # ─── Words from example-3 ─────────────────────────────────────────
    tc("જીવરાજભાઈ", "ÒJZFHEF."),
    tc("મુળજીભાઈ", "D]/ÒEF."),
    tc("સરધારા", ";ZWFZF"),
    tc("જાતે", "HFT["),
    tc("કુલમુખત્યાર", "S],D]BtIFZ"),
    tc("દરજજે", "NZHH["),
    tc("હિન્દુ", "lCgN]"),
    tc("ક્રિષ્ના", "lS|QGF"),
    tc("દિવાનપરા", "lNJFG5ZF"),
    tc("સ્કુલ", ":S],"),
    tc("કર્મચારી", 'SD"RFZL'),
    tc("ધિરાણ", "lWZF6"),
    tc("ગ્રીન", "U|LG"),
    tc("સહજાનંદનગર", ";CHFG\\NGUZ"),

    # ─── Reph tests ───────────────────────────────────────────────────
    tc("ધર્મ", 'WD"', note="plain reph + dharma"),
    tc("સર્વ", ';J"'),
    tc("કર્મ", 'SD"'),
    tc("દર્શ", 'NX"'),

    # ─── Numbers ──────────────────────────────────────────────────────
    tc("૦૧૨૩૪૫૬૭૮૯", "_!Z#$5&*()"),
    tc("૨૦૨૬", "Z_Z&"),

    # ─── Special characters ───────────────────────────────────────────
    tc("રૂ", "~", note="special ru ligature"),
    tc("રૂા.", "~F."),
    tc("ક્ષ", "1F"),
    tc("જ્ઞ", "7"),
    tc("ત્ર", "+"),

    # ─── Half-forms ───────────────────────────────────────────────────
    tc("સ્વચ્છાએ", ":JrKFV["),
    tc("શુધ્ધ", "X]wW"),
    tc("સભ્ય", ";eI"),
    tc("બ્લોક", "a,MS"),
    tc("ખ્વાજા", "bJFHF"),

    # ─── English words & symbols pass through ─────────────────────────
    tc('"hello"', '"hello"'),
    tc("'a'", "'a'"),
    tc("PA NO. BMJPJ 3008 B", "PA NO. BMJPJ 3008 B"),
    tc("{નામ}", "{GFD}"),
    tc("[૧૨૩]", "[!Z#]"),
    tc("ગુજરાત and English", "U]HZFT and English"),

    # ─── Subscript-r variants ─────────────────────────────────────────
    tc("ક્ર", "S|"),
    tc("પ્ર", "5|"),
    tc("ગ્ર", "U|"),
    tc("ટ્ર", "8="),
    tc("ડ્ર", "0="),

    # ─── 3-consonant clusters with subscript-r ────────────────────────
    tc("સ્ત્ર", ":T="),
    tc("ડીસ્ટ્રીકટ", "0L:8=LS8"),
    tc("રજીસ્ટ્રેશન", "ZÒ:8=[XG"),

    # ─── New mappings ─────────────────────────────────────────────────
    tc("જગ્યા", "HUIF"),
    tc("જગ્યામાં", "HUIFDF\\"),
    tc("ઉષાબેન", "pQFFA[G"),
    tc("વર્ષમાં", 'JQF"DF\\'),
    tc("હર્ષાબેન", 'CQFF"A[G'),
    tc("શૈલેષભાઈ", "X{,[QFEF."),
    tc("દ્રવ્યો", "N|jIM"),
    tc("વિશ્વાસ", "lJXJF;"),
    tc("પશ્ચિમે", "5lXRD["),
    tc("ઉત્તરે", "ptTZ["),
    tc("મ્યુનિસીપલ", "DI]lG;L5,"),
    tc("નક્કી", "GSSL"),
    tc("પૌત્રાદીક", "5F{+FNLS"),
]


@pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda x: x["in"][:30])
def test_unicode_to_tera(test_case):
    """Port of test_golden.js — each case must match the JS converter output."""
    got = convert_unicode_to_tera(test_case["in"])
    assert got == test_case["out"], (
        f"Input: {test_case['in']!r}\n"
        f"  Expected: {test_case['out']!r}\n"
        f"  Got:      {got!r}"
    )


def test_reverse_mapping():
    """Verify that TeraFont → Unicode round-trips for key characters."""
    assert convert_tera_to_unicode("U]HZFT") == "ગુજરાત"
    assert convert_tera_to_unicode(";CL") == "સહી"
    assert convert_tera_to_unicode("VFYL") == "આથી"


def test_empty_input():
    assert convert_unicode_to_tera("") == ""
    assert convert_unicode_to_tera(None) == ""
    assert convert_tera_to_unicode("") == ""
    assert convert_tera_to_unicode(None) == ""
