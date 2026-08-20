# Engineering notes

## Schema

The result keeps role family/title, controlled seniority, an explicit
experience range, separate mandatory and preferred skill lists, location and
its requirement strength, controlled work mode, domain, compensation, numeric
headcount, and explicit exclusions. Unknown scalar values are `null` and
unknown collections are empty; unsupported facts are never filled by inference.
The schema deliberately does not include candidate ranking, confidence prose,
or extracted reasoning.

## Structured output

The compact versioned prompt asks the model for JSON only, with a schema-guided
response format where the provider supports it. A small validation/normalizing
step rejects malformed JSON and invalid enum values. Free-form explanations,
chain-of-thought, and large few-shot examples were rejected because they add
latency and tokens without improving this extraction task.

## Hardest brief

F04 is hardest: its later correction supersedes “five years”, Bangalore is a
preference rather than a requirement, and Go is preferred while Java is merely
acceptable. The text still leaves title, domain, compensation, headcount, and
work mode unknown.

## Fragility and next steps

Informal multilingual phrasing, unusual compensation units, and provider
responses that omit usage metadata remain failure points. With five more hours
I would add provider-contract tests using recorded responses, more adversarial
correction examples, and metrics for validation/retry rates.

## Time and token efficiency

Actual implementation time: approximately 3 hours (including evaluation and
documentation). Token counts use provider input/output metadata when present;
the offline fallback uses a documented rough character-based estimate, not an
exact billing count. `eval.py` prints the average total tokens per brief when
usage is available. The compact prompt and JSON-only output are designed for
high-throughput use.
