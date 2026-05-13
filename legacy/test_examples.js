/**
 * Compare converter output against example-*.txt files.
 *
 * Default: NORMALIZED comparison — collapse whitespace runs and ignore
 * leading/trailing whitespace per line. The expected files contain manual
 * tab/blank-line edits that aren't part of the encoding.
 *
 * Pass --strict to require exact match.
 *
 * Usage: node test_examples.js [--strict] [files...]
 */

const fs = require('fs');
const path = require('path');

global.document = { addEventListener: () => {} };
const { convertUnicodeToTera } = require('./converter.js');

const STRICT = process.argv.includes('--strict');
const files = process.argv.slice(2)
    .filter(a => !a.startsWith('--'))
    .map(f => path.isAbsolute(f) ? f : path.join(__dirname, f));

const targets = files.length > 0 ? files :
    ['example-1.txt', 'example-2.txt', 'example-3.txt', 'example-4.txt']
        .map(f => path.join(__dirname, f));

function parseExample(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const inputMatch = content.match(/^input:\n([\s\S]*?)\n^output:/m);
    const outputMatch = content.match(/^output:\n([\s\S]*)$/m);
    if (!inputMatch || !outputMatch) {
        throw new Error(`Cannot parse ${filePath} — missing input:/output: markers`);
    }
    return {
        input: inputMatch[1],
        expected: outputMatch[1],
    };
}

// Normalize: collapse whitespace, ignore tabs/empty-line padding.
function normalize(s) {
    return s.replace(/\s+/g, ' ').trim();
}

// Find first character mismatch and return context.
function firstMismatch(got, expected, contextSize = 25) {
    const len = Math.max(got.length, expected.length);
    for (let i = 0; i < len; i++) {
        if (got[i] !== expected[i]) {
            const start = Math.max(0, i - contextSize);
            const end = i + contextSize;
            return {
                pos: i,
                got: got.substring(start, end),
                expected: expected.substring(start, end),
                gotChar: got[i] ? `"${got[i]}" U+${got.codePointAt(i).toString(16).toUpperCase().padStart(4,'0')}` : 'EOF',
                expChar: expected[i] ? `"${expected[i]}" U+${expected.codePointAt(i).toString(16).toUpperCase().padStart(4,'0')}` : 'EOF',
            };
        }
    }
    return null;
}

let totalFiles = 0, passFiles = 0;

for (const fp of targets) {
    totalFiles++;
    let data;
    try { data = parseExample(fp); } catch (e) { console.error(`SKIP ${path.basename(fp)}: ${e.message}`); continue; }

    const got = convertUnicodeToTera(data.input);

    if (STRICT) {
        if (got === data.expected) {
            passFiles++;
            console.log(`✓ ${path.basename(fp)} — STRICT match`);
        } else {
            const m = firstMismatch(got, data.expected);
            console.log(`✗ ${path.basename(fp)} — strict mismatch at pos ${m.pos}`);
            console.log(`    GOT: ${JSON.stringify(m.got)}`);
            console.log(`    EXP: ${JSON.stringify(m.expected)}`);
            console.log(`    char: got ${m.gotChar} vs exp ${m.expChar}`);
        }
    } else {
        const gotN = normalize(got);
        const expN = normalize(data.expected);
        if (gotN === expN) {
            passFiles++;
            console.log(`✓ ${path.basename(fp)} — normalized match (got ${got.length} chars, exp ${data.expected.length})`);
        } else {
            const m = firstMismatch(gotN, expN);
            console.log(`✗ ${path.basename(fp)} — normalized mismatch at pos ${m.pos}`);
            console.log(`    GOT: ${JSON.stringify(m.got)}`);
            console.log(`    EXP: ${JSON.stringify(m.expected)}`);
            console.log(`    char: got ${m.gotChar} vs exp ${m.expChar}`);
        }
    }
}

console.log(`\n${passFiles}/${totalFiles} files match (${STRICT ? 'strict' : 'normalized'}).`);
process.exit(passFiles === totalFiles ? 0 : 1);
