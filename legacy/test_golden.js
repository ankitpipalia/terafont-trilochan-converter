/**
 * Focused golden tests: word-level Unicode → TeraFont conversions
 * extracted from the example-*.txt files.
 *
 * Run: node test_golden.js
 */

const { convertUnicodeToTera } = require('./converter.js');

const tests = [
    // ─── ASCII punctuation passes through unchanged ───────────────────
    { in: '::', out: '::', note: 'colons pass through' },
    { in: ':: સોગંદનામુ ::', out: ':: ;MU\\NGFD] ::', note: 'header line, : passes' },
    { in: '(૧)', out: '(!)', note: 'parens pass, digit converts' },
    { in: '(૨)', out: '(Z)' },
    { in: '૫૭/૫૮', out: '5*/5(', note: 'slash passes' },
    { in: '૪૮', out: '$(', note: 'two-digit number' },
    { in: '૧૦/૦૪/૨૦૨૬', out: '!_/_$/Z_Z&', note: 'date with slash passthrough' },
    { in: '–', out: '–', note: 'en-dash passes through' },
    { in: '"કા"', out: '"SF"', note: 'quotes pass, Gujarati converts' },

    // ─── Words from example-1 (verified by reading expected output) ───
    { in: 'સોગંદનામુ', out: ';MU\\NGFD]', note: 'sogandnamu' },
    { in: 'આથી', out: 'VFYL' },
    { in: 'અમો', out: 'VDM' },
    { in: 'નીચે', out: 'GLR[' },
    { in: 'સહી', out: ';CL' },
    { in: 'કરનાર', out: 'SZGFZ' },
    { in: 'ફિરોઝભાઈ', out: 'lOZMhEF.' },
    { in: 'હનીફભાઈ', out: 'CGLOEF.' },
    { in: 'રાઠોડ', out: 'ZF9M0' },
    { in: 'ધર્મે', out: 'WD["', note: 'reph: ધર્મ + e-matra' },
    { in: 'મુસ્લિમ', out: 'D]l:,D', note: 'half-sa with short-i' },
    { in: 'ધંધો', out: 'W\\WM' },
    { in: 'નોકરી', out: 'GMSZL' },
    { in: 'નવી', out: 'GJL' },
    { in: 'શેરી', out: 'X[ZL' },
    { in: 'રાજકોટ', out: 'ZFHSM8' },
    { in: 'મુસ્લિમ', out: 'D]l:,D' },
    { in: 'નિવૃત', out: 'lGJ\'T', note: 'short-i + vocalic-r matra' },
    { in: 'નેહરૂનગર', out: 'G[C~GUZ', note: 'contains રૂ → ~' },
    { in: 'રૈયા', out: 'Z{IF' },
    { in: 'સોગંદ', out: ';MU\\N' },
    { in: 'પ્રતિજ્ઞાપુર્વક', out: '5|lT7F5]J"S', note: 'pra + tya + jnya + reph' },
    { in: 'જાહેર', out: 'HFC[Z' },
    { in: 'કરી', out: 'SZL' },
    { in: 'છીએ', out: 'KLV[' },
    { in: 'ઉપરોકત', out: 'p5ZMST', note: 'upa-rok-ta (kt without virama)' },
    { in: 'દર્શાવેલ', out: 'NXF"J[,', note: 'reph: દર્શ' },
    { in: 'સરનામે', out: ';ZGFD[' },
    { in: 'મિલ્કત', out: 'lD<ST', note: 'short-i + half-la + ka + ta' },
    { in: 'સરનામુ', out: ';ZGFD]' },
    { in: 'મોરબી', out: 'DMZAL' },
    { in: 'રોડ', out: 'ZM0' },
    { in: 'આવેલ', out: 'VFJ[,' },
    { in: 'રેવન્યુ', out: 'Z[JgI]', note: 'half-na' },
    { in: 'સર્વે', out: ';J["', note: 'reph: સર્વ + e' },
    { in: 'પૈકીની', out: '5{SLGL' },
    { in: 'જમીન', out: 'HDLG' },
    { in: 'મધુવન', out: 'DW]JG' },
    { in: 'હાઉસીંગ', out: 'CFp;L\\U' },
    { in: 'સોસાયટી', out: ';M;FI8L' },
    { in: 'સુચીત', out: ';]RLT' },
    { in: 'પ્લોટ', out: '%,M8', note: 'half-pa + la + o-matra + retroflex-ta' },
    { in: 'જમીન', out: 'HDLG' },
    { in: 'ચો.વા.આ.', out: 'RM.JF.VF.', note: 'periods pass through' },

    // ─── Words from example-2 ─────────────────────────────────────────
    { in: 'પ્રકાશભાઈ', out: '5|SFXEF.', note: 'pra + kasha + bhai' },
    { in: 'શાન્તીલાલ', out: 'XFgTL,F,', note: 'half-na' },
    { in: 'મંડળી', out: 'D\\0/L' },
    { in: 'ગ્રાહક', out: 'U|FCS' },
    { in: 'સામાન્ય', out: ';FDFgI', note: 'half-na + ya' },
    { in: 'નિયમિત', out: 'lGIlDT' },
    { in: 'મારી', out: 'DFZL' },
    { in: 'ફરજીયાત', out: 'OZÒIFT', note: 'ji ligature' },
    { in: 'જમા', out: 'HDF' },
    { in: 'કરાવુ', out: 'SZFJ]' },

    // ─── Words from example-3 ─────────────────────────────────────────
    { in: 'જીવરાજભાઈ', out: 'ÒJZFHEF.', note: 'ji ligature' },
    { in: 'મુળજીભાઈ', out: 'D]/ÒEF.', note: 'ji ligature' },
    { in: 'સરધારા', out: ';ZWFZF' },
    { in: 'જાતે', out: 'HFT[' },
    { in: 'કુલમુખત્યાર', out: 'S],D]BtIFZ', note: 'half-ta + ya' },
    { in: 'દરજજે', out: 'NZHH[' },
    { in: 'હિન્દુ', out: 'lCgN]', note: 'short-i + half-na' },
    { in: 'નિવૃત', out: 'lGJ\'T' },
    { in: 'ક્રિષ્ના', out: 'lS|QGF', note: 'kri + ssa-half + na + aa' },
    { in: 'દિવાનપરા', out: 'lNJFG5ZF' },
    { in: 'સ્કુલ', out: ':S],', note: 'half-sa + ku + la' },
    { in: 'કર્મચારી', out: 'SD"RFZL', note: 'reph: કર્મ' },
    { in: 'ધિરાણ', out: 'lWZF6', note: 'short-i + dha + ra + na' },
    { in: 'ગ્રીન', out: 'U|LG' },
    { in: 'સહજાનંદનગર', out: ';CHFG\\NGUZ' },

    // ─── Reph tests ───────────────────────────────────────────────────
    { in: 'ધર્મ', out: 'WD"', note: 'plain reph + dharma' },
    { in: 'સર્વ', out: ';J"' },
    { in: 'કર્મ', out: 'SD"' },
    { in: 'દર્શ', out: 'NX"' },

    // ─── Numbers ──────────────────────────────────────────────────────
    { in: '૦૧૨૩૪૫૬૭૮૯', out: '_!Z#$5&*()' },
    { in: '૨૦૨૬', out: 'Z_Z&' },

    // ─── Special characters ───────────────────────────────────────────
    { in: 'રૂ', out: '~', note: 'special ru ligature' },
    { in: 'રૂા.', out: '~F.', note: 'rupees abbrev; period passes' },
    { in: 'ક્ષ', out: '1F', note: 'ksha ligature' },
    { in: 'જ્ઞ', out: '7', note: 'jnya ligature' },
    { in: 'ત્ર', out: '+', note: 'tra ligature' },

    // ─── Half-forms (each consonant in cluster with virama) ───────────
    { in: 'સ્વચ્છાએ', out: ':JrKFV[', note: 'cha-half = r (cha+virama+cha)' },
    { in: 'શુધ્ધ', out: 'X]wW', note: 'dha-half = w (dha+virama+dha)' },
    { in: 'સભ્ય', out: ';eI', note: 'bha-half = e' },
    { in: 'બ્લોક', out: 'a,MS', note: 'ba-half = a' },
    { in: 'ખ્વાજા', out: 'bJFHF', note: 'kha-half = b' },
    { in: 'મુસ્લિમ', out: 'D]l:,D', note: 'sa-half + short-i' },

    // ─── English words & symbols pass through ─────────────────────────
    { in: '"hello"', out: '"hello"', note: 'English in quotes passes through' },
    { in: '\'a\'', out: '\'a\'', note: 'single quotes pass through' },
    { in: 'PA NO. BMJPJ 3008 B', out: 'PA NO. BMJPJ 3008 B', note: 'English passes through' },
    { in: '{નામ}', out: '{GFD}', note: 'curly braces pass; Gujarati converts' },
    { in: '[૧૨૩]', out: '[!Z#]', note: 'square brackets pass; digits convert' },
    { in: 'ગુજરાત and English', out: 'U]HZFT and English', note: 'mixed: convert Gujarati only' },

    // ─── Subscript-r variants ─────────────────────────────────────────
    { in: 'ક્ર', out: 'S|', note: 'kra: regular subscript-r |' },
    { in: 'પ્ર', out: '5|', note: 'pra: regular subscript-r |' },
    { in: 'ગ્ર', out: 'U|', note: 'gra: regular subscript-r |' },
    { in: 'ટ્ર', out: '8=', note: 'tra (retroflex): subscript-r =' },
    { in: 'ડ્ર', out: '0=', note: 'd-ra (retroflex): subscript-r =' },

    // ─── 3-consonant clusters with subscript-r (orphan ્+ર → =) ──────
    { in: 'સ્ત્ર', out: ':T=', note: 'stra: half-sa + ta + = (3-cons)' },
    { in: 'ડીસ્ટ્રીકટ', out: '0L:8=LS8', note: 'district' },
    { in: 'રજીસ્ટ્રેશન', out: 'ZÒ:8=[XG', note: 'registration with ji-ligature + 3-cluster' },

    // ─── New mappings from 2026-05-09 pass ───────────────────────────
    { in: 'જગ્યા', out: 'HuIF', note: 'ga-half: ગ્ય → uI' },
    { in: 'જગ્યામાં', out: 'HuIFDF\\', note: 'ga-half with aa + anusvara' },
    { in: 'ગ્રાહક', out: 'U|FCS', note: 'ગ્ + ર still uses subscript-r, not ga-half' },
    { in: 'ઉષાબેન', out: 'pQFFA[G', note: 'standalone ષ uses QF base glyph + aa matra' },
    { in: 'વર્ષમાં', out: 'JQF"DF\\', note: 'reph + standalone ષ uses QF base glyph' },
    { in: 'હર્ષાબેન', out: 'CQFF"A[G', note: 'reph + ષા uses QF + aa + reph mark' },
    { in: 'શૈલેષભાઈ', out: 'X{,[QFEF.', note: 'standalone ષ before ભ uses QF base glyph' },
    { in: 'દ્રવ્યો', out: 'ãjIM', note: 'special દ્ર conjunct' },
    { in: 'વિશ્વાસ', out: 'lJ`JF;', note: 'sha-half: શ્વ → `J' },
    { in: 'પશ્ચિમે', out: '5lüD[', note: 'special શ્ચિ conjunct' },
    { in: 'ઉત્તરે', out: 'p¿Z[', note: 'special ત્ત conjunct' },
    { in: 'મ્યુનિસીપલ', out: 'dI]lG;L5,', note: 'ma-half in મ્યુ' },
    { in: 'નક્કી', out: 'GÞL', note: 'special ક્કી conjunct' },
    { in: 'પૌત્રાદીક', out: '5F{+FNLS', note: 'dependent ૌ uses F{ in examples' },
];

let pass = 0, fail = 0;
const failures = [];

for (const t of tests) {
    const got = convertUnicodeToTera(t.in);
    if (got === t.out) {
        pass++;
    } else {
        fail++;
        failures.push({ ...t, got });
    }
}

console.log(`\n${pass}/${pass + fail} passed`);
if (failures.length > 0) {
    console.log('\nFailures:');
    for (const f of failures) {
        const note = f.note ? `  (${f.note})` : '';
        console.log(`  in:  ${JSON.stringify(f.in)}${note}`);
        console.log(`  exp: ${JSON.stringify(f.out)}`);
        console.log(`  got: ${JSON.stringify(f.got)}`);
        console.log();
    }
}

process.exit(fail > 0 ? 1 : 0);
