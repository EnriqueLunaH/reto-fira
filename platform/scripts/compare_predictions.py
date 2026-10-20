"""Audit three submissions and reproduce metrics without treating agreement as accuracy.

Run from the repository root:
    .\platform\.venv\Scripts\python.exe platform/scripts/compare_predictions.py

Only comparison-* files are written. Source CSVs, trained models, predictions and
reported metrics are never modified. Peer validation numbers are transcribed from
their supplied Markdown reports; their OOF predictions/code are not available.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SEED = 20261014
BOOTSTRAPS = 5000
SUBMISSIONS = {
    "ours": ("platform/artifacts/predicciones_59.csv", "ID_parcela", "Rendimiento_predicho_t_ha"),
    "agrocebada_hidden": ("comparisons/agrocebada_hidden.csv", "ID", "prediction_t_ha"),
    "Predicciones_agroceba": ("comparisons/Predicciones-agroceba.csv", "ID_POLIGONO", "PREDICCION_T_HA"),
}


def fingerprint(path: Path, root: Path) -> dict:
    return {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def numbers(actual, predicted) -> dict:
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    residual = predicted - actual
    mse = float(np.mean(residual ** 2))
    sst = float(np.sum((actual - actual.mean()) ** 2))
    return {"n": len(actual), "mae": float(np.mean(abs(residual))), "mse": mse,
            "rmse": float(np.sqrt(mse)), "r2": 1 - float(np.sum(residual ** 2)) / sst if sst else None,
            "bias": float(np.mean(residual))}


def bootstrap_intervals(actual, predicted) -> dict:
    """Percentile CI conditional on fixed OOF predictions, not full refitting uncertainty."""
    rng = np.random.default_rng(SEED)
    actual, predicted = np.asarray(actual), np.asarray(predicted)
    idx = rng.integers(0, len(actual), size=(BOOTSTRAPS, len(actual)))
    y, p = actual[idx], predicted[idx]
    diff = p - y
    sst = np.sum((y - y.mean(axis=1, keepdims=True)) ** 2, axis=1)
    samples = {"mae": np.mean(abs(diff), axis=1), "rmse": np.sqrt(np.mean(diff ** 2, axis=1)),
               "r2": 1 - np.sum(diff ** 2, axis=1) / sst,
               "bias": diff.mean(axis=1)}
    return {name: dict(zip(("lower_95", "upper_95"), map(float, np.quantile(vals, [.025, .975]))))
            for name, vals in samples.items()}


def assert_check(checks: dict, name: str, value: bool):
    checks[name] = bool(value)
    if not value:
        raise ValueError(f"Failed integrity check: {name}")


def reported_peer_metrics() -> list[dict]:
    # Explicitly reported figures, not independently reproducible measurements.
    return [
        {"submission": "agrocebada_hidden", "scheme": "random_parcel_repeated_evaluations", "n": 1380,
         "mae": .3778, "rmse": .5284, "r2": .6118, "status": "reported_only",
         "source": "comparisons/agrocebada_hidden.md", "section": "2. Métricas principales"},
        {"submission": "agrocebada_hidden", "scheme": "random_parcel_mean_of_10_oof", "n": 138,
         "mae": .3682, "rmse": .5196, "r2": .6246, "status": "reported_only",
         "source": "comparisons/agrocebada_hidden.md", "section": "2. Métricas principales"},
        {"submission": "agrocebada_hidden", "scheme": "spatial_kmeans5", "n": 138,
         "mae": .7277, "rmse": .8925, "r2": -.1076, "status": "reported_only",
         "source": "comparisons/agrocebada_hidden.md", "section": "3. Comparación con líneas base"},
        {"submission": "Predicciones_agroceba", "scheme": "random_parcel_nested_selector", "n": 138,
         "mae": .4190, "rmse": .5519, "r2": .5765, "status": "reported_only",
         "source": "comparisons/Predicciones-agroceba.md", "section": "3.2 Selección de grupo de variables"},
        {"submission": "Predicciones_agroceba", "scheme": "spatial_chirps_nested_selector", "n": 138,
         "mae": .6390, "rmse": .7775, "r2": .1594, "status": "reported_only",
         "source": "comparisons/Predicciones-agroceba.md", "section": "3.2 Selección de grupo de variables"},
    ]


def run(root: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    master_path = root / "data/fira/CSV-files/ID_area_rendimiento_70_30_Reto_AgroCebada.csv"
    master = pd.read_csv(master_path, encoding="utf-8-sig")
    master = master.loc[:, ~master.columns.str.startswith("Unnamed:")]
    checks = {}
    assert_check(checks, "master_197_unique_ids", len(master) == 197 and master.ID_POLIGONO.is_unique)
    hidden = master.loc[master.CONJUNTO.eq("PREDICCION")].copy()
    training = master.loc[master.CONJUNTO.eq("ENTRENAMIENTO")].copy()
    assert_check(checks, "master_138_labels_59_hidden", len(training) == 138 and len(hidden) == 59
                 and training.RENDIMIENTO_T_HA.notna().all() and hidden.RENDIMIENTO_T_HA.isna().all())
    expected_ids = set(hidden.ID_POLIGONO)
    meta_path = root / "platform/artifacts/parcels.csv"
    metadata = pd.read_csv(meta_path)
    assert_check(checks, "parcel_metadata_197_unique_matches_official_ids",
                 len(metadata) == 197 and metadata.ID_POLIGONO.is_unique
                 and set(metadata.ID_POLIGONO) == set(master.ID_POLIGONO))
    aligned_meta = metadata.set_index("ID_POLIGONO").loc[master.ID_POLIGONO]
    assert_check(checks, "parcel_metadata_areas_targets_partitions_match_official",
                 np.allclose(aligned_meta.AREA_HA, master.AREA_HA, rtol=0, atol=1e-12)
                 and np.allclose(aligned_meta.RENDIMIENTO_T_HA, master.RENDIMIENTO_T_HA,
                                 rtol=0, atol=1e-12, equal_nan=True)
                 and aligned_meta.CONJUNTO.tolist() == master.CONJUNTO.tolist())
    merged = hidden[["ID_POLIGONO", "AREA_HA"]].merge(
        metadata[["ID_POLIGONO", "Estado", "Municipio", "longitude", "latitude"]],
        on="ID_POLIGONO", how="left", validate="one_to_one")
    inputs = [master_path, meta_path]
    audits = []
    for name, (relative, id_col, pred_col) in SUBMISSIONS.items():
        path = root / relative
        frame = pd.read_csv(path, encoding="utf-8-sig")
        raw_ids = frame[id_col].astype("string")
        pred = pd.to_numeric(frame[pred_col], errors="coerce")
        ids = set(raw_ids.dropna())
        audit = {"submission": name, "path": relative, "row_count": len(frame),
                 "id_column": id_col, "yield_column": pred_col, "units": "t/ha (declared by column name)",
                 "duplicate_id_rows": int(raw_ids.duplicated().sum()), "missing_id_rows": int(raw_ids.isna().sum()),
                 "missing_prediction_rows": int(pred.isna().sum()), "nonfinite_prediction_rows": int((~np.isfinite(pred)).sum()),
                 "whitespace_ids": int(raw_ids.ne(raw_ids.str.strip()).sum()),
                 "invalid_id_pattern_rows": int((~raw_ids.str.fullmatch(r"AGC_\d{3}", na=False)).sum()),
                 "missing_official_ids": sorted(expected_ids - ids), "unexpected_ids": sorted(ids - expected_ids),
                 "official_order_match": raw_ids.tolist() == hidden.ID_POLIGONO.tolist(),
                 "nonpositive_predictions": int((pred <= 0).sum()),
                 "min": float(pred.min()), "max": float(pred.max()), "mean": float(pred.mean()),
                 "median": float(pred.median()), "sample_std": float(pred.std(ddof=1)),
                 "full_column_names": frame.columns.tolist()}
        assert_check(checks, f"{name}_59_valid_unique_finite_hidden_predictions",
                     len(frame) == 59 and raw_ids.is_unique and not raw_ids.isna().any()
                     and np.isfinite(pred).all() and ids == expected_ids
                     and audit["whitespace_ids"] == 0 and audit["invalid_id_pattern_rows"] == 0)
        normalized = pd.DataFrame({"ID_POLIGONO": raw_ids, name: pred})
        merged = merged.merge(normalized, on="ID_POLIGONO", how="left", validate="one_to_one")
        if name == "agrocebada_hidden":
            aligned = frame.set_index(id_col).loc[hidden.ID_POLIGONO]
            area = hidden.set_index("ID_POLIGONO").AREA_HA
            assert_check(checks, "agrocebada_hidden_areas_match_official",
                         np.allclose(aligned.AREA_HA, area, rtol=0, atol=1e-12))
            assert_check(checks, "agrocebada_hidden_target_empty_and_partition_correct",
                         aligned.RENDIMIENTO_T_HA.isna().all() and aligned.CONJUNTO.eq("PREDICCION").all())
            assert_check(checks, "agrocebada_hidden_production_matches_area_times_yield",
                         np.allclose(aligned.production_t, aligned.AREA_HA * aligned.prediction_t_ha, rtol=1e-12))
            interval_ok = all((aligned[f"lower_{level}"] <= aligned.prediction_t_ha).all()
                              and (aligned.prediction_t_ha <= aligned[f"upper_{level}"]).all() for level in (80, 90, 95))
            interval_ok = interval_ok and (aligned.lower_95 <= aligned.lower_90).all() \
                and (aligned.lower_90 <= aligned.lower_80).all() and (aligned.upper_80 <= aligned.upper_90).all() \
                and (aligned.upper_90 <= aligned.upper_95).all()
            assert_check(checks, "agrocebada_hidden_intervals_ordered_and_nested", interval_ok)
        audits.append(audit)
        inputs.append(path)

    names = list(SUBMISSIONS)
    merged["prediction_range_t_ha"] = merged[names].max(axis=1) - merged[names].min(axis=1)
    merged["prediction_sample_std_t_ha"] = merged[names].std(axis=1, ddof=1)
    pairwise = []
    for a, b in itertools.combinations(names, 2):
        difference = merged[a] - merged[b]
        merged[f"{a}_minus_{b}_t_ha"] = difference
        pairwise.append({"a": a, "b": b, "n": len(difference),
                         "mean_signed_difference_a_minus_b_t_ha": float(difference.mean()),
                         "mean_absolute_difference_t_ha": float(abs(difference).mean()),
                         "root_mean_squared_difference_t_ha": float(np.sqrt(np.mean(difference ** 2))),
                         "median_absolute_difference_t_ha": float(abs(difference).median()),
                         "max_absolute_difference_t_ha": float(abs(difference).max()),
                         "max_difference_id": merged.loc[abs(difference).idxmax(), "ID_POLIGONO"],
                         "pearson_r": float(merged[a].corr(merged[b])),
                         "spearman_rho": float(merged[a].corr(merged[b], method="spearman"))})
    merged.to_csv(out / "comparison-predictions.csv", index=False, float_format="%.12g")
    pd.DataFrame(pairwise).to_csv(out / "comparison-pairwise.csv", index=False, float_format="%.12g")
    pd.DataFrame(audits).drop(columns=["full_column_names", "missing_official_ids", "unexpected_ids"]).to_csv(
        out / "comparison-input-audit.csv", index=False, float_format="%.12g")

    metrics_path = root / "platform/artifacts/metrics.json"
    reported = json.loads(metrics_path.read_text(encoding="utf-8"))
    inputs.append(metrics_path)
    validation = {}
    validation_metrics = []
    slices = []
    errors = []
    train_lookup = training.set_index("ID_POLIGONO").RENDIMIENTO_T_HA
    for scheme in ("parcel", "spatial"):
        path = root / f"platform/artifacts/validation-{scheme}.csv"
        frame = pd.read_csv(path)
        assert_check(checks, f"{scheme}_validation_complete_once_per_training_parcel",
                     len(frame) == 138 and frame.ID_parcela.is_unique and set(frame.ID_parcela) == set(train_lookup.index))
        assert_check(checks, f"{scheme}_validation_actuals_match_official",
                     np.allclose(frame.actual, train_lookup.loc[frame.ID_parcela], rtol=0, atol=1e-12))
        assert_check(checks, f"{scheme}_validation_predictions_finite",
                     np.isfinite(frame[["actual", "predicted", "baseline"]]).all().all())
        source_metrics = reported[f"{scheme}_cv"]
        model, baseline = numbers(frame.actual, frame.predicted), numbers(frame.actual, frame.baseline)
        for kind, stats in (("model", model), ("baseline", baseline)):
            assert_check(checks, f"{scheme}_{kind}_csv_reproduces_reported_metrics",
                         all(np.isclose(stats[metric], source_metrics[kind][metric], rtol=0, atol=1e-12)
                             for metric in ("n", "mae", "rmse", "r2", "bias")))
            validation_metrics.append({"submission": "ours", "scheme": scheme, "predictor": kind,
                                       **stats, "status": "recomputed_from_oof_csv", "source": path.relative_to(root).as_posix()})
        bounded = np.isfinite(frame.lower) & np.isfinite(frame.upper)
        coverage = float(((frame.loc[bounded, "actual"] >= frame.loc[bounded, "lower"]) &
                          (frame.loc[bounded, "actual"] <= frame.loc[bounded, "upper"])).mean())
        width = float((frame.loc[bounded, "upper"] - frame.loc[bounded, "lower"]).mean())
        assert_check(checks, f"{scheme}_coverage_denominator_reproduced",
                     int(bounded.sum()) == source_metrics["interval_evaluation_n"]
                     and int((~bounded).sum()) == source_metrics["unbounded_interval_n"]
                     and np.isclose(coverage, source_metrics["coverage_90"]) and np.isclose(width, source_metrics["mean_interval_width"]))
        # Observed yield quantiles characterize errors; they are not candidate selection inputs.
        frame["actual_yield_quartile"] = pd.qcut(frame.actual, 4, labels=["Q1", "Q2", "Q3", "Q4"])
        for dimension in ("state", "fold", "actual_yield_quartile"):
            for value, sub in frame.groupby(dimension, observed=True):
                slices.append({"scheme": scheme, "dimension": dimension, "value": str(value),
                               **numbers(sub.actual, sub.predicted)})
        frame["signed_error_t_ha"] = frame.predicted - frame.actual
        frame["absolute_error_t_ha"] = abs(frame.signed_error_t_ha)
        frame["scheme"] = scheme
        errors.extend(frame.sort_values("absolute_error_t_ha", ascending=False).head(15).to_dict(orient="records"))
        validation[scheme] = {"model": model, "baseline": baseline,
                              "relative_mae_reduction_vs_own_baseline": 1 - model["mae"] / baseline["mae"],
                              "relative_rmse_reduction_vs_own_baseline": 1 - model["rmse"] / baseline["rmse"],
                              "interval_coverage_bounded_rows_only": coverage, "bounded_interval_n": int(bounded.sum()),
                              "unbounded_interval_n": int((~bounded).sum()), "mean_bounded_interval_width_t_ha": width,
                              "fixed_oof_parcel_bootstrap_95": bootstrap_intervals(frame.actual, frame.predicted),
                              "fold_sizes": {str(k): int(v) for k, v in frame.groupby("fold").size().items()}}
        if scheme == "spatial":
            m = metadata.set_index("ID_POLIGONO").loc[frame.ID_parcela]
            blocks = (np.floor(m.x_m.to_numpy() / 20000).astype(int).astype(str).astype(object) + "_" +
                      np.floor(m.y_m.to_numpy() / 20000).astype(int).astype(str).astype(object))
            block_frame = pd.DataFrame({"block": blocks, "fold": frame.fold.to_numpy()})
            assert_check(checks, "spatial_outer_folds_do_not_share_20km_blocks",
                         block_frame.groupby("block").fold.nunique().max() == 1)
            validation[scheme]["spatial_blocks_n"] = int(block_frame.block.nunique())
            validation[scheme]["spatial_block_sizes"] = {str(k): int(v) for k, v in block_frame.groupby("block").size().items()}
        inputs.append(path)

    fit, calibration = set(reported["fit_ids"]), set(reported["calibration_ids"])
    assert_check(checks, "final_fit_calibration_disjoint_cover_138_labels", not (fit & calibration)
                 and fit | calibration == set(training.ID_POLIGONO) and not ((fit | calibration) & expected_ids))
    final_audit = {"fit_n": len(fit), "calibration_n": len(calibration), "selection": reported["selection"],
                   "selection_metric_note": "Current source select_model sorts by MAE, then RMSE; selection metrics are internal, not final test error.",
                   "calibration_metrics_status": "metrics.json reported; optionally independently recalculated below"}
    # The local joblib is a project-produced trusted artifact; never load unknown external pickle files.
    model_path = root / "platform/artifacts/model.joblib"
    if model_path.exists():
        import joblib
        saved = joblib.load(model_path)
        assert_check(checks, "frozen_model_fit_calibration_ids_match_report",
                     set(saved["fit_ids"]) == fit and set(saved["calibration_ids"]) == calibration)
        x_path = root / f"platform/artifacts/features-cloud-{saved['cloud_threshold']}.csv"
        x = pd.read_csv(x_path).set_index("ID_POLIGONO")[saved["columns"]]
        cal_ids = reported["calibration_ids"]
        cal_pred = np.maximum(saved["pipeline"].predict(x.loc[cal_ids]), 0)
        cal_metrics = numbers(train_lookup.loc[cal_ids], cal_pred)
        assert_check(checks, "frozen_model_reproduces_calibration_metrics",
                     all(np.isclose(cal_metrics[k], reported["calibration_point_metrics"][k], atol=1e-12, rtol=0)
                         for k in ("n", "mae", "rmse", "r2", "bias")))
        hidden_pred = np.maximum(saved["pipeline"].predict(x.loc[hidden.ID_POLIGONO]), 0)
        assert_check(checks, "frozen_model_reproduces_submission_within_four_decimal_rounding",
                     np.allclose(hidden_pred, merged.ours, rtol=0, atol=.000050001))
        final_audit["calibration_point_metrics_recomputed"] = cal_metrics
        final_audit["calibration_metrics_status"] = "recomputed_from_frozen_model_and_official_labels"
        inputs.extend([model_path, x_path])
    peers = reported_peer_metrics()
    pd.DataFrame(validation_metrics + peers).to_csv(out / "comparison-validation-metrics.csv", index=False, float_format="%.12g")
    pd.DataFrame(slices).to_csv(out / "comparison-validation-slices.csv", index=False, float_format="%.12g")
    pd.DataFrame(errors).to_csv(out / "comparison-largest-oof-errors.csv", index=False, float_format="%.12g")
    # Proposed common folds to request from all teammates. This does not reconstruct
    # either peer's original partitions or imply that their OOF scores used these folds.
    from sklearn.model_selection import KFold
    common_folds = []
    for split_seed in (20261013, 20261014):
        assigned = np.zeros(len(training), dtype=int)
        for outer_fold, (_, holdout) in enumerate(KFold(5, shuffle=True, random_state=split_seed).split(training), 1):
            assigned[holdout] = outer_fold
        common_folds.extend({"ID_POLIGONO": parcel_id, "seed": split_seed, "outer_fold": int(fold)}
                            for parcel_id, fold in zip(training.ID_POLIGONO, assigned))
    pd.DataFrame(common_folds).to_csv(out / "comparison-common-folds.csv", index=False)
    assert_check(checks, "proposed_common_folds_276_rows_two_complete_138_parcel_assignments",
                 len(common_folds) == 276 and all(
                     len({r["ID_POLIGONO"] for r in common_folds if r["seed"] == seed}) == 138
                     for seed in (20261013, 20261014)))
    for path in (root / "comparisons/agrocebada_hidden.md", root / "comparisons/Predicciones-agroceba.md",
                 root / "platform/pipeline/train.py", Path(__file__).resolve()):
        inputs.append(path)
    summary = {"seed": SEED, "bootstrap_resamples": BOOTSTRAPS, "checks": checks, "input_audits": audits,
               "pairwise_prediction_agreement_not_accuracy": pairwise,
               "largest_disagreements": merged.sort_values("prediction_range_t_ha", ascending=False).head(10).to_dict(orient="records"),
               "validation_recomputed": validation, "final_model_audit": final_audit,
               "proposed_common_folds": {"path": "comparison-common-folds.csv", "seeds": [20261013, 20261014],
                                         "algorithm": "sklearn.model_selection.KFold(n_splits=5, shuffle=True, random_state=seed)",
                                         "row_order": "Official master CSV order restricted to ENTRENAMIENTO",
                                         "purpose": "Shared future validation; peer original folds are unknown",
                                         "primary_metric": "MAE (current project selection criterion, not asserted official)",
                                         "guardrail_metric": "RMSE; also report R2 and bias"},
               "peer_metrics_reported_only": peers,
               "critical_limitations": [
                   "The 59 official prediction parcels have no observed yield; their MAE/RMSE/R2 cannot be computed.",
                   "Pairwise differences and correlations quantify agreement, never accuracy or ensemble weights.",
                   "Peer OOF predictions, fitted code and fold assignments are absent; their Markdown metrics cannot be independently reproduced.",
                   "Different folds, training sizes, seeds, scoring criteria, spatial grouping and repeat aggregation prevent a fair cross-project ranking.",
                   "Bootstrap intervals resample fixed OOF parcel residuals; they omit refitting/model-search uncertainty and ignore spatial dependence.",
                   "Conditional coverage on finite spatial intervals must keep its denominator; unbounded rows cannot be silently omitted in an overall guarantee.",
               ], "sources": [fingerprint(path, root) for path in inputs]}
    (out / "comparison-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"checks_passed": len(checks), "pairwise": pairwise,
                      "validation": {key: val["model"] for key, val in validation.items()},
                      "largest_disagreements": summary["largest_disagreements"][:5]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "platform/artifacts")
    args = parser.parse_args()
    run(args.root.resolve(), args.output_dir.resolve())
