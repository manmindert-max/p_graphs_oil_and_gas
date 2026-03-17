# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .arps import calc_eur_tail, eval_arps, fit_arps
from .constants import (
    FIT_COLOR,
    FLUIDS,
    FLUID_COLORS,
    GAS_COLOR,
    OIL_COLOR,
    WATER_COLOR,
)


def semilog_well_figure(sub: pd.DataFrame, well_name: str, mode: str, forecast_extension_months: int, q_min: float):
    t = sub["TotalProdMonths"].values
    fluids = [
        ("Oil", "LiquidsProd_BBL", "OilRate_BPD", OIL_COLOR, "BBL", "BPD"),
        ("Gas", "GasProd_MCF", "GasRate_MCFD", GAS_COLOR, "MCF", "MCFD"),
        ("Water", "WaterProd_BBL", "WaterRate_BPD", WATER_COLOR, "BBL", "BPD"),
    ]

    fig = make_subplots(rows=1, cols=3, subplot_titles=[f"{f[0]} Production" for f in fluids], horizontal_spacing=0.07)
    params_rows = []

    for col_i, (fname, vol_col, rate_col, color, vol_unit, rate_unit) in enumerate(fluids, 1):
        y_arr = sub[rate_col].values
        fig.add_trace(
            go.Scatter(
                x=t,
                y=y_arr,
                mode="markers",
                name=fname,
                marker=dict(color=color, size=5, opacity=0.8),
                showlegend=(col_i == 1),
            ),
            row=1,
            col=col_i,
        )

        fit = fit_arps(t, y_arr, mode=mode)
        if fit:
            month0 = fit.get("month0", float(t[fit["t0"]]))
            t_last = float(fit.get("t_last", 0.0))

            t_plot = np.linspace(0, max(t_last, 1e-6), 300)
            q_plot = eval_arps(t_plot, fit["qi"], fit["Di"], fit["b"])
            fig.add_trace(
                go.Scatter(
                    x=t_plot + month0,
                    y=q_plot,
                    mode="lines",
                    name=f"{fname} fit",
                    line=dict(color=FIT_COLOR, width=2, dash="dash"),
                    showlegend=(col_i == 1),
                ),
                row=1,
                col=col_i,
            )

            if forecast_extension_months > 0:
                t_fc = np.linspace(t_last, t_last + forecast_extension_months, 200)
                q_fc = eval_arps(t_fc, fit["qi"], fit["Di"], fit["b"])
                fig.add_trace(
                    go.Scatter(
                        x=t_fc + month0,
                        y=q_fc,
                        mode="lines",
                        name=f"{fname} forecast",
                        line=dict(color=color, width=2, dash="dot"),
                        showlegend=(col_i == 1),
                    ),
                    row=1,
                    col=col_i,
                )

            cum = float(np.nansum(sub[vol_col].values))
            eur = calc_eur_tail(fit, cum, forecast_extension_months=forecast_extension_months, q_min=q_min)
            params_rows.append(
                {
                    "Fluid": fname,
                    "qi (rate/day)": f"{fit['qi']:.1f}",
                    "Di (1/mo)": f"{fit['Di']:.4f}",
                    "b": f"{fit['b']:.3f}",
                    "R²": f"{fit['r2']:.3f}",
                    "Decline Type": fit["label"],
                    "EUR": f"{eur:,.0f}",
                    "EUR Units": vol_unit,
                }
            )

        fig.update_yaxes(type="log", row=1, col=col_i, title_text=rate_unit)
        fig.update_xaxes(title_text="Producing Month", row=1, col=col_i)

    fig.update_layout(
        title=dict(text=f"<b>{well_name}</b> — Semi-log Production + Arps Fit", x=0.5),
        height=420,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=80, b=50, l=60, r=20),
    )
    return fig, pd.DataFrame(params_rows)


def percentile_analysis(all_eurs: dict, forecast_extension_months: int, all_fits: dict):
    # summary + P10/P90 ratios
    summary_rows = []
    p10p90_ratios = {}
    for fluid in FLUIDS:
        vals = np.array([v.get(fluid, np.nan) for v in all_eurs.values()], dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            continue
        p10v = np.percentile(vals, 90)
        p50v = np.percentile(vals, 50)
        p90v = np.percentile(vals, 10)
        ratio = p10v / p90v if p90v > 0 else np.nan
        p10p90_ratios[fluid] = ratio
        summary_rows.append(
            {
                "Fluid": fluid,
                "P10 (high)": f"{p10v:,.0f}",
                "P50 (median)": f"{p50v:,.0f}",
                "P90 (low)": f"{p90v:,.0f}",
                "Mean": f"{vals.mean():,.0f}",
                "P10 / P90": f"{ratio:.2f}" if np.isfinite(ratio) else "—",
                "Wells": len(vals),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    # box plot
    eur_fig = make_subplots(rows=1, cols=3, subplot_titles=["Oil EUR (BBL)", "Gas EUR (MCF)", "Water EUR (BBL)"])
    for col_i, fluid in enumerate(FLUIDS, 1):
        vals = np.array([v.get(fluid, np.nan) for v in all_eurs.values()], dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            continue
        color = FLUID_COLORS[fluid]
        eur_fig.add_trace(go.Box(y=vals, name=fluid, marker_color=color, boxmean="sd", showlegend=False), row=1, col=col_i)
        for pct, lbl, dash in [(10, "P90", "dot"), (50, "P50", "dash"), (90, "P10", "dashdot")]:
            eur_fig.add_hline(
                y=np.percentile(vals, pct),
                line=dict(color="white", dash=dash, width=1),
                annotation_text=lbl,
                annotation_position="right",
                row=1,
                col=col_i,
            )
    eur_fig.update_layout(
        title=dict(text="<b>EUR Distribution — P10 / P50 / P90</b>", x=0.5),
        height=420,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        margin=dict(t=80, b=50, l=60, r=90),
    )

    # common time grid for type curves
    t_max = 0.0
    for wfits in all_fits.values():
        for fit in wfits.values():
            if not fit:
                continue
            t_max = max(t_max, float(fit.get("t_last", 0.0)) + float(forecast_extension_months))
    t_common = np.arange(0, int(np.ceil(t_max)) + 1, dtype=float)

    tc_fig = make_subplots(rows=1, cols=3, subplot_titles=["Oil Rate (BPD)", "Gas Rate (MCFD)", "Water Rate (BPD)"])
    for col_i, fluid in enumerate(FLUIDS, 1):
        color = FLUID_COLORS[fluid]
        profiles = []
        for wfits in all_fits.values():
            fit = wfits.get(fluid)
            if not fit:
                continue
            q = np.maximum(eval_arps(t_common, fit["qi"], fit["Di"], fit["b"]), 0)
            t_end = float(fit.get("t_last", 0.0)) + float(forecast_extension_months)
            q[t_common > t_end] = 0
            profiles.append(q)
        if not profiles:
            continue
        mat = np.array(profiles)
        p10 = np.percentile(mat, 90, axis=0)
        p50 = np.percentile(mat, 50, axis=0)
        p90 = np.percentile(mat, 10, axis=0)

        tc_fig.add_trace(
            go.Scatter(
                x=np.concatenate([t_common, t_common[::-1]]),
                y=np.concatenate([p10, p90[::-1]]),
                fill="toself",
                fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                name=f"{fluid} P10–P90",
                showlegend=True,
            ),
            row=1,
            col=col_i,
        )

        for profile in mat:
            tc_fig.add_trace(
                go.Scatter(x=t_common, y=profile, mode="lines", line=dict(color=color, width=0.5), opacity=0.2, showlegend=False),
                row=1,
                col=col_i,
            )

        for ydata, lbl, dash, w in [(p10, "P10", "dashdot", 2.0), (p50, "P50", "solid", 2.5), (p90, "P90", "dot", 2.0)]:
            tc_fig.add_trace(
                go.Scatter(
                    x=t_common,
                    y=ydata,
                    mode="lines",
                    name=f"{fluid} {lbl}",
                    line=dict(color=color, dash=dash, width=w),
                    showlegend=(col_i == 1),
                ),
                row=1,
                col=col_i,
            )

        tc_fig.update_yaxes(type="log", row=1, col=col_i)
        tc_fig.update_xaxes(title_text="Producing Month", row=1, col=col_i)

    tc_fig.update_layout(
        title=dict(text="<b>Type Curve Envelope — Active Wells</b>", x=0.5),
        height=450,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=80, b=50, l=60, r=20),
    )

    return summary_df, eur_fig, tc_fig, p10p90_ratios


def p10p90_ratio_figure(all_eurs: dict) -> go.Figure:
    colors = [OIL_COLOR, GAS_COLOR, WATER_COLOR]
    ratios, labels = [], []
    for fluid in FLUIDS:
        vals = np.array([v.get(fluid, np.nan) for v in all_eurs.values()], dtype=float)
        vals = vals[np.isfinite(vals)]
        if len(vals) < 2:
            ratios.append(np.nan)
            labels.append(fluid)
            continue
        p10 = np.percentile(vals, 90)
        p90 = np.percentile(vals, 10)
        ratios.append(p10 / p90 if p90 > 0 else np.nan)
        labels.append(fluid)

    fig = go.Figure()
    for lbl, ratio, color in zip(labels, ratios, colors):
        fig.add_trace(
            go.Bar(
                x=[lbl],
                y=[ratio if np.isfinite(ratio) else 0],
                name=lbl,
                marker_color=color,
                text=[f"{ratio:.2f}x" if np.isfinite(ratio) else "N/A"],
                textposition="outside",
            )
        )
    fig.add_hline(y=1.0, line=dict(color="white", dash="dot", width=1), annotation_text="Ratio = 1", annotation_position="right")
    fig.update_layout(
        title=dict(text="<b>P10 / P90 EUR Ratio by Fluid</b>", x=0.5),
        yaxis_title="P10 / P90 Ratio",
        height=360,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        showlegend=False,
        margin=dict(t=80, b=60, l=60, r=90),
    )
    return fig


def cumulative_bar_chart(all_eurs: dict) -> go.Figure:
    wells = list(all_eurs.keys())
    oil_e = [all_eurs[w].get("Oil", 0) for w in wells]
    gas_e = [all_eurs[w].get("Gas", 0) / 6 for w in wells]
    water_e = [all_eurs[w].get("Water", 0) for w in wells]

    idx = np.argsort(oil_e)[::-1]
    wells = [wells[i] for i in idx]
    oil_e = [oil_e[i] for i in idx]
    gas_e = [gas_e[i] for i in idx]
    water_e = [water_e[i] for i in idx]

    fig = go.Figure()
    fig.add_bar(name="Oil EUR (BBL)", x=wells, y=oil_e, marker_color=OIL_COLOR)
    fig.add_bar(name="Gas EUR (BOE equiv)", x=wells, y=gas_e, marker_color=GAS_COLOR)
    fig.add_bar(name="Water EUR (BBL)", x=wells, y=water_e, marker_color=WATER_COLOR)
    fig.update_layout(
        barmode="group",
        title=dict(text="<b>EUR by Well (sorted by Oil EUR)</b>", x=0.5),
        xaxis_title="Well",
        yaxis_title="EUR",
        height=400,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=80, b=120, l=60, r=20),
        xaxis_tickangle=-45,
    )
    return fig

