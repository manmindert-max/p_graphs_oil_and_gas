# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit


def arps_hyperbolic(t, qi, Di, b):
    b = np.clip(b, 1e-6, 2.0)
    return qi / (1.0 + b * Di * t) ** (1.0 / b)


def arps_exponential(t, qi, Di):
    return qi * np.exp(-Di * t)


def arps_harmonic(t, qi, Di):
    return qi / (1.0 + Di * t)


def eval_arps(t, qi, Di, b):
    if b < 1e-4:
        return arps_exponential(t, qi, Di)
    if abs(b - 1.0) < 1e-4:
        return arps_harmonic(t, qi, Di)
    return arps_hyperbolic(t, qi, Di, b)


def fit_arps(months, rates, mode: str = "hyperbolic"):
    """
    Fit an Arps decline curve to positive-rate points.

    Returns dict with:
      qi, Di, b, r2, label,
      t0 (index in original series),
      month0 (first positive TotalProdMonths),
      month_last (last positive TotalProdMonths),
      t_last (month_last - month0).
    """
    rates = np.asarray(rates, dtype=float)
    months = np.asarray(months, dtype=float)
    mask = (rates > 0) & np.isfinite(rates) & np.isfinite(months)
    t_abs = months[mask]
    q = rates[mask]
    if len(t_abs) < 3:
        return None

    t0_idx = int(mask.argmax())
    month0 = float(t_abs[0])
    month_last = float(t_abs[-1])
    t = t_abs - t_abs[0]
    t_last = float(t[-1])

    qi0 = float(q[0])
    Di0 = max(-np.log(max(q[-1], 1e-9) / qi0) / max(t[-1], 1), 0.005) if qi0 > 0 else 0.05

    try:
        if mode == "exponential":
            popt, _ = curve_fit(
                arps_exponential,
                t,
                q,
                p0=[qi0, Di0],
                bounds=([0, 1e-6], [qi0 * 5, 5.0]),
                maxfev=5000,
            )
            qi, Di, b = *popt, 0.0
            q_fit = arps_exponential(t, qi, Di)
            label = "Exponential"
        elif mode == "harmonic":
            popt, _ = curve_fit(
                arps_harmonic,
                t,
                q,
                p0=[qi0, Di0],
                bounds=([0, 1e-6], [qi0 * 5, 5.0]),
                maxfev=5000,
            )
            qi, Di, b = *popt, 1.0
            q_fit = arps_harmonic(t, qi, Di)
            label = "Harmonic"
        else:
            popt, _ = curve_fit(
                arps_hyperbolic,
                t,
                q,
                p0=[qi0, Di0, 0.8],
                bounds=([0, 1e-6, 0], [qi0 * 5, 5.0, 2.0]),
                maxfev=10000,
            )
            qi, Di, b = popt
            q_fit = arps_hyperbolic(t, qi, Di, b)
            label = "Hyperbolic"

        ss_res = float(np.sum((q - q_fit) ** 2))
        ss_tot = float(np.sum((q - q.mean()) ** 2))
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan

        return dict(
            qi=float(qi),
            Di=float(Di),
            b=float(b),
            r2=float(r2) if np.isfinite(r2) else np.nan,
            label=label,
            t0=t0_idx,
            month0=month0,
            month_last=month_last,
            t_last=t_last,
        )
    except Exception:
        return None


def calc_eur_tail(fit, cum_existing, forecast_extension_months: int = 360, q_min: float = 0.1) -> float:
    """
    EUR = cumulative actual + integral of fitted tail from t_last to t_last + extension,
    truncated below economic limit.
    """
    if fit is None:
        return np.nan
    t_start = float(fit.get("t_last", 0.0))
    t_end = t_start + float(forecast_extension_months)
    if t_end <= t_start:
        return float(cum_existing)
    t = np.arange(t_start, t_end + 1, dtype=float)
    q = np.maximum(eval_arps(t, fit["qi"], fit["Di"], fit["b"]), 0)
    q[q < q_min] = 0
    return float(cum_existing) + float(np.trapezoid(q, t))

