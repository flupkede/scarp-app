#!/usr/bin/env python3
"""Scarp Glacier — Visualize ITS_LIVE velocity data.

Produces:
  1. Velocity time series plots for key glaciers (Tracy Arm, Barry Arm)
  2. Map of velocity summary across all sampled points
  3. Velocity trend map (accelerating vs decelerating glaciers)

Usage:
    cd C:/WorkArea/AI/scarp
    uv run --project glacier python glacier/20_visualize.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import (
    DATA_PROCESSED,
    GLACIER_POINTS_OF_INTEREST,
    VELOCITY_SUMMARY_FILE,
    VELOCITY_TIMESERIES_FILE,
)

# ---------------------------------------------------------------------------
# Output directory for plots
# ---------------------------------------------------------------------------
PLOTS_DIR = DATA_PROCESSED / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Plot style
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.fontsize": 8,
        "figure.facecolor": "white",
    }
)


def load_data() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """Load extracted velocity data."""
    ts_path = DATA_PROCESSED / VELOCITY_TIMESERIES_FILE
    summary_path = DATA_PROCESSED / VELOCITY_SUMMARY_FILE

    if not ts_path.exists():
        print(f"Error: {ts_path} not found. Run 10_extract.py first.")
        sys.exit(1)

    ts = pd.read_parquet(ts_path)
    ts["mid_date"] = pd.to_datetime(ts["mid_date"])

    summary = gpd.read_file(summary_path) if summary_path.exists() else gpd.GeoDataFrame()

    print(f"Loaded {len(ts)} observations, {ts['point_id'].nunique()} points")
    return ts, summary


def plot_timeseries(ts: pd.DataFrame) -> None:
    """Plot velocity time series for named glaciers of interest."""
    labels = [label for _, _, label in GLACIER_POINTS_OF_INTEREST]
    named = ts[ts["point_id"].isin(labels)]

    if named.empty:
        print("  No named glacier data to plot")
        return

    # Pick top-6 by observation count for readability
    top_glaciers = named.groupby("point_id")["v"].count().nlargest(6).index
    plot_data = named[named["point_id"].isin(top_glaciers)]

    fig, axes = plt.subplots(len(top_glaciers), 1, figsize=(14, 3 * len(top_glaciers)), sharex=True)
    if len(top_glaciers) == 1:
        axes = [axes]

    colors = plt.cm.Set2(np.linspace(0, 1, len(top_glaciers)))

    for ax, (glacier, group), color in zip(axes, plot_data.groupby("point_id"), colors):
        group = group.sort_values("mid_date")

        # Resample to monthly means for cleaner plot
        monthly = (
            group.set_index("mid_date")
            .resample("MS")["v"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )

        ax.fill_between(
            monthly["mid_date"],
            monthly["mean"] - monthly["std"],
            monthly["mean"] + monthly["std"],
            alpha=0.2,
            color=color,
        )
        ax.plot(monthly["mid_date"], monthly["mean"], color=color, linewidth=1)

        # Mark Tracy Arm tsunami event (2024)
        if glacier == "Tracy Arm":
            ax.axvline(pd.Timestamp("2024-01"), color="red", linestyle="--", alpha=0.5)
            ax.text(
                pd.Timestamp("2024-01"),
                ax.get_ylim()[1] * 0.9,
                " 2024 tsunami",
                color="red",
                fontsize=8,
            )

        ax.set_ylabel("v (m/yr)")
        ax.set_title(
            f"{glacier}  (n={len(group)}, v_mean={group['v'].mean():.1f} m/yr)"
        )
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Date")
    fig.suptitle("ITS_LIVE Glacier Velocity Time Series — SE Alaska", fontsize=14, y=1.01)
    fig.tight_layout()

    path = PLOTS_DIR / "velocity_timeseries.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def plot_velocity_map(summary: gpd.GeoDataFrame) -> None:
    """Map of mean velocity across all sampled points."""
    if summary.empty:
        print("  No summary data to map")
        return

    fig, ax = plt.subplots(figsize=(12, 10))

    # Plot points colored by mean velocity
    vmin = summary["v_mean"].quantile(0.05)
    vmax = summary["v_mean"].quantile(0.95)

    scatter = ax.scatter(
        summary.geometry.x,
        summary.geometry.y,
        c=summary["v_mean"],
        s=summary["obs_count"] / summary["obs_count"].max() * 200 + 20,
        cmap="YlOrRd",
        vmin=vmin,
        vmax=vmax,
        alpha=0.8,
        edgecolors="black",
        linewidths=0.5,
    )

    # Label named glaciers
    labels = {label for _, _, label in GLACIER_POINTS_OF_INTEREST}
    for _, row in summary.iterrows():
        if row["point_id"] in labels:
            ax.annotate(
                row["point_id"],
                (row.geometry.x, row.geometry.y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                fontweight="bold",
            )

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, label="Mean velocity (m/yr)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("ITS_LIVE Mean Glacier Velocity — SE Alaska")
    ax.grid(True, alpha=0.2)

    path = PLOTS_DIR / "velocity_map.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_trend_map(summary: gpd.GeoDataFrame) -> None:
    """Map of velocity trends (accelerating vs decelerating)."""
    if summary.empty:
        print("  No summary data for trend map")
        return

    fig, ax = plt.subplots(figsize=(12, 10))

    # Color by trend: red = accelerating, blue = decelerating
    trend = summary["v_trend_m_yr_per_year"]
    # Clamp extremes for visualization
    vmax = trend.abs().quantile(0.9)

    scatter = ax.scatter(
        summary.geometry.x,
        summary.geometry.y,
        c=trend,
        cmap="RdBu_r",  # red=positive, blue=negative
        vmin=-vmax,
        vmax=vmax,
        s=80,
        alpha=0.8,
        edgecolors="black",
        linewidths=0.5,
    )

    # Label significant trends
    for _, row in summary.iterrows():
        t = row["v_trend_m_yr_per_year"]
        if abs(t) > vmax * 0.5:
            labels = {label for _, _, label in GLACIER_POINTS_OF_INTEREST}
            label = row["point_id"] if row["point_id"] in labels else ""
            if label:
                ax.annotate(
                    f"{label}\n({t:+.0f})",
                    (row.geometry.x, row.geometry.y),
                    textcoords="offset points",
                    xytext=(5, 5),
                    fontsize=7,
                )

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, label="Velocity trend (m/yr per year)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("ITS_LIVE Velocity Trend — Red=Accelerating, Blue=Decelerating")
    ax.grid(True, alpha=0.2)

    path = PLOTS_DIR / "velocity_trend_map.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_sawtooth(ts: pd.DataFrame) -> None:
    """Plot sawtooth velocity patterns for glaciers showing episodic behavior.

    Focuses on Tracy Arm (2024 tsunami case study) and Brady Glacier
    (fastest point, known surge behavior).
    """
    targets = ["Tracy Arm", "Brady Glacier"]
    target_data = ts[ts["point_id"].isin(targets)]

    if target_data.empty:
        print("  No target glacier data for sawtooth plot")
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    for ax, glacier in zip(axes, targets):
        group = target_data[target_data["point_id"] == glacier].sort_values("mid_date")

        if group.empty:
            ax.text(0.5, 0.5, f"No data for {glacier}", transform=ax.transAxes, ha="center")
            continue

        # Monthly resampling
        monthly = (
            group.set_index("mid_date")
            .resample("MS")["v"]
            .agg(["mean", "std"])
            .reset_index()
            .dropna()
        )

        ax.plot(monthly["mid_date"], monthly["mean"], color="darkred", linewidth=1)
        ax.fill_between(
            monthly["mid_date"],
            monthly["mean"] - monthly["std"],
            monthly["mean"] + monthly["std"],
            alpha=0.15,
            color="darkred",
        )

        # Highlight velocity spikes (potential surge/retreat events)
        v_threshold = monthly["mean"].mean() + 2 * monthly["mean"].std()
        spikes = monthly[monthly["mean"] > v_threshold]
        if not spikes.empty:
            ax.scatter(spikes["mid_date"], spikes["mean"], color="red", s=30, zorder=5, label="Velocity spike")

        ax.set_ylabel("v (m/yr)")
        ax.set_title(f"{glacier} — Velocity Pattern")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    axes[-1].set_xlabel("Date")
    axes[0].set_xlabel("Date")
    fig.suptitle(
        "Sawtooth Velocity Patterns — Episodic Glacier Behavior",
        fontsize=13,
    )
    fig.tight_layout()

    path = PLOTS_DIR / "sawtooth_patterns.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def main() -> None:
    print("=" * 60)
    print("Scarp Glacier — Velocity Visualization")
    print("=" * 60)
    print()

    ts, summary = load_data()

    print("\nGenerating plots ...")
    print("  1. Velocity time series for named glaciers")
    plot_timeseries(ts)

    print("  2. Mean velocity map")
    plot_velocity_map(summary)

    print("  3. Velocity trend map")
    plot_trend_map(summary)

    print("  4. Sawtooth velocity patterns")
    plot_sawtooth(ts)

    print("\nDone. All plots saved to glacier/data/processed/plots/")


if __name__ == "__main__":
    main()
