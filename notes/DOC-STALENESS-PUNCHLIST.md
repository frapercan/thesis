# Thesis documentation staleness punch-list

Audit date: 2026-06-18. Worktree off `origin/main` (HEAD 7686752).
Scope: `chapters/*.tex` + `defensa.tex` + a quick Sphinx-docs scan.

This file lists staleness that is **number-dependent or needs a narrative
decision** and was therefore NOT fixed in this pass (the experiment round is
mid-flight; the LAFA numbers are not yet sealed natively). Safe,
number-independent fixes already applied are in the PR body, not here.

Format: `file:line` | issue | what it depends on / blocks on.

---

## 0. Audit verdict on the two "expected" fixes (context for the conductor)

The brief assumed a pgvector-for-KNN contradiction and an ESMC-300M error.
Neither is actually present as an error in the current manuscript:

- **pgvector**: every mention is correctly scoped to *storage only*, with KNN
  explicitly stated to run in NumPy/FAISS. Consistent across
  `04_system_design.tex:978-980`, `05_implementation.tex:114-121, 583-588`,
  `06_evaluation.tex:17-23`, `appendix_a.tex:24-36`. No fix needed.
- **ESMC-300M**: this is a *legitimate, documented* single-PLM baseline
  (`esmc_300m`, dim 960), distinct from the ensemble member `esmc_600m`
  (dim 1152). Confirmed in `protea-backends/docs/.../esm3c.rst` ("ESM-C 300M is
  classified as a single-PLM baseline reference and is not part of the 8-PLM
  ensemble") and `PROTEA/EXPERIMENTS.md` ("527K ESM-C 300M (dim=960)"). The
  thesis dims for both variants are correct. Flipping 300M -> 600M would
  *introduce* an error, so it was NOT done (see item 4 for the real,
  narrative-only concern).

Two genuine, number-independent cross-reference errors WERE found and fixed
(see PR body): a wrong ADR citation, and a stale "2nd place" CAFA claim on the
defense slide.

---

## 1. `\gridna` (Exp 9) and `\TODO` (Exp 10) placeholders: await sealed numbers

| file:line | issue | depends on |
|---|---|---|
| `chapters/06_evaluation.tex:442-466` | Multi-PLM x K generalisation grid (8 PLM rows x K in {3,5,10}) is entirely `\gridna` ("n/a") placeholders. | The leakage-clean SELECT-window grid run on the PROTEA `/benchmark` surface (cafaeval, GOA 226->230). Populate one cafaeval F_max per (PLM, K) cell only from completed runs; do NOT invent. |
| `chapters/06_evaluation.tex:530-532` | Exp 10 universal-reranker `f_micro_w` is a red `\TODO` block ("pending clean v227-lineage 227->230 recompute"). | The contamination-free v227-lineage GOA 227->230 recompute (in progress per the surrounding prose at 06:524-528). Replace the `\TODO` once verified leakage-clean. |

Note: `06:440` comment hard-codes "ProstT5/K5 is the established champion
(0.7291)" as a reviewer hint for the grid; keep consistent with whatever the
sealed grid reports.

## 2. Native-vs-offline 0.391 framing gap: central narrative decision

The 0.391 mean `f_micro_w` first-place result is the **offline research**
result. Ground truth: the on-platform NATIVE PROTEA reproduction is still in
progress (currently classifier-abstaining ~0.31, being unblocked). The thesis
asserts the sealed 0.391 as PROTEA's own and as served live from `/benchmark`.

| file:line | issue | depends on |
|---|---|---|
| `chapters/06_evaluation.tex:732-811` | Exp 13 titled "A Learned Re-Ranker Reaches First Place"; Table `tab:exp13-lafa` row "PROTEA (this work) ... 0.391" presented as the full PROTEA system. | A decision on whether to frame 0.391 as the *offline research* number (the #19-class research) vs *native PROTEA*. Until native reproduction lands, "PROTEA (this work)" overstates the platform. |
| `chapters/06_evaluation.tex:829-835` | Reproducibility para claims the sealed 0.391 "is served from the `/benchmark` surface ... the application is the single source of truth for the reported figure." | This is NOT yet true natively (~0.31 abstained). Either qualify as offline-lab-served, or hold until native reproduction confirms 0.391 on `/benchmark`. |
| `chapters/07_conclusion.tex:117, 125` | "IA-weighted micro-F of 0.391, against 0.381 ... first-place standing". | Same offline-vs-native distinction; tie the wording to the research result, not PROTEA-native. |
| `chapters/01_introduction.tex` (CAFA #19 lines 111-114, 387-388) + `07_conclusion.tex:108-110` | #19 (team result) and 0.391 (offline) are two separate achievements; ensure they are not conflated and that #19 is attributed to the research, not to PROTEA the product. | Narrative-clarity decision (numbers themselves are fine). |

## 3. Stacked meta-reranker (ADR-D43) pivot: not yet in the narrative

ADR-D43 (`PROTEA/docs/source/adr/D43-stacked-meta-reranker.rst`, Accepted
2026-06-17) replaces the monolithic single-level booster with a stacked
meta-reranker: a wide **EvidenceScorer** port (one calibrated score per
candidate per signal) feeding a shallow per-category **Combiner** over the
score vector. Motivation: the monolith collapsed PK (single-level 0.317 vs
linear 0.315 on the frame where the offline champion reaches 0.391).

| file:line | issue | depends on |
|---|---|---|
| `chapters/06_evaluation.tex:771-779` | Exp 13 describes "a learned combiner, fitted separately for each of the three evaluation settings" over homology + classifier + priors + association. This is the *pre-pivot* monolith framing, close to but predating the stacked architecture. | Decision on whether the thesis narrates the D43 stacked pivot (evidence-scorer ports + shallow combiner) or stays at the current per-category combiner description. If narrated, this is where it enters. |
| `chapters/07_conclusion.tex` future-work section | No mention of the stacked-meta-reranker architecture as the forward direction. | Same decision; natural home for the pivot as future/ongoing work if not folded into Exp 13. |

## 4. Other narrative/number-dependent tensions found (NOT fixed)

| file:line | issue | depends on |
|---|---|---|
| `chapters/07_conclusion.tex:221, 268` | "Main experiments use ESMC~300M" / "frozen ESMC-300M encoder". Correct per artifacts, but the manuscript interleaves the 300M single-PLM baseline with the 600M ensemble member without a one-line reader cue, which can read as inconsistent. | Narrative-clarity decision only (both dims are correct). Optional: add a sentence distinguishing 300M-baseline vs 600M-ensemble. NOT a factual fix. |
| `chapters/06_evaluation.tex:420` vs `04:853`/`05:858` | Grid lists 8 backends including "ESMC-300M"; the multi-PLM KNN ensemble (05:858, 05:937) uses "ESMC 600M". Two different model roles share the "ESMC" label. | Same clarity decision as above; intentional, not an error. |
| `chapters/06_evaluation.tex:803-807` (Exp 13 table) | Leaderboard rows (TransFew 0.381, FunBind 0.366, GOA-nonexp 0.325, DeepGOPlus 0.311) are reported to 3 dp on a single sealed window. | Confirm against the sealed `/benchmark` values once native reproduction lands; the prose at 06:823-827 already honestly flags single-window uncertainty. |
| `appendix_d.tex:380-411`, `appendix_b.tex:212-219` | "Indicative" / "pre-leakage-fix per-category" delta tables marked as indicative pending a leakage-free re-run. | The leakage-free per-category re-run noted in-text. Number-dependent. |

## 5. Sphinx docs (repositories/*/docs): freshness verdict

All seven PROTEA-family repos (PROTEA, protea-method, protea-backends,
protea-reranker-lab, protea-runners, protea-sources, protea-contracts) ship a
Sphinx `docs/` with autodoc configured (cafaeval-protea has docs/ but no
conf.py). The PROTEA core docs are **current and autogenerated**: the ADR index
already lists and toctrees D43 (updated 2026-06-17), and pgvector-for-storage /
KNN-excluded is correctly documented with the right ADR-001 citation across
`architecture/data_model.rst`, `complexity/faiss_knn.rst`, and
`related_work.rst`. The only staleness is in a few hand-written Markdown notes
outside the autodoc surface: `docs/CONFIG_INVENTORY.md` and
`adr/D37-...rst:78` / `appendix/howto_guides.rst:336` still reference the
deleted `train_reranker` operation/module (training moved to
protea-reranker-lab). The reranker-lab Sphinx docs do not yet mention the D43
stacked meta-reranker (lab docs last touched 2026-06-08, pivot landed
2026-06-17). Net: API docs are fresh; a light pass on the MD inventory notes and
a reranker-lab docs update for the stacked architecture are the only follow-ups.
