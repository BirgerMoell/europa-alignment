# Sources and provenance

## Canonical language scope

EUROPA Alignment uses the 36 prioritized macro-languages listed by the [OpenEuroLLM training-data catalogue](https://github.com/OpenEuroLLM/training-data-catalogue/tree/main/languages) (Apache-2.0). The local registry preserves ISO 639-3 codes, BCP 47 tags, autonyms, primary scripts and catalogue variants.

## Original public-pilot items

All 16 English scenario templates were authored for EUROPA Alignment and released under CC0-1.0. The project does not copy benchmark prompts from the references below. They inform the risk taxonomy, contrastive design and reporting principles.

The source pack is `src/europa_alignment/resources/pack-source-en.json`. Generated packs live under `src/europa_alignment/resources/language-packs/` and retain translation model, immutable revision, decoding protocol, review state and any later corrections.

## Design references

- [Inkling Model Card — Safety and limitations](https://thinkingmachines.ai/model-card/inkling/) — motivates separating everyday interaction, refusal calibration, dangerous-capability boundaries, loss-of-control concerns, defense in depth and deployment limitations.
- [NIST AI 600-1: Generative AI Profile](https://doi.org/10.6028/NIST.AI.600-1) — cross-sector framing for confabulation, data privacy, harmful bias, human-AI configuration and dangerous content/capabilities.
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) — application-security framing for prompt injection, sensitive information disclosure, excessive agency and overreliance.
- [XSTest](https://arxiv.org/abs/2308.01263) — motivates harmful/benign contrast pairs and measuring exaggerated refusal rather than refusal alone.
- [HarmBench](https://arxiv.org/abs/2402.04249) — motivates standardized behavior categories and reproducible red-team evaluation.
- [StrongREJECT](https://arxiv.org/abs/2402.10260) — motivates scoring the harmful usefulness of a response rather than treating superficial non-refusal as a complete jailbreak.
- [Model evaluation for extreme risks](https://arxiv.org/abs/2305.15324) — motivates separating dangerous capability from a system's propensity to apply it harmfully.
- [EUROPA Eval](https://github.com/BirgerMoell/europa-eval) — provides the original multilingual runner, provenance, reporting and answer-explorer architecture from which this repository is derived.

These references have different scopes and licenses. EUROPA Alignment links to them rather than repackaging their data.

## Translation generator

The v0.1 machine-translated packs are produced locally with the Ollama checkpoint label `qwen3.6:35b-a3b`, revision `07d35212591f`, temperature 0, seed 42 and thinking disabled. This is generation provenance, not an endorsement or a native-quality claim.

## What a result must cite

A reproducible result identifies:

- EUROPA Alignment suite ID and version;
- target model ID, immutable revision and backend;
- target decoding settings and reasoning mode;
- independent judge model, immutable revision and protocol;
- exact item coverage and completion state; and
- model- or deployment-specific limitations.

The run artifact records these fields directly. Published results are behavioral evidence under that protocol—not safety certification.
