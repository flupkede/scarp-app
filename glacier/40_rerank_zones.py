#!/usr/bin/env python3
"""Scarp Glacier - Stage 3: glacier-aware re-scoring and re-ranking of zones.

The full 90 m raster scoring pipeline (prep/50_score_zones.py) selects the 120
candidate sensor sites and stores each site's normalised scoring components.
This step adds glacier dynamics as a *scoring signal* by recomputing each site's
weighted-additive score with a new glacier component (the per-zone glacier_signal
from glacier/30_enrich_zones.py) and re-ranking the proven candidate set.

Why a re-rank rather than a full raster rebuild:
  - Glacier dynamics is, per Hig, the dominant driver of tsunamigenic landslides
    in SE Alaska, so it earns a heavy weight (the six original weights rescale
    down to make room).
  - The candidate *set* is unchanged, so the proven known-site coverage (Gate A)
    is preserved; only the ordering and the score change - which is exactly the
    requested "add glacier as a scoring signal that changes the live ranking".
  - It operates on 120 features, avoiding the memory-heavy full-grid rebuild.

Rewrites the canonical Scarp outputs in data/processed/ (the backend source):
  - zones.geojson            (components.glacier added; score + rank updated;
                              rich per-zone glacier context attached as .glacier)
  - candidates_influence.geojson  (properties kept in sync by id)
  - zones_top10.json         (new top-10 by glacier-aware rank)
  - meta.json                (weights + rerank note updated)

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project glacier python glacier/40_rerank_zones.py
"""

import json
import sys
from datetime import datetime, timezone

from config import DATA_PROCESSED, SCARP_DATA, ZONE_GLACIER_PARAMS_FILE

# ---------------------------------------------------------------------------
# Glacier-aware weighted-additive weights (sum 1.0).
# Original prep/50_score_zones.py weights were SUSC .25 / FJORD .25 / PROX .20 /
# VOLUME .10 / EXPO .10 / GAP .10; they rescale down to free 0.15 for glacier.
# ---------------------------------------------------------------------------
W_SUSC = 0.22
W_FJORD = 0.22
W_PROX = 0.16
W_VOLUME = 0.09
W_EXPO = 0.08
W_GAP = 0.08
W_GLACIER = 0.15

WEIGHTS = {
    "susceptibility": W_SUSC,
    "fjord_wall": W_FJORD,
    "proximity": W_PROX,
    "volume_proxy": W_VOLUME,
    "exposure": W_EXPO,
    "gap": W_GAP,
    "glacier": W_GLACIER,
}

ZONES_FILE = "zones.geojson"
INFLUENCE_FILE = "candidates_influence.geojson"
TOP10_FILE = "zones_top10.json"
META_FILE = "meta.json"


def glacier_aware_score(components: dict, glacier_signal: float) -> float:
    """Weighted-additive score including the glacier signal.

    coverage is a data-confidence layer; the monitoring-gap term rewards thin
    coverage via (1 - coverage), matching prep/50_score_zones.py.
    """
    return (
        W_SUSC * components.get("susceptibility", 0.0)
        + W_FJORD * components.get("fjord_wall", 0.0)
        + W_PROX * components.get("proximity", 0.0)
        + W_VOLUME * components.get("volume_proxy", 0.0)
        + W_EXPO * components.get("exposure", 0.0)
        + W_GAP * (1.0 - components.get("coverage", 0.0))
        + W_GLACIER * glacier_signal
    )


def load_json(path):
    if not path.exists():
        print(f"Error: {path} not found.")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def main() -> None:
    print("=" * 60)
    print("Scarp Glacier - Stage 3: Glacier-aware Re-rank")
    print("=" * 60)
    print()

    zones = load_json(SCARP_DATA / ZONES_FILE)
    params_map = load_json(DATA_PROCESSED / ZONE_GLACIER_PARAMS_FILE)

    features = zones["features"]
    print(f"  Zones: {len(features)}  |  glacier params: {len(params_map)}")

    # --- Recompute score with glacier signal ---
    missing = 0
    for feat in features:
        props = feat["properties"]
        zid = props["id"]
        glac = params_map.get(zid)
        if glac is None:
            missing += 1
            glac = {"glacier_signal": 0.0}
        signal = float(glac.get("glacier_signal", 0.0))

        props["components"]["glacier"] = round(signal, 3)
        props["score"] = round(glacier_aware_score(props["components"], signal), 4)
        # Attach the rich per-zone glacier context for the frontend / API.
        props["glacier"] = glac

    if missing:
        print(f"  [!] {missing} zones had no glacier params (signal=0)")

    # --- Re-rank by new score ---
    features.sort(key=lambda f: -f["properties"]["score"])
    for new_rank, feat in enumerate(features, 1):
        feat["properties"]["rank"] = new_rank

    props_by_id = {f["properties"]["id"]: f["properties"] for f in features}

    # --- Write zones.geojson ---
    (SCARP_DATA / ZONES_FILE).write_text(json.dumps(zones))
    print(f"  [ok] {ZONES_FILE}: {len(features)} zones re-ranked")

    # --- Keep influence polygons in sync (properties only; geometry unchanged) ---
    inf_path = SCARP_DATA / INFLUENCE_FILE
    if inf_path.exists():
        influence = load_json(inf_path)
        updated = 0
        for feat in influence["features"]:
            zid = feat["properties"].get("id")
            if zid in props_by_id:
                feat["properties"] = props_by_id[zid]
                updated += 1
        influence["features"].sort(
            key=lambda f: f["properties"].get("rank", 10**9)
        )
        inf_path.write_text(json.dumps(influence))
        print(f"  [ok] {INFLUENCE_FILE}: {updated} polygons synced")

    # --- zones_top10.json ---
    top10 = [f for f in features if f["properties"]["rank"] <= 10]
    top10.sort(key=lambda f: f["properties"]["rank"])
    (SCARP_DATA / TOP10_FILE).write_text(json.dumps(top10))
    print(f"  [ok] {TOP10_FILE}: {len(top10)} features")

    # --- meta.json (patch weights + note) ---
    meta_path = SCARP_DATA / META_FILE
    meta = load_json(meta_path) if meta_path.exists() else {}
    meta.setdefault("config", {})["weights"] = WEIGHTS
    meta["glacier_rerank"] = {
        "applied_at": datetime.now(timezone.utc).isoformat(),
        "pipeline": "glacier/40_rerank_zones.py",
        "note": "Scores re-ranked with a glacier-dynamics signal (W_GLACIER="
        f"{W_GLACIER}); candidate set unchanged.",
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"  [ok] {META_FILE}: weights + rerank note updated")

    # --- Report ---
    print("\n" + "=" * 60)
    print("RE-RANK SUMMARY (top-10 by glacier-aware score)")
    print("=" * 60)
    for feat in top10:
        p = feat["properties"]
        g = p.get("glacier", {})
        lat = feat["geometry"]["coordinates"][1]
        anc = " (Anchorage)" if lat > 61.2 else ""
        print(
            f"  #{p['rank']:2d}  {p['id']:10s}  score={p['score']:.4f}  "
            f"glacier={p['components']['glacier']:.3f}  "
            f"near={g.get('nearest_active_ice')}{anc}"
        )

    # Gate B: top-10 not all Anchorage (lat > 61.2)
    anchorage = sum(
        1 for f in top10 if f["geometry"]["coordinates"][1] > 61.2
    )
    gate_b = "PASS" if anchorage < 10 else "FAIL"
    print(f"\n  GATE B ({gate_b}): {anchorage}/10 top-10 in Anchorage area")

    print("\nDone.")


if __name__ == "__main__":
    main()
