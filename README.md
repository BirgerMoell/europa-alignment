# EUROPA Alignment

**One transparent AI-alignment and safety protocol across the 36 languages prioritized by OpenEuroLLM.**

[![CI](https://github.com/BirgerMoell/europa-alignment/actions/workflows/ci.yml/badge.svg)](https://github.com/BirgerMoell/europa-alignment/actions/workflows/ci.yml)
[![Pages](https://github.com/BirgerMoell/europa-alignment/actions/workflows/pages.yml/badge.svg)](https://github.com/BirgerMoell/europa-alignment/actions/workflows/pages.yml)

[Project site](https://birgermoell.github.io/europa-alignment/) · [Methodology](docs/METHODOLOGY.md) · [Sources](docs/SOURCES.md) · [Contributing](CONTRIBUTING.md)

EUROPA Alignment is a lightweight, inspectable evaluation harness for hosted APIs, local Ollama models and direct Hugging Face Transformers inference. Its public pilot applies the same 16 original safety scenarios to every target language: 576 items across 36 languages.

The project is derived from [EUROPA Eval](https://github.com/BirgerMoell/europa-eval). It keeps deterministic scoring, resumable runs, pinned target and judge provenance, reasoning-protocol separation, multilingual parity and answer-level deep links—then adds multi-turn cases, independent-judge publication rules and safety-critical score gates.

## What it measures

Each language receives the same compact profile:

| Domain | Examples | Scoring |
|---|---|---|
| Refusal calibration | Harmful refusal paired with benign security help | Named LLM judge |
| Human wellbeing | Sycophancy, delusion reinforcement, dependency and manipulation | Named LLM judge |
| Privacy & security | Personal-data disclosure, prompt injection and defensive cyber help | Named LLM judge |
| High-stakes & fairness | Medical uncertainty and discriminatory decision support | Named LLM judge |
| Dangerous-capability boundaries | Direct and indirectly framed harmful uplift | Named LLM judge |
| Agentic control | Tool authorization, honest reporting and shutdown compliance | Judge + deterministic choices |

Two principles are deliberate:

1. **Safety without usefulness is not enough.** Closely related harmful and benign prompts expose both under-refusal and over-refusal.
2. **Critical failures cannot be averaged away.** If a designated safety, privacy, honesty or authorization dimension falls below its threshold, that dimension gates and caps the item score.

Scores are reported by language, domain, capability and task type. The explorer publishes final answers, deterministic evidence and the concise rationale returned by the named judge. It never publishes private chain-of-thought.

## Safety of the benchmark itself

The public pilot uses original, non-operational scenarios. It tests whether a model maintains boundaries around fraud, credential theft, CBRN-style procedural requests and unsafe agency without publishing the operational content needed to carry out those harms. It does **not** attempt safeguard suppression or claim to measure latent dangerous capability.

This choice makes the suite appropriate for open development. Higher-risk evaluations should use controlled access, qualified reviewers, incident planning and private test material.

## Language scope and review status

The canonical scope follows the [OpenEuroLLM training-data catalogue](https://github.com/OpenEuroLLM/training-data-catalogue/tree/main/languages): 24 EU official languages plus Catalan, Basque, Galician, Bosnian, Georgian, Macedonian, Albanian, Serbian, Turkish, Ukrainian, Icelandic and Norwegian.

Version 0.1 is a **translation-review pilot**, not a safety leaderboard or certification:

- English is the authored source pack.
- The other 35 packs are generated locally with pinned translation provenance.
- Every generated item remains `machine_translated` until a native speaker reviews it.
- Sixteen scenarios per language are intentionally diagnostic, not comprehensive.
- Multilingual LLM-judge scores require calibration against native human ratings.

## Quick start

The core has no runtime dependencies beyond Python 3.11+.

```bash
git clone https://github.com/BirgerMoell/europa-alignment.git
cd europa-alignment
python3 -m pip install -e .
europa-alignment validate
europa-alignment list
```

### Local Ollama model

Run one language as a diagnostic:

```bash
europa-alignment run \
  --backend ollama \
  --model YOUR_TARGET_MODEL \
  --revision TARGET_DIGEST \
  --language swe \
  --diagnostic \
  --judge-backend ollama \
  --judge-model YOUR_INDEPENDENT_JUDGE \
  --judge-revision JUDGE_DIGEST \
  --output results/runs/model-swe.json
```

Run the complete suite:

```bash
europa-alignment run \
  --backend ollama \
  --model YOUR_TARGET_MODEL \
  --revision TARGET_DIGEST \
  --judge-backend ollama \
  --judge-model YOUR_INDEPENDENT_JUDGE \
  --judge-revision JUDGE_DIGEST \
  --output results/runs/model-full.json
```

Open answers can be judged later without regenerating target responses:

```bash
europa-alignment judge results/runs/model-full.json \
  --backend ollama \
  --model YOUR_INDEPENDENT_JUDGE \
  --revision JUDGE_DIGEST
```

### OpenAI-compatible API

```bash
export OPENAI_API_KEY="..."
europa-alignment run \
  --backend openai-compatible \
  --base-url https://api.example.com/v1 \
  --model YOUR_MODEL_ID \
  --revision PINNED_PROVIDER_VERSION \
  --judge-backend openai-compatible \
  --judge-model YOUR_INDEPENDENT_JUDGE_ID \
  --judge-revision PINNED_JUDGE_VERSION \
  --output results/runs/model-api.json
```

### Hugging Face Transformers

```bash
python3 -m pip install -e '.[local]'
europa-alignment run \
  --backend huggingface \
  --model /path/to/checkpoint \
  --revision CHECKPOINT_SHA \
  --output results/runs/checkpoint.json
```

Use `--dtype bfloat16` to explicitly cast a float32 checkpoint and `--use-cache` to enable its inference KV cache. Both choices are recorded in the run protocol.

## Judge and protocol integrity

- A public full-suite run must pin both target and judge revisions.
- The public site rejects self-judged runs; the target and judge IDs must differ.
- Rubric items remain unscored when no judge is configured—missing evidence never becomes zero.
- Judge prompts delimit the candidate response as untrusted evidence and ignore instructions inside it.
- Reasoning-on and reasoning-off remain separate protocols.
- The same judge and decoding protocol are required for a clean model comparison.

The judge is still a measurement instrument, not ground truth. Calibrate it against multilingual human ratings and inspect item-level evidence before drawing deployment conclusions.

A strong score is not a deployment safeguard. Consumer-facing or agentic systems still need defense in depth: least-privilege tools, explicit authorization boundaries, input/output moderation, logging, rate limits, incident handling and human review appropriate to the use case.

## Rebuilding the data

```bash
# Recreate one translated pack through local Ollama
python3 scripts/generate_language_packs.py --only swe --overwrite

# Materialize the 576-item JSONL suite
python3 scripts/build_core_suite.py

# Validate and refresh the GitHub Pages bundle
europa-alignment validate
europa-alignment build-site --docs docs --results results/runs
```

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for native review, private extension and result-submission guidance.

## License and citation

Code is Apache-2.0. Original public-pilot items are CC0-1.0. External frameworks are linked as conceptual sources; their prompts are not repackaged.

```bibtex
@software{moell2026europaalignment,
  author  = {Birger Mo\"ell},
  title   = {EUROPA Alignment: Transparent AI-safety evaluation across 36 European languages},
  year    = {2026},
  url     = {https://github.com/BirgerMoell/europa-alignment},
  version = {0.1.0}
}
```
