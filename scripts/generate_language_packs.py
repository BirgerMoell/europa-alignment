#!/usr/bin/env python3
"""Translate the authored alignment pack through a local Ollama model."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LANGUAGES_PATH = ROOT / "src/europa_alignment/resources/languages.json"
MASTER_PATH = ROOT / "src/europa_alignment/resources/pack-source-en.json"
PACK_DIR = ROOT / "src/europa_alignment/resources/language-packs"
PROTECTED = {
    "AC-771", "AUDIT-204", "D-204", "LANTERN",
    "STOP", "SYSTEM_SECRET", "draft_id", "send_available", "status",
}
OPTION_FIELDS = ("tool_options", "shutdown_options")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3.6:35b-a3b")
    parser.add_argument("--model-revision", default="07d35212591f")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    registry = read_json(LANGUAGES_PATH)
    master = read_json(MASTER_PATH)
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    selected = set(args.only)
    for language in registry["languages"]:
        code = language["code"]
        if selected and code not in selected:
            continue
        destination = PACK_DIR / f"{code}.json"
        if destination.exists() and not args.overwrite:
            try:
                existing = read_json(destination)
                validate_translation(master["strings"], existing["strings"], english=code == "eng")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                print(f"regenerate {code}: {exc}")
            else:
                print(f"skip {code}: {destination.name} exists")
                continue

        if code == "eng":
            translated = master["strings"]
            generator = "authored-source"
            generator_revision = None
            review_status = "source_native"
        else:
            print(f"translate {code}: {language['name']}")
            last_error: Exception | None = None
            for attempt in range(1, 4):
                try:
                    translated = translate(
                        strings=master["strings"], language=language,
                        model=args.model, base_url=args.base_url,
                    )
                    normalize_option_prefixes(translated)
                    validate_translation(master["strings"], translated, english=False)
                    break
                except Exception as exc:  # noqa: BLE001 - retry one isolated local generation
                    last_error = exc
                    print(f"retry {code} ({attempt}/3): {exc}")
                    time.sleep(attempt)
            else:
                raise RuntimeError(f"could not translate {code}: {last_error}") from last_error
            generator = args.model
            generator_revision = args.model_revision
            review_status = "machine_translated"

        destination.write_text(
            json.dumps(
                {
                    "language": language,
                    "review_status": review_status,
                    "translation_generator": generator,
                    "translation_model_revision": generator_revision,
                    "translation_protocol": {"temperature": 0, "seed": 42, "think": False},
                    "strings": translated,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    return 0


def translate(
    *, strings: dict[str, Any], language: dict[str, Any], model: str, base_url: str
) -> dict[str, Any]:
    system = (
        "You are a meticulous safety-evaluation translator. Return one valid JSON object "
        "with exactly the same keys, nesting, array lengths and message roles. Translate "
        "every natural-language string into the requested language. Preserve scenario meaning, "
        "risk level, names, option letters, JSON key names, uppercase literals and identifiers. "
        "Do not soften harmful requests or add safety advice: the target model is being tested. "
        "Preserve AC-771, AUDIT-204, D-204, LANTERN, STOP, SYSTEM_SECRET, "
        "draft_id, send_available and status exactly. Do not add explanations."
    )
    user = (
        f"Target language: {language['name']} ({language['autonym']})\n"
        f"ISO 639-3: {language['code']}\n"
        f"Required script: {language['scripts'][0]}\n"
        "Use only the target language and its required script for natural-language text. "
        "Do not leave English fragments or introduce characters from another script, except "
        "for the protected identifiers and fixed message roles.\n\n"
        "In shutdown_options, preserve the single token STOP but translate every other word; "
        "do not copy the English sentence around it.\n\n"
        + (
            "Script requirement: write Serbian natural-language text in Cyrillic, not Latin, "
            "except for the protected identifiers.\n\n"
            if language["code"] == "srp"
            else ""
        )
        + json.dumps(strings, ensure_ascii=False, indent=2)
    )
    request = urllib.request.Request(
        base_url.rstrip("/") + "/api/chat",
        data=json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0, "seed": 42, "num_predict": 12288},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=900) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = str(payload.get("message", {}).get("content", ""))
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    decoded = json.loads(content)
    if not isinstance(decoded, dict):
        raise ValueError("translation is not a JSON object")
    return decoded


def validate_translation(source: Any, translated: Any, *, english: bool, path: str = "strings") -> None:
    if isinstance(source, dict):
        if not isinstance(translated, dict) or source.keys() != translated.keys():
            raise ValueError(f"{path}: object keys differ")
        for key, value in source.items():
            validate_translation(value, translated[key], english=english, path=f"{path}.{key}")
        if path == "strings":
            serialized = json.dumps(translated, ensure_ascii=False)
            source_serialized = json.dumps(source, ensure_ascii=False)
            for literal in PROTECTED:
                if literal in source_serialized and literal not in serialized:
                    raise ValueError(f"protected literal disappeared: {literal}")
        return
    if isinstance(source, list):
        if not isinstance(translated, list) or len(source) != len(translated):
            raise ValueError(f"{path}: array shape changed")
        for index, value in enumerate(source):
            validate_translation(value, translated[index], english=english, path=f"{path}[{index}]")
        return
    if not isinstance(source, str) or not isinstance(translated, str) or not translated.strip():
        raise ValueError(f"{path}: expected non-empty text")
    if path.endswith(".role") and translated != source:
        raise ValueError(f"{path}: message role changed")
    if not english and not path.endswith(".role") and translated.casefold().strip() == source.casefold().strip():
        exempt = any(literal == source for literal in PROTECTED)
        if not exempt:
            raise ValueError(f"{path}: natural-language text was not translated")


def normalize_option_prefixes(translated: dict[str, Any]) -> None:
    for key in OPTION_FIELDS:
        normalized = []
        for expected_letter, option in zip("ABCD", translated[key]):
            text = str(option).strip()
            match = re.match(r"^[^\s.]+\.\s*(.+)$", text, re.DOTALL)
            if not match:
                raise ValueError(f"{key}: could not isolate option body for {expected_letter}")
            normalized.append(f"{expected_letter}. {match.group(1).strip()}")
        translated[key] = normalized


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
