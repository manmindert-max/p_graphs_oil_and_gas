# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .arps import eval_arps, fit_arps
from .constants import FLUIDS, FLUID_COLORS, FLUID_UNITS, FLUID_VOL, P50_FIT_COLOR


def build_p50_profile(all_fits: dict, forecast_extension_months: int) -> dict:
    t_max = 0.0
    for wfits in all_fits.values():
        for fit in wfits.values():
            if not fit:
                continue
            t_max = max(t_max, float(fit.get("t_last", 0.0)) + float(forecast_extension_months))
    t_grid = np.arange(0, int(np.ceil(t_max)) + 1, dtype=float)

    result = {}
    for fluid in FLUIDS:
        profiles = []
        for fits in all_fits.values():
            fit = fits.get(fluid)
            if not fit:
                continue
            q = np.maximum(eval_arps(t_grid, fit["qi"], fit["Di"], fit["b"]), 0)
            t_end = float(fit.get("t_last", 0.0)) + float(forecast_extension_months)
            q[t_grid > t_end] = 0
            profiles.append(q)

        if not profiles:
            result[fluid] = {
                "t": t_grid,
                "p10": np.zeros_like(t_grid),
                "p50": np.zeros_like(t_grid),
                "p90": np.zeros_like(t_grid),
            }
            continue

        mat = np.array(profiles)
        result[fluid] = {
            "t": t_grid,
            "p10": np.percentile(mat, 90, axis=0),
            "p50": np.percentile(mat, 50, axis=0),
            "p90": np.percentile(mat, 10, axis=0),
            "n": mat.shape[0],
        }
    return result


def fit_p50_curve(profiles: dict, q_min: float) -> dict:
    fits = {}
    for fluid, data in profiles.items():
        t = data["t"]
        q = data["p50"]
        mask = q > q_min
        t_f, q_f = t[mask], q[mask]
        if len(t_f) < 3:
            fits[fluid] = None
            continue
        fit = fit_arps(t_f, q_f, mode="hyperbolic")
        if fit:
            t_int = data["t"]
            q_int = np.maximum(eval_arps(t_int, fit["qi"], fit["Di"], fit["b"]), 0)
            q_int[q_int < q_min] = 0
            fit["eur"] = float(np.trapezoid(q_int, t_int))
        fits[fluid] = fit
    return fits


def p50_type_curve_figure(profiles: dict, p50_fits: dict, q_min: float):
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=["Oil Rate (BPD)", "Gas Rate (MCFD)", "Water Rate (BPD)"],
        horizontal_spacing=0.07,
    )

    params_rows = []
    for col_i, fluid in enumerate(FLUIDS, 1):
        data = profiles[fluid]
        t, p10, p50, p90 = data["t"], data["p10"], data["p50"], data["p90"]
        color = FLUID_COLORS[fluid]

        fig.add_trace(
            go.Scatter(
                x=np.concatenate([t, t[::-1]]),
                y=np.concatenate([p10, p90[::-1]]),
                fill="toself",
                fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{fluid} P10–P90 band",
                showlegend=(col_i == 1),
            ),
            row=1,
            col=col_i,
        )

        for ydata, lbl, dash in [(p10, "P10", "dashdot"), (p90, "P90", "dot")]:
            fig.add_trace(
                go.Scatter(
                    x=t,
                    y=ydata,
                    mode="lines",
                    name=f"{fluid} {lbl}",
                    line=dict(color=color, dash=dash, width=1.5),
                    showlegend=(col_i == 1),
                ),
                row=1,
                col=col_i,
            )

        fig.add_trace(
            go.Scatter(
                x=t,
                y=p50,
                mode="lines",
                name=f"{fluid} P50",
                line=dict(color=color, width=2.5),
                showlegend=(col_i == 1),
            ),
            row=1,
            col=col_i,
        )

        fit = p50_fits.get(fluid)
        if fit:
            t_fit = np.linspace(float(t[0]), float(t[-1]), 400)
            q_fit = eval_arps(t_fit, fit["qi"], fit["Di"], fit["b"])
            fig.add_trace(
                go.Scatter(
                    x=t_fit,
                    y=q_fit,
                    mode="lines",
                    name=f"{fluid} Arps fit",
                    line=dict(color=P50_FIT_COLOR, width=2.5, dash="dash"),
                    showlegend=(col_i == 1),
                ),
                row=1,
                col=col_i,
            )
            params_rows.append(
                {
                    "Fluid": fluid,
                    "qi (rate/day)": f"{fit['qi']:.2f}",
                    "Di (1/mo)": f"{fit['Di']:.5f}",
                    "b": f"{fit['b']:.3f}",
                    "R²": f"{fit['r2']:.3f}",
                    "Decline": fit["label"],
                    f"EUR ({FLUID_VOL[fluid]})": f"{fit.get('eur', 0):,.0f}",
                }
            )

        fig.update_yaxes(type="log", row=1, col=col_i, title_text=FLUID_UNITS[fluid])
        fig.update_xaxes(title_text="Producing Month", row=1, col=col_i)

    fig.update_layout(
        title=dict(text="<b>P50 Type Curve — Hyperbolic Arps Fit</b>", x=0.5),
        height=460,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=80, b=60, l=65, r=20),
    )
    return fig, pd.DataFrame(params_rows)

