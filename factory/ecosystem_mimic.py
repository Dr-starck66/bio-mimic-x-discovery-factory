#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from statistics import mean, pstdev

SCHEMA = "biomimic-ecosystem-mimic-v1"


def _clean_taxa(taxa):
    out = {}
    for name, value in (taxa or {}).items():
        try:
            abundance = float(value)
        except (TypeError, ValueError):
            continue
        if abundance > 0:
            out[str(name)] = abundance
    return out


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def shannon_diversity(taxa):
    values = list(_clean_taxa(taxa).values())
    total = sum(values)
    if total <= 0:
        return 0.0
    return -sum((value / total) * math.log(value / total) for value in values)


def pielou_evenness(taxa):
    richness = len(_clean_taxa(taxa))
    if richness == 0:
        return 0.0
    if richness == 1:
        return 1.0
    return shannon_diversity(taxa) / math.log(richness)


def bray_curtis(a, b):
    aa, bb = _clean_taxa(a), _clean_taxa(b)
    names = set(aa) | set(bb)
    denominator = sum(aa.get(name, 0.0) + bb.get(name, 0.0) for name in names)
    if denominator <= 0:
        return 0.0
    numerator = sum(abs(aa.get(name, 0.0) - bb.get(name, 0.0)) for name in names)
    return numerator / denominator


def _slope(values):
    if len(values) < 2:
        return None
    x_bar = (len(values) - 1) / 2
    y_bar = mean(values)
    denominator = sum((i - x_bar) ** 2 for i in range(len(values)))
    if denominator == 0:
        return None
    return sum((i - x_bar) * (y - y_bar) for i, y in enumerate(values)) / denominator


def _pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 4:
        return None
    mx, my = mean(xs), mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denominator = math.sqrt(sum(x * x for x in dx) * sum(y * y for y in dy))
    if denominator == 0:
        return None
    return sum(x * y for x, y in zip(dx, dy)) / denominator


def _normalize_observations(document):
    normalized, rejected = [], []
    for index, raw in enumerate(document.get("observations", [])):
        if not isinstance(raw, dict):
            rejected.append({"index": index, "reason": "observation_not_object"})
            continue
        taxa = _clean_taxa(raw.get("taxa", {}))
        if not taxa:
            rejected.append({"index": index, "reason": "no_positive_taxa_abundance"})
            continue
        normalized.append(
            {
                "time": str(raw.get("time") or f"step-{index:04d}"),
                "_time": _parse_time(raw.get("time")),
                "_index": index,
                "taxa": taxa,
                "environment": raw.get("environment", {}) if isinstance(raw.get("environment", {}), dict) else {},
                "perturbation": raw.get("perturbation"),
            }
        )
    normalized.sort(key=lambda x: (x["_time"] is None, x["_time"] or datetime.max, x["_index"]))
    return normalized, rejected


def _cofluctuation_network(observations, threshold=0.60):
    taxa = sorted({name for obs in observations for name in obs["taxa"]})
    edges = []
    for i, left in enumerate(taxa):
        xs = [obs["taxa"].get(left, 0.0) for obs in observations]
        for right in taxa[i + 1 :]:
            ys = [obs["taxa"].get(right, 0.0) for obs in observations]
            r = _pearson(xs, ys)
            if r is not None and abs(r) >= threshold:
                edges.append(
                    {
                        "source": left,
                        "target": right,
                        "pearson_r": round(r, 6),
                        "direction": "cofluctuate" if r > 0 else "counterfluctuate",
                        "semantics": "COFLUCTUATION_ONLY_INTERACTION_NOT_INFERRED",
                    }
                )
    return {
        "threshold_abs_r": threshold,
        "minimum_timepoints": 4,
        "semantics": "Heuristic cofluctuation network; correlation is not evidence of ecological interaction or causality.",
        "edges": edges,
    }


def _perturbation_responses(observations, totals, baseline_window=3, recovery_tolerance=0.20):
    out = []
    for i, obs in enumerate(observations):
        if not obs.get("perturbation"):
            continue
        prior = totals[max(0, i - baseline_window) : i]
        if len(prior) < 2:
            out.append(
                {
                    "time": obs["time"],
                    "perturbation": obs["perturbation"],
                    "status": "INSUFFICIENT_PRE_EVENT_BASELINE",
                }
            )
            continue
        baseline = mean(prior)
        scale = max(abs(baseline), 1e-12)
        event_deviation = abs(totals[i] - baseline) / scale
        resistance = max(0.0, 1.0 - event_deviation)
        recovered_index = None
        for j in range(i + 1, len(observations)):
            if abs(totals[j] - baseline) / scale <= recovery_tolerance:
                recovered_index = j
                break
        record = {
            "time": obs["time"],
            "perturbation": obs["perturbation"],
            "baseline_total_abundance": round(baseline, 6),
            "event_total_abundance": round(totals[i], 6),
            "resistance_complement": round(resistance, 6),
            "recovery_tolerance_fraction": recovery_tolerance,
            "metric_semantics": "Descriptive complement-of-deviation metric; not a probability.",
        }
        if recovered_index is None:
            record.update(
                {
                    "status": "RECOVERY_NOT_OBSERVED_WITHIN_WINDOW",
                    "recovery_lag_steps": None,
                    "recovery_lag_days": None,
                }
            )
        else:
            days = None
            t0, t1 = obs["_time"], observations[recovered_index]["_time"]
            if t0 is not None and t1 is not None:
                days = (t1 - t0).total_seconds() / 86400
            record.update(
                {
                    "status": "RECOVERED_WITHIN_TOLERANCE",
                    "recovery_lag_steps": recovered_index - i,
                    "recovery_lag_days": None if days is None else round(days, 6),
                }
            )
        out.append(record)
    return out


def _hypotheses(points, network, perturbations):
    hypotheses = []
    mean_turnover = mean([p["turnover_from_previous"] for p in points[1:]]) if len(points) > 1 else 0.0
    richness_change = points[-1]["richness"] - points[0]["richness"] if len(points) > 1 else 0
    if len(points) >= 3 and mean_turnover >= 0.20 and richness_change != 0:
        hypotheses.append(
            {
                "id": "ECO-H1-SUCCESSION",
                "status": "HYPOTHESIS",
                "statement": "Community composition is undergoing directional succession rather than remaining compositionally static.",
                "prediction": "Additional observations should preserve a directional richness/composition trend beyond short-term sampling noise.",
                "falsifier": "The apparent trend disappears with denser sampling or reverses without an identified disturbance.",
            }
        )
    recovered = [p for p in perturbations if p.get("status") == "RECOVERED_WITHIN_TOLERANCE"]
    if recovered:
        hypotheses.append(
            {
                "id": "ECO-H2-RECOVERY",
                "status": "HYPOTHESIS",
                "statement": "The observed community may possess recovery dynamics after the recorded perturbation.",
                "prediction": "Independent perturbation episodes should show repeatable return toward a pre-event reference range.",
                "falsifier": "Independent events fail to recover or the reference range is not stable before perturbation.",
            }
        )
    if network["edges"]:
        hypotheses.append(
            {
                "id": "ECO-H3-COFLUCTUATION",
                "status": "HYPOTHESIS",
                "statement": "Some taxa share repeatable temporal covariance that may reflect shared drivers or ecological coupling.",
                "prediction": "Covariance should persist after controlling for measured environmental drivers and sampling effort.",
                "falsifier": "Associations vanish after environmental/sampling controls or fail in an independent time window.",
            }
        )
    return hypotheses


def analyze_ecosystem(document):
    if not isinstance(document, dict):
        raise TypeError("document must be a dict")
    observations, rejected = _normalize_observations(document)
    ecosystem_id = str(document.get("ecosystem_id") or "unidentified")
    points, totals = [], []
    previous = None
    for obs in observations:
        taxa = obs["taxa"]
        total = sum(taxa.values())
        totals.append(total)
        colonizations, losses, turnover = [], [], None
        if previous is not None:
            before, after = set(previous["taxa"]), set(taxa)
            colonizations = sorted(after - before)
            losses = sorted(before - after)
            turnover = bray_curtis(previous["taxa"], taxa)
        points.append(
            {
                "time": obs["time"],
                "richness": len(taxa),
                "total_abundance": round(total, 6),
                "shannon_diversity": round(shannon_diversity(taxa), 6),
                "pielou_evenness": round(pielou_evenness(taxa), 6),
                "colonizations": colonizations,
                "local_losses": losses,
                "turnover_from_previous": None if turnover is None else round(turnover, 6),
                "perturbation": obs.get("perturbation"),
            }
        )
        previous = obs

    valid_turnovers = [p["turnover_from_previous"] for p in points if p["turnover_from_previous"] is not None]
    temporal_stability = None
    if len(totals) >= 3 and mean(totals) > 0:
        sd = pstdev(totals)
        temporal_stability = None if sd == 0 else mean(totals) / sd

    network = _cofluctuation_network(observations)
    perturbations = _perturbation_responses(observations, totals)
    metrics = {
        "latest_richness": points[-1]["richness"] if points else 0,
        "richness_trend_per_observation": None if len(points) < 2 else round(_slope([p["richness"] for p in points]), 6),
        "mean_bray_curtis_turnover": None if not valid_turnovers else round(mean(valid_turnovers), 6),
        "temporal_stability_inverse_cv_total_abundance": None if temporal_stability is None else round(temporal_stability, 6),
        "colonization_events": sum(len(p["colonizations"]) for p in points),
        "local_loss_events": sum(len(p["local_losses"]) for p in points),
    }
    result = {
        "schema": SCHEMA,
        "ecosystem_id": ecosystem_id,
        "status": "ANALYZED" if len(observations) >= 2 else "INSUFFICIENT_DATA",
        "epistemic_status": "OBSERVATIONAL_ANALYSIS",
        "observation_count": len(observations),
        "rejected_observations": rejected,
        "metrics": metrics,
        "time_series": points,
        "cofluctuation_network": network,
        "perturbation_responses": perturbations,
        "hypotheses": _hypotheses(points, network, perturbations),
        "causal_inference": False,
        "interaction_inference": False,
        "claims_established_truth": False,
        "limitations": [
            "Observational time series cannot by itself establish causality.",
            "Cofluctuation edges are not species-interaction claims.",
            "Recovery metrics depend on sampling frequency, baseline choice, and perturbation labeling.",
            "Species richness and abundance metrics are sensitive to observation effort and detectability.",
        ],
    }
    result["sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()
    return result
