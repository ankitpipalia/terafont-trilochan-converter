/**
 * Word-by-word comparison: tokenize the converter output and the expected
 * output, then list every word that differs.
 *
 * The example files contain manual whitespace/decorative edits (added `oo`
 * headers, tabs, blank lines, the occasional `]]` typo). Word-by-word
 * comparison sees past those and surfaces only real encoding differences.
 *
 * Usage: node test_word_diff.js [file...]
 */

const fs = require('fs');
const path = require('path');

global.document = { addEventListener: () => {} };
const { convertUnicodeToTera } = require('./converter.js');

function parseExample(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const inputMatch = content.match(/^input:\n([\s\S]*?)\n^output:/m);
    const outputMatch = content.match(/^output:\n([\s\S]*)$/m);
    if (!inputMatch || !outputMatch) throw new Error(`bad markers in ${filePath}`);
    return { input: inputMatch[1], expected: outputMatch[1] };
}

// Tokenize on whitespace.
function tokens(s) {
    return s.split(/\s+/).filter(Boolean);
}

// Multiset diff: returns tokens unique to A vs unique to B.
function multisetDiff(a, b) {
    const countsA = new Map();
    const countsB = new Map();
    for (const t of a) countsA.set(t, (countsA.get(t) || 0) + 1);
    for (const t of b) countsB.set(t, (countsB.get(t) || 0) + 1);
    const onlyA = [], onlyB = [];
    for (const [k, v] of countsA) {
        const w = countsB.get(k) || 0;
        if (v > w) onlyA.push({ tok: k, count: v - w });
    }
    for (const [k, v] of countsB) {
        const w = countsA.get(k) || 0;
        if (v > w) onlyB.push({ tok: k, count: v - w });
    }
    return { onlyA, onlyB };
}

const files = process.argv.slice(2).length > 0
    ? process.argv.slice(2).map(f => path.isAbsolute(f) ? f : path.join(__dirname, f))
    : ['example-1.txt', 'example-2.txt', 'example-3.txt', 'example-4.txt']
        .map(f => path.join(__dirname, f));

for (const fp of files) {
    let data;
    try { data = parseExample(fp); } catch (e) { console.error(`SKIP ${path.basename(fp)}`); continue; }
    const got = convertUnicodeToTera(data.input);
    const gotToks = tokens(got);
    const expToks = tokens(data.expected);
    const { onlyA: inGot, onlyB: inExp } = multisetDiff(gotToks, expToks);
    console.log(`\n── ${path.basename(fp)} — gotTokens=${gotToks.length} expTokens=${expToks.length}`);
    if (inGot.length === 0 && inExp.length === 0) {
        console.log('  ✓ all tokens match');
        continue;
    }
    console.log(`  ${inGot.length} tokens in OUR output that aren't in expected`);
    console.log(`  ${inExp.length} tokens in expected that aren't in OUR output`);
    const showCount = 40;
    console.log('  --- IN OUR OUTPUT (potential converter overshoot) ---');
    for (const t of inGot.slice(0, showCount)) console.log(`    ${t.count}× ${JSON.stringify(t.tok)}`);
    if (inGot.length > showCount) console.log(`    ... +${inGot.length - showCount} more`);
    console.log('  --- IN EXPECTED ONLY (potential converter miss) ---');
    for (const t of inExp.slice(0, showCount)) console.log(`    ${t.count}× ${JSON.stringify(t.tok)}`);
    if (inExp.length > showCount) console.log(`    ... +${inExp.length - showCount} more`);
}
