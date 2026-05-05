#!/usr/bin/env python3
"""
Protein-level paired bootstrap for CAFA-style Fmax CIs.

Precomputes per-protein per-tau TP and FP counts once, then resamples
protein indices with replacement to produce a bootstrap distribution of Fmax
(macro-averaged, CAFA normalization) for each namespace.

Usage:
    poetry run python thesis/scripts/bootstrap_fmax.py \
        --artifact storage/evaluation_artifacts/<uuid> \
        --obo data/go-basic.obo \
        --out thesis/data/bootstrap_<label>.json \
        --label baseline \
        --b 1000 \
        --seed 42
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from cafaeval.evaluation import compute_f
from cafaeval.parser import (
    gt_exclude_parser,
    gt_parser,
    obo_parser,
    pred_parser,
)

NAMESPACES = ("biological_process", "molecular_function", "cellular_component")


def precompute_per_protein_counts(
    p_mat: np.ndarray,  # (n_proteins, n_toi) float
    g_mat: np.ndarray,  # (n_proteins, n_toi) bool
    tau_arr: np.ndarray,  # (n_taus,) float
) -> tuple[np.ndarray, np.ndarray]:
    """Return (n_pred_pt, n_tp_pt), both (n_proteins, n_taus) int."""
    n_proteins, _ = p_mat.shape
    n_taus = len(tau_arr)
    n_pred_pt = np.zeros((n_proteins, n_taus), dtype=np.int32)
    n_tp_pt = np.zeros((n_proteins, n_taus), dtype=np.int32)
    # Loop over taus — each step is one boolean mask sum.
    for t_idx, tau in enumerate(tau_arr):
        mask = p_mat >= tau
        n_pred_pt[:, t_idx] = mask.sum(axis=1)
        n_tp_pt[:, t_idx] = np.logical_and(mask, g_mat).sum(axis=1)
    return n_pred_pt, n_tp_pt


def precompute_per_protein_counts_exclude(
    pred_matrix: np.ndarray,  # (n_proteins, n_terms_all) float
    gt_matrix: np.ndarray,  # (n_proteins, n_terms_all) bool
    toi: np.ndarray,  # (n_toi,) int
    exclude_matrix: np.ndarray,  # (n_proteins, n_terms_all) bool
    proteins_with_gt: np.ndarray,  # (n_sel,) int
    tau_arr: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-protein per-tau counts with protein-specific TOI (for PK/exclude).

    Returns (n_pred_pt, n_tp_pt, n_gt) — the per-protein GT count is computed
    here because the TOI varies per protein.
    """
    n_sel = len(proteins_with_gt)
    n_taus = len(tau_arr)
    n_pred_pt = np.zeros((n_sel, n_taus), dtype=np.int32)
    n_tp_pt = np.zeros((n_sel, n_taus), dtype=np.int32)
    n_gt = np.zeros(n_sel, dtype=np.int32)
    toi_set = set(toi.tolist())
    for i, p_idx in enumerate(proteins_with_gt):
        excluded = exclude_matrix[p_idx].nonzero()[0]
        toi_i = np.array(sorted(toi_set - set(excluded.tolist())), dtype=np.int64)
        g_i = gt_matrix[p_idx, toi_i]
        p_i = pred_matrix[p_idx, toi_i]
        n_gt[i] = g_i.sum()
        # vector of (n_taus,) boolean masks is expensive; do per-tau loop
        for t_idx, tau in enumerate(tau_arr):
            mask = p_i >= tau
            n_pred_pt[i, t_idx] = mask.sum()
            n_tp_pt[i, t_idx] = np.logical_and(mask, g_i).sum()
    return n_pred_pt, n_tp_pt, n_gt


def bootstrap_namespace(
    n_pred_pt: np.ndarray,  # (n_sel, n_taus) int
    n_tp_pt: np.ndarray,  # (n_sel, n_taus) int
    n_gt: np.ndarray,  # (n_sel,) int
    tau_arr: np.ndarray,
    B: int,
    rng: np.random.Generator,
) -> tuple[float, np.ndarray]:
    """Return (point_Fmax, bootstrap_Fmax_samples).

    Point estimate uses the full sample (CAFA normalization: sum of per-protein
    precision over proteins with at least one prediction; sum of per-protein
    recall over all proteins with GT, divided by number of proteins with GT).
    """
    n_sel, n_taus = n_pred_pt.shape

    denom_pred = np.where(n_pred_pt > 0, n_pred_pt, 1)
    pr_pt = n_tp_pt.astype(np.float64) / denom_pred
    pr_pt[n_pred_pt == 0] = 0.0

    n_gt_col = n_gt[:, None].astype(np.float64)
    denom_gt = np.where(n_gt_col > 0, n_gt_col, 1)
    rc_pt = n_tp_pt.astype(np.float64) / denom_gt
    rc_pt[n_gt_col.squeeze() == 0] = 0.0

    has_pred_pt = (n_pred_pt > 0).astype(np.int32)

    def _fmax_from(idx: np.ndarray) -> float:
        prec_sum = pr_pt[idx].sum(axis=0)
        rec_sum = rc_pt[idx].sum(axis=0)
        n_contrib = has_pred_pt[idx].sum(axis=0)
        ne = idx.size  # proteins with GT in sample
        pr = np.divide(
            prec_sum,
            n_contrib,
            out=np.zeros_like(prec_sum),
            where=n_contrib > 0,
        )
        rc = rec_sum / ne if ne > 0 else np.zeros_like(rec_sum)
        f = compute_f(pr, rc)
        return float(f.max())

    point = _fmax_from(np.arange(n_sel))

    samples = np.zeros(B, dtype=np.float64)
    for b in range(B):
        idx = rng.integers(0, n_sel, size=n_sel)
        samples[b] = _fmax_from(idx)
    return point, samples


def run_category(
    artifact_dir: Path,
    category: str,
    ontologies,
    tau_arr: np.ndarray,
    B: int,
    rng: np.random.Generator,
) -> dict:
    gt_file = artifact_dir / f"gt_{category}.tsv"
    pred_file = artifact_dir / "predictions" / "predictions.tsv"
    use_exclude = category == "PK"
    exclude_file = artifact_dir / "pk_known_terms.tsv" if use_exclude else None

    print(f"[{category}] parsing GT...", flush=True)
    t = time.time()
    gt = gt_parser(str(gt_file), ontologies)
    print(f"[{category}] gt parsed in {time.time()-t:.1f}s", flush=True)

    print(f"[{category}] parsing predictions...", flush=True)
    t = time.time()
    prediction = pred_parser(str(pred_file), ontologies, gt, prop_mode="max")
    print(f"[{category}] predictions parsed in {time.time()-t:.1f}s", flush=True)

    if use_exclude:
        print(f"[{category}] parsing exclude list...", flush=True)
        t = time.time()
        gt_exclude = gt_exclude_parser(str(exclude_file), gt, ontologies)
        print(f"[{category}] exclude parsed in {time.time()-t:.1f}s", flush=True)
    else:
        gt_exclude = None

    out = {"category": category, "namespaces": {}}

    for ns in NAMESPACES:
        if ns not in prediction:
            print(f"[{category}/{ns}] SKIP — no predictions", flush=True)
            continue
        toi = ontologies[ns].toi
        gt_mat = gt[ns].matrix
        pred_mat = prediction[ns].matrix

        proteins_has_gt = gt_mat[:, toi].sum(axis=1) > 0
        proteins_with_gt = np.where(proteins_has_gt)[0]
        n_sel = len(proteins_with_gt)
        print(f"[{category}/{ns}] n_proteins_with_gt={n_sel}", flush=True)

        t = time.time()
        if use_exclude:
            n_pred_pt, n_tp_pt, n_gt_vec = precompute_per_protein_counts_exclude(
                pred_mat,
                gt_mat,
                toi,
                gt_exclude[ns].matrix,
                proteins_with_gt,
                tau_arr,
            )
        else:
            g_sub = gt_mat[proteins_with_gt][:, toi]
            p_sub = pred_mat[proteins_with_gt][:, toi]
            n_pred_pt, n_tp_pt = precompute_per_protein_counts(p_sub, g_sub, tau_arr)
            n_gt_vec = g_sub.sum(axis=1)
        print(f"[{category}/{ns}] precompute {time.time()-t:.1f}s", flush=True)

        t = time.time()
        point, samples = bootstrap_namespace(
            n_pred_pt, n_tp_pt, n_gt_vec, tau_arr, B, rng
        )
        lo, hi = np.percentile(samples, [2.5, 97.5])
        mean = float(samples.mean())
        std = float(samples.std(ddof=1))
        print(
            f"[{category}/{ns}] Fmax={point:.4f} "
            f"CI95=[{lo:.4f},{hi:.4f}] mean={mean:.4f} sd={std:.4f} "
            f"({time.time()-t:.1f}s, B={B})",
            flush=True,
        )
        out["namespaces"][ns] = {
            "fmax": round(point, 4),
            "ci_lo": round(float(lo), 4),
            "ci_hi": round(float(hi), 4),
            "mean": round(mean, 4),
            "std": round(std, 4),
            "n_proteins": int(n_sel),
            "B": B,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--obo", required=True)
    ap.add_argument("--ia", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--b", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--tau-step", type=float, default=0.01)
    args = ap.parse_args()

    artifact_dir = Path(args.artifact)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    tau_arr = np.arange(args.tau_step, 1.0, args.tau_step)
    rng = np.random.default_rng(args.seed)

    print(f"parsing OBO ({args.obo})...", flush=True)
    t = time.time()
    ontologies = obo_parser(args.obo, ("is_a", "part_of"), args.ia, True)
    print(f"OBO parsed in {time.time()-t:.1f}s", flush=True)

    results = {
        "label": args.label,
        "artifact": str(artifact_dir.name),
        "B": args.b,
        "seed": args.seed,
        "tau_step": args.tau_step,
        "categories": {},
    }
    for cat in ("NK", "LK", "PK"):
        results["categories"][cat] = run_category(
            artifact_dir, cat, ontologies, tau_arr, args.b, rng
        )

    with out_path.open("w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
