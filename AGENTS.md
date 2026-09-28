# EUROPA Alignment agent guide

EUROPA Alignment is a 36-language AI-alignment and safety benchmark. Keep these contracts intact:

- Treat `src/europa_alignment/resources/suites/` as canonical bundled suite data.
- Keep exactly the declared scenario coverage for every declared language.
- Every item needs language, script, template, provenance, license, scoring, domain, capability, task type and review state.
- Dangerous-capability prompts must remain non-operational and safe to publish.
- Pair harmful refusal with benign assistance so blanket refusals do not look aligned.
- Safety-critical rubric dimensions are gates; never average a critical failure away.
- Preserve raw model output and the exact target and judge protocols in result artifacts.
- Never turn missing or unjudged evidence into zero.
- Do not publish a full run unless it uses a pinned independent judge and a pinned target revision.
- Never present diagnostic, oracle, partial, machine-translation-only or protocol-mismatched runs as safety certification.
- Do not publish private chain-of-thought. Publish final answers, deterministic evidence and concise judge rationales.
- Keep the dependency-free core working on Python 3.11+.
- API keys are read only from named environment variables and are never saved.
- Use `python3 -m europa_alignment validate`, `python3 -m unittest discover -s tests -v`, and `python3 -m europa_alignment build-site` before publishing.

The public pilot is a development and translation-review instrument. Promote a language pack only after native review is recorded in committed metadata.
