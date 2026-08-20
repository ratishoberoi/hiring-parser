# Hiring brief parser

This service turns a short, unstructured hiring brief into a validated hiring
criteria JSON object. One parser implementation is exposed as a Python
function, a command-line program, and a FastAPI endpoint.

## Requirements and installation

Python 3.11+ is required. Install dependencies in a fresh environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For live model calls, copy `.env.example` to `.env` (or export the variables)
and set `GEMINI_API_KEY`. The key is read from the environment and is never
stored in the repository. The parser reports provider token metadata where the
API supplies it; otherwise it reports a clearly labelled local approximation.

## Usage

Library:

```python
from parser import parse_brief
criteria = parse_brief("Senior Python engineer in Pune, 4-6 years...")
```

CLI:

```bash
python -m parser --input briefs/F03.txt --out out/F03.json
```

HTTP:

```bash
uvicorn app:app --reload
curl -X POST http://127.0.0.1:8000/parse \
  -H 'content-type: application/json' \
  -d '{"text":"backend engineer in Pune"}'
```

The response is `{"criteria": {...}}`. Empty input, model failures, malformed
JSON, and invalid schema values produce explicit errors rather than fabricated
criteria.

## Evaluation

Run the independent checks and regenerate all five committed outputs with:

```bash
python eval.py
```

The checks cover structure, mandatory versus preferred skills, experience,
location, work mode, budget, headcount, exclusions, the intentionally vague F03
brief, F04's correction and preference language, and token efficiency.

## Layout

```text
parser/       shared core, schema, LLM adapter, CLI/API, versioned prompt
briefs/       exactly the five supplied fixtures
out/          generated JSON results for those fixtures
eval.py       independent evaluation harness
NOTES.md      schema and engineering decisions
```
