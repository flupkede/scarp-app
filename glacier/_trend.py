"""Shared velocity-trend regression.

Single source of truth for the robust linear velocity trend, imported by both
10_extract.py and 15_explore.py. (10_extract's leading-digit filename blocks a
normal import, so the shared logic lives here in an importable module.)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import (
    MIN_TREND_OBSERVATIONS,
    MIN_TREND_SPAN_YEARS,
    SECONDS_PER_YEAR,
)


def linear_velocity_trend(dates: pd.Series, v_values: np.ndarray) -> float:
    """Linear velocity trend (m/yr per year) via least-squares regression.

    `dates` and `v_values` must be positionally aligned (same point, same order).
    Builds a clean aligned frame, drops NaT/NaN, sorts chronologically, and
    converts the time axis to fractional years via timedelta.total_seconds()
    (the pd.to_numeric path silently mis-scales datetime64 and collapses the
    x-range). Returns 0.0 when there is too little signal to trust a slope.
    """
    frame = pd.DataFrame(
        {"date": pd.to_datetime(pd.Series(dates).values, errors="coerce"), "v": v_values}
    ).dropna()
    if len(frame) < MIN_TREND_OBSERVATIONS:
        return 0.0

    frame = frame.sort_values("date")
    years = (frame["date"] - frame["date"].min()).dt.total_seconds() / SECONDS_PER_YEAR
    if float(years.max()) < MIN_TREND_SPAN_YEARS:
        return 0.0

    try:
        slope = np.polyfit(years.to_numpy(), frame["v"].to_numpy(), 1)[0]
    except (np.linalg.LinAlgError, ValueError):
        return 0.0
    return float(slope)
