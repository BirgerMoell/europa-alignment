#!/usr/bin/env python3
"""Reproduce every number, table and figure in the EUROPA Alignment paper.

Reads only the committed run artifacts in ``results/runs/`` and the bundled
suite. Writes LaTeX macros/tables to ``paper/generated/`` and figures to
``paper/figures/``. Dependencies: numpy and matplotlib.

    python3 paper/analysis.py
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results" / "runs"
OUT = ROOT / "paper" / "generated"
FIG = ROOT / "paper" / "figures"
SUITE = ROOT / "src/europa_alignment/resources/suites/europa-alignment-core-v0.1/dev.jsonl"
LANGS = json.loads((ROOT / "src/europa_alignment/resources/languages.json").read_text())
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261118)
B = 10_000

# Complete, independently judged runs (publication gate) in training order.
COMPLETE = [
    ("stage1", "birgermoell-oellm-9b-256k-stage1-instruct-v1-huggingface.json", "Stage-1 SFT"),
    ("sft", "neonkraft-oellm-9b-theta64m-instruct-sft-huggingface.json", "Dolci SFT"),
    ("dpo9k", "birgermoell-oellm-9b-threeway-dpo-step9000-huggingface.json", "DPO step 9k"),
    ("dpo", "birgermoell-oellm-9b-threeway-dpo-full-v1-huggingface.json", "DPO final"),
]
# Partial runs: deterministic items only, no judge configured.
PARTIAL = [
    ("apertus", "apertus-8b-instruct-2509-huggingface.json", "Apertus-8B-Instruct"),
    ("qwen", "qwen3-6-35b-a3b-ollama.json", "Qwen3.6-35B-A3B"),
]
# Dolci-Instruct-DPO-translated languages used in the DPO mixture (model card).
DPO_LANGS = {"ces", "deu", "ell", "eng", "spa", "fin", "fra", "ita", "pol", "ron", "swe", "ukr"}

TEMPLATE_ORDER = [
    "harmful-direct", "benign-security", "roleplay-indirect", "sycophancy",
    "delusion-support", "dependency-boundary", "manipulation", "privacy",
    "medical-uncertainty", "fairness", "prompt-injection", "tool-authorization",
    "cyber-defense", "dangerous-capability", "deceptive-reporting", "shutdown-compliance",
]
DOMAIN_ORDER = [
    ("refusal_calibration", "Refusal calibration"),
    ("human_wellbeing", "Human wellbeing"),
    ("privacy_security", "Privacy \\& security"),
    ("high_stakes_fairness", "High stakes \\& fairness"),
    ("dangerous_capabilities", "Dangerous capabilities"),
    ("agentic_control", "Agentic control"),
]

suite = [json.loads(line) for line in SUITE.read_text().splitlines() if line.strip()]
items = {x["id"]: x for x in suite}
lang_names = {}
for entry in (LANGS if isinstance(LANGS, list) else LANGS.get("languages", [])):
    code = entry.get("iso639_3") or entry.get("code") or entry.get("id")
    lang_names[code] = entry.get("name") or entry.get("english_name") or code


def load(fname):
    d = json.loads((RUNS / fname).read_text())
    by_id = {s["item_id"]: s for s in d["samples"]}
    return d, by_id


runs = {k: load(f) for k, f, _ in COMPLETE}
partial = {k: load(f) for k, f, _ in PARTIAL}
label = {k: l for k, _, l in COMPLETE + PARTIAL}
ids = [x["id"] for x in suite]


def vec(key, field="score", subset=None):
    _, by = runs[key]
    sel = subset or ids
    if field == "passed":
        return np.array([1.0 if by[i]["passed"] else 0.0 for i in sel])
    return np.array([float(by[i]["score"]) for i in sel])


def boot_mean(v):
    idx = RNG.integers(0, len(v), size=(B, len(v)))
    m = v[idx].mean(axis=1)
    return float(v.mean()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def cluster_boot(key, field="score"):
    """Bootstrap resampling *languages* (clusters of 16 parallel items)."""
    _, by = runs[key]
    langs = sorted({items[i]["language"] for i in ids})
    per = {l: np.array([float(by[i][field]) for i in ids if items[i]["language"] == l]) for l in langs}
    arr = np.stack([per[l] for l in langs])  # 36 x 16
    idx = RNG.integers(0, len(langs), size=(B, len(langs)))
    m = arr[idx].mean(axis=(1, 2))
    return float(arr.mean()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def paired_diff(a, b):
    """Paired bootstrap over templates x languages, clustered by language."""
    da, db = vec(a), vec(b)
    langs = sorted({items[i]["language"] for i in ids})
    li = {l: [n for n, i in enumerate(ids) if items[i]["language"] == l] for l in langs}
    diff = np.stack([da[li[l]] - db[li[l]] for l in langs])
    idx = RNG.integers(0, len(langs), size=(B, len(langs)))
    m = diff[idx].mean(axis=(1, 2))
    return float(diff.mean()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


macros: dict[str, str] = {}


def mac(name, value, fmt="{:.3f}"):
    text = fmt.format(value) if not isinstance(value, str) else value
    if text.startswith("-") and text[1:2].isdigit():
        text = "\\textminus " + text[1:]
    macros[name] = text


def pct(x):
    return f"{100 * x:.1f}"


# ---------------------------------------------------------------- main table
rows = []
for key, _, lab in COMPLETE:
    d, by = runs[key]
    s = d["summary"]
    sc, lo, hi = cluster_boot(key)
    pr, plo, phi = cluster_boot(key, "passed")
    deterministic = [i for i in ids if items[i]["scoring"]["type"] == "choice"]
    rows.append(dict(
        key=key, label=lab, score=sc, lo=lo, hi=hi, pass_rate=pr,
        macro_lang=s["language_profile"]["macro_language_score"],
        min_lang=s["language_profile"]["minimum_language_score"],
        min_lang_id=min(s["languages"], key=lambda x: x["score"])["id"],
        macro_dom=s["capability_profile"]["macro_domain_score"],
        min_dom=s["capability_profile"]["minimum_domain_score"],
        gate=s["critical_gates"]["failure_rate"],
        retention=s["contrast_sets"]["pair_retention_rate"],
        echo=s["output_diagnostics"]["prompt_echo_rate"],
        malformed=s["counts"]["malformed"],
        median_tokens=s["output_diagnostics"].get("median_output_tokens"),
        latency=s["latency"]["median_ms"] / 1000,
        hours=(np.datetime64(d["finished_at"][:19]) - np.datetime64(d["started_at"][:19])).astype("timedelta64[m]").astype(int) / 60,
        revision=d["model"]["revision"][:10],
        model_id=d["model"]["id"],
        device=d["protocol"]["backend_settings"].get("resolved_device", ""),
        det=float(np.mean([by[i]["score"] for i in deterministic])),
        det_pass=float(np.mean([by[i]["passed"] for i in deterministic])),
    ))
    tag = {"stage1": "StageOne", "sft": "SFT", "dpo9k": "DPOnine", "dpo": "DPO"}[key]
    mac(f"score{tag}", sc)
    mac(f"scoreLo{tag}", lo)
    mac(f"scoreHi{tag}", hi)
    mac(f"pass{tag}", pct(pr), "{}")
    mac(f"gate{tag}", pct(rows[-1]["gate"]), "{}")
    mac(f"retention{tag}", pct(rows[-1]["retention"]), "{}")
    mac(f"echo{tag}", pct(rows[-1]["echo"]), "{}")
    mac(f"minLang{tag}", rows[-1]["min_lang"])
    mac(f"minDom{tag}", rows[-1]["min_dom"])
    mac(f"det{tag}", rows[-1]["det"])
    mac(f"detPass{tag}", pct(rows[-1]["det_pass"]), "{}")
    mac(f"hours{tag}", rows[-1]["hours"], "{:.1f}")

with open(OUT / "table_main.tex", "w") as f:
    f.write("\\begin{tabular}{lcccccccc}\n\\toprule\n")
    f.write("Checkpoint & Score [95\\% CI] & Pass & Macro lang. & Min lang. & Min domain & Gate fail & Pair ret. & Echo \\\\\n\\midrule\n")
    for r in rows:
        f.write(f"{r['label']} & {r['score']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}] & {pct(r['pass_rate'])}\\% & "
                f"{r['macro_lang']:.3f} & {r['min_lang']:.3f} (\\texttt{{{r['min_lang_id']}}}) & {r['min_dom']:.3f} & "
                f"{pct(r['gate'])}\\% & {pct(r['retention'])}\\% & {pct(r['echo'])}\\% \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

with open(OUT / "table_provenance.tex", "w") as f:
    f.write("\\begin{tabular}{llllr}\n\\toprule\n")
    f.write("Label & Model (Hugging Face ID) & Revision & Device & Wall-clock (h) \\\\\n\\midrule\n")
    for r in rows:
        mid = r["model_id"].replace("_", "\\_")
        f.write(f"{r['label']} & \\scriptsize\\texttt{{{mid}}} & \\texttt{{{r['revision']}}} & {r['device'].split(':')[0]} & {r['hours']:.1f} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- paired diffs
for a, b, name in [("sft", "stage1", "SFTvsStageOne"), ("dpo", "sft", "DPOvsSFT"), ("dpo", "dpo9k", "DPOvsNine")]:
    m, lo, hi = paired_diff(a, b)
    mac(f"diff{name}", m, "{:+.3f}")
    mac(f"diffLo{name}", lo, "{:+.3f}")
    mac(f"diffHi{name}", hi, "{:+.3f}")

# ---------------------------------------------------------------- domain table
with open(OUT / "table_domains.tex", "w") as f:
    f.write("\\begin{tabular}{l" + "c" * len(COMPLETE) + "}\n\\toprule\nDomain & " +
            " & ".join(l for _, _, l in COMPLETE) + " \\\\\n\\midrule\n")
    for did, dname in DOMAIN_ORDER:
        vals = []
        for key, _, _ in COMPLETE:
            dd = {x["id"]: x for x in runs[key][0]["summary"]["domains"]}
            vals.append(dd[did]["score"])
        best = max(vals)
        cells = [(f"\\textbf{{{v:.3f}}}" if v == best else f"{v:.3f}") for v in vals]
        f.write(f"{dname} & " + " & ".join(cells) + " \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- template heatmap
tmpl = np.zeros((len(TEMPLATE_ORDER), len(COMPLETE)))
for j, (key, _, _) in enumerate(COMPLETE):
    by = runs[key][1]
    for i, t in enumerate(TEMPLATE_ORDER):
        tmpl[i, j] = np.mean([by[x]["score"] for x in ids if items[x]["template_id"] == t])

fig, ax = plt.subplots(figsize=(4.6, 5.6))
im = ax.imshow(tmpl, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(COMPLETE)), [l for _, _, l in COMPLETE], rotation=30, ha="right", fontsize=8)
ax.set_yticks(range(len(TEMPLATE_ORDER)), TEMPLATE_ORDER, fontsize=8)
for i in range(tmpl.shape[0]):
    for j in range(tmpl.shape[1]):
        ax.text(j, i, f"{tmpl[i, j]:.2f}", ha="center", va="center", fontsize=7,
                color="black" if 0.25 < tmpl[i, j] < 0.85 else "white")
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02).ax.tick_params(labelsize=7)
ax.set_title("Mean item score per scenario template (36 languages)", fontsize=9)
fig.tight_layout()
fig.savefig(FIG / "template_heatmap.pdf")
plt.close(fig)
for i, t in enumerate(TEMPLATE_ORDER):
    tag = "".join(p.capitalize() for p in t.split("-"))
    for j, (key, _, _) in enumerate(COMPLETE):
        ktag = {"stage1": "StageOne", "sft": "SFT", "dpo9k": "DPOnine", "dpo": "DPO"}[key]
        mac(f"t{tag}{ktag}", tmpl[i, j], "{:.2f}")

# ---------------------------------------------------------------- language heatmap
langs = sorted({items[i]["language"] for i in ids})
L = np.zeros((len(langs), len(COMPLETE)))
for j, (key, _, _) in enumerate(COMPLETE):
    by = runs[key][1]
    for i, l in enumerate(langs):
        L[i, j] = np.mean([by[x]["score"] for x in ids if items[x]["language"] == l])
order = np.argsort(L[:, -1])
fig, ax = plt.subplots(figsize=(7.2, 2.9))
mat = L[order].T
im = ax.imshow(mat, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
ax.set_yticks(range(len(COMPLETE)), [l for _, _, l in COMPLETE], fontsize=8)
xl = [langs[k] + ("*" if langs[k] in DPO_LANGS else "") for k in order]
ax.set_xticks(range(len(langs)), xl, rotation=90, fontsize=7, family="monospace")
fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01).ax.tick_params(labelsize=7)
ax.set_title("Mean score per language (sorted by final DPO; * = language present in DPO data)", fontsize=8.5)
fig.tight_layout()
fig.savefig(FIG / "language_heatmap.pdf")
plt.close(fig)

# ---------------------------------------------------------------- DPO-language analysis
sft_l = {l: L[i, 1] for i, l in enumerate(langs)}
dpo_l = {l: L[i, 3] for i, l in enumerate(langs)}
delta = {l: dpo_l[l] - sft_l[l] for l in langs}
inn = np.array([delta[l] for l in langs if l in DPO_LANGS])
out = np.array([delta[l] for l in langs if l not in DPO_LANGS and l != "kat"])
out_all = np.array([delta[l] for l in langs if l not in DPO_LANGS])
obs = inn.mean() - out.mean()
pool = np.concatenate([inn, out])
perm = np.array([(lambda p: p[:len(inn)].mean() - p[len(inn):].mean())(RNG.permutation(pool)) for _ in range(B)])
p_perm = float((np.abs(perm) >= abs(obs)).mean())
mac("dpoDeltaIn", inn.mean(), "{:+.3f}")
mac("dpoDeltaOut", out.mean(), "{:+.3f}")
mac("dpoDeltaOutAll", out_all.mean(), "{:+.3f}")
mac("dpoDeltaGap", obs, "{:+.3f}")
mac("dpoDeltaP", p_perm, "{:.2f}")
mac("dpoNOut", str(len(out)))
mac("dpoDeltaMinOut", float(out.min()), "{:+.3f}")
mac("dpoOutPositive", str(int((out > 0).sum())))

fig, ax = plt.subplots(figsize=(3.4, 2.7))
xs = np.array([sft_l[l] for l in langs])
ys = np.array([dpo_l[l] for l in langs])
mask = np.array([l in DPO_LANGS for l in langs])
ax.scatter(xs[~mask], ys[~mask], s=14, label="not in DPO data", color="#4c78a8")
ax.scatter(xs[mask], ys[mask], s=18, marker="s", label="in DPO data", color="#e45756")
ax.plot([0, 1], [0, 1], ls="--", lw=0.8, color="grey")
for l, x, y in zip(langs, xs, ys):
    if l in ("kat", "deu", "eus", "mlt", "slv", "swe"):
        ax.annotate(l, (x, y), fontsize=6.5, xytext=(3, -3), textcoords="offset points")
ax.set_xlabel("Dolci SFT language score", fontsize=8)
ax.set_ylabel("DPO final language score", fontsize=8)
ax.tick_params(labelsize=7)
ax.legend(fontsize=6.5, loc="lower right")
ax.set_xlim(0.1, 1.0)
ax.set_ylim(0.1, 1.0)
fig.tight_layout()
fig.savefig(FIG / "dpo_transfer.pdf")
plt.close(fig)

# ---------------------------------------------------------------- refusal-calibration quadrants
quad_rows = []
for key, _, lab in COMPLETE:
    by = runs[key][1]
    c = Counter()
    for l in langs:
        h = by[f"europa-align-v01-{l}-harmful-direct"]["passed"]
        b = by[f"europa-align-v01-{l}-benign-security"]["passed"]
        c[("both" if h and b else "over" if h else "under" if b else "neither")] += 1
    quad_rows.append((lab, c))
    ktag = {"stage1": "StageOne", "sft": "SFT", "dpo9k": "DPOnine", "dpo": "DPO"}[key]
    for q in ("both", "over", "under", "neither"):
        mac(f"q{q.capitalize()}{ktag}", str(c[q]))
with open(OUT / "table_quadrants.tex", "w") as f:
    f.write("\\begin{tabular}{lcccc}\n\\toprule\nCheckpoint & Calibrated & Over-refusal & Under-refusal & Neither \\\\\n"
            " & (refuse \\& help) & (refuse only) & (help only) & \\\\\n\\midrule\n")
    for lab, c in quad_rows:
        f.write(f"{lab} & {c['both']} & {c['over']} & {c['under']} & {c['neither']} \\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- Georgian / tokenizer fertility
def lang_stats(key):
    by = runs[key][1]
    res = {}
    eng_in = {items[x]["template_id"]: by[x]["input_tokens"] for x in ids if items[x]["language"] == "eng"}
    for l in langs:
        sel = [x for x in ids if items[x]["language"] == l]
        fert = np.mean([by[x]["input_tokens"] / eng_in[items[x]["template_id"]] for x in sel])
        repl = np.mean(["\ufffd" in (by[x]["response"] or "") for x in sel])
        trunc = np.mean([by[x].get("finish_reason") == "length" for x in sel])
        res[l] = (fert, repl, trunc, np.mean([by[x]["score"] for x in sel]))
    return res

ls_dpo = lang_stats("dpo")
fert = np.array([ls_dpo[l][0] for l in langs])
score = np.array([ls_dpo[l][3] for l in langs])
mac("fertKat", ls_dpo["kat"][0], "{:.2f}")
mac("replKat", pct(ls_dpo["kat"][1]), "{}")
mac("truncKat", pct(ls_dpo["kat"][2]), "{}")
mac("truncMedianOther", pct(float(np.median([ls_dpo[l][2] for l in langs if l != "kat"]))), "{}")
mac("replMaxOther", pct(max(ls_dpo[l][1] for l in langs if l != "kat")), "{}")
mac("fertMaxOther", max(ls_dpo[l][0] for l in langs if l != "kat"), "{:.2f}")
mac("fertMaxOtherLang", max((ls_dpo[l][0], l) for l in langs if l != "kat")[1])
mac("fertMedian", float(np.median(fert)), "{:.2f}")
nk = np.array([l != "kat" for l in langs])
r_with = float(np.corrcoef(fert, score)[0, 1])
r_without = float(np.corrcoef(fert[nk], score[nk])[0, 1])
mac("fertCorr", r_with, "{:+.2f}")
mac("fertCorrNoKat", r_without, "{:+.2f}")
for key in ("stage1", "sft", "dpo9k", "dpo"):
    ktag = {"stage1": "StageOne", "sft": "SFT", "dpo9k": "DPOnine", "dpo": "DPO"}[key]
    mac(f"kat{ktag}", lang_stats(key)["kat"][3])
# second-worst language per run
for key in ("sft", "dpo"):
    ktag = {"sft": "SFT", "dpo": "DPO"}[key]
    srt = sorted((v[3], l) for l, v in lang_stats(key).items())
    mac(f"secondWorst{ktag}", srt[1][1])
    mac(f"secondWorstScore{ktag}", srt[1][0])

fig, ax = plt.subplots(figsize=(3.4, 2.5))
ax.scatter(fert[nk], score[nk], s=14, color="#4c78a8")
ax.scatter(fert[~nk], score[~nk], s=22, color="#e45756", marker="D")
ax.annotate("kat (Georgian)", (fert[~nk][0], score[~nk][0]), fontsize=7, xytext=(-62, 4), textcoords="offset points")
ax.set_xlabel("Prompt tokens relative to English (same template)", fontsize=8)
ax.set_ylabel("DPO final language score", fontsize=8)
ax.tick_params(labelsize=7)
fig.tight_layout()
fig.savefig(FIG / "fertility.pdf")
plt.close(fig)

# ---------------------------------------------------------------- checkpoint stability (step 9k vs final)
p9 = vec("dpo9k", "passed")
pf = vec("dpo", "passed")
agree = float((p9 == pf).mean())
po = agree
pe = p9.mean() * pf.mean() + (1 - p9.mean()) * (1 - pf.mean())
kappa = (po - pe) / (1 - pe)
s9, sf = vec("dpo9k"), vec("dpo")
mac("stabAgree", pct(agree), "{}")
mac("stabKappa", kappa, "{:.2f}")
mac("stabIdentical", pct(float((np.abs(s9 - sf) < 1e-9).mean())), "{}")
mac("stabFlips", str(int((p9 != pf).sum())))

# ---------------------------------------------------------------- judge diagnostics
dims_all = Counter()
gate_applied = 0
rubric_n = 0
lq = defaultdict(list)
for key, _, _ in COMPLETE:
    for x in ids:
        s = runs[key][1][x]
        if s["scorer"] != "rubric":
            continue
        rubric_n += 1
        sd = s.get("score_details") or {}
        if sd.get("critical_gate_applied"):
            gate_applied += 1
        p = s.get("parsed") or {}
        if "language_quality" in p:
            lq[key].append(p["language_quality"])
mac("rubricJudgments", f"{rubric_n:,}".replace(",", "{,}"))
mac("judgeGateShare", pct(gate_applied / rubric_n), "{}")
mac("lqStageOne", float(np.mean(lq["stage1"])), "{:.2f}")
mac("lqDPO", float(np.mean(lq["dpo"])), "{:.2f}")
judge_lat = [runs["dpo"][1][x]["judgment"]["latency_ms"] for x in ids if runs["dpo"][1][x].get("judgment")]
mac("judgeLatency", float(np.median(judge_lat)) / 1000, "{:.1f}")

# ---------------------------------------------------------------- deterministic items incl. partial runs
det_ids = [i for i in ids if items[i]["scoring"]["type"] == "choice"]
with open(OUT / "table_deterministic.tex", "w") as f:
    f.write("\\begin{tabular}{lcccc}\n\\toprule\nModel & Score & Strict pass & Contract violations & Run \\\\\n\\midrule\n")
    for key, _, lab in COMPLETE + PARTIAL:
        by = (runs.get(key) or partial[key])[1]
        sc = np.mean([by[i]["score"] for i in det_ids])
        ps = np.mean([by[i]["passed"] for i in det_ids])
        half = sum(1 for i in det_ids if by[i]["score"] == 0.5)
        kind = "complete" if key in runs else "partial, no judge"
        f.write(f"{lab} & {sc:.3f} & {pct(ps)}\\% & {half}/72 & {kind} \\\\\n")
        ktag = {"apertus": "Apertus", "qwen": "Qwen"}.get(key)
        if ktag:
            mac(f"det{ktag}", sc)
            mac(f"detPass{ktag}", pct(ps), "{}")
            mac(f"half{ktag}", str(half))
    f.write("\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- suite stats
mac("nItems", str(len(ids)))
mac("nLangs", str(len(langs)))
mac("nRubric", str(sum(1 for i in ids if items[i]["scoring"]["type"] == "rubric")))
mac("nChoice", str(len(det_ids)))
mac("nMultiTurn", str(sum(1 for i in ids if items[i]["task_type"] == "multi_turn_open_generation")))
mac("judgeId", runs["dpo"][0]["judge"]["id"])
mac("judgeRev", runs["dpo"][0]["judge"]["revision"].split(":")[-1][:12])

with open(OUT / "macros.tex", "w") as f:
    f.write("% Auto-generated by paper/analysis.py -- do not edit by hand.\n")
    for k, v in sorted(macros.items()):
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")

print(json.dumps(macros, indent=1))
