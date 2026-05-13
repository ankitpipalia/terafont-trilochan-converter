# Examples

Drop your own Gujarati Unicode + TeraFont Trilochan reference pairs here for verification.

## Format

Each example is a single `.txt` file with two sections:

```
input:
<Gujarati Unicode text>

output:
<expected TeraFont Trilochan text>
```

## Privacy

⚠️ **These files are git-ignored by default.** Real legal documents contain personal data (names, addresses, ID numbers). The pattern `examples/example-*.txt` is in `.gitignore` — they stay on your machine only.

If you want to commit a public sample for the test suite, name it `examples/public-*.txt` (this pattern is not gitignored).

## Why these aren't in the repo

The original development used four real affidavits / lease agreements to reverse-engineer the TeraFont mapping. Those files contained personal information and were never committed. The mappings they uncovered live in [`app/converter.py`](../app/converter.py) and are locked in by the 120 golden tests in [`tests/test_converter.py`](../tests/test_converter.py).

If you have your own sample documents and want to validate the converter against them, drop them here and run:

```bash
# (you'll need to write a small adapter — see legacy/test_examples.js for inspiration)
```
