# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .constants import OUTLIER_COLOR


def detect_outliers(all_eurs: dict, iqr_factor: float = 1.5) -> pd.DataFrame:
    rows = []
    for w, eurs in all_eurs.items():
        rows.append(
            {
                "Well": w,
                "Oil EUR": eurs.get("Oil", np.nan),
                "Gas EUR": eurs.get("Gas", np.nan),
                "Water EUR": eurs.get("Water", np.nan),
            }
        )
    df = pd.DataFrame(rows).set_index("Well")

    oil = df["Oil EUR"].dropna()
    q1, q3 = np.percentile(oil, 25), np.percentile(oil, 75)
    iqr = q3 - q1
    lo, hi = q1 - iqr_factor * iqr, q3 + iqr_factor * iqr

    reasons, outlier = [], []
    for w in df.index:
        v = df.loc[w, "Oil EUR"]
        if np.isnan(v):
            reasons.append("No fit")
            outlier.append(False)
        elif v < lo:
            reasons.append(f"Oil EUR below Q1 − {iqr_factor}×IQR ({lo:,.0f})")
            outlier.append(True)
        elif v > hi:
            reasons.append(f"Oil EUR above Q3 + {iqr_factor}×IQR ({hi:,.0f})")
            outlier.append(True)
        else:
            reasons.append("")
            outlier.append(False)

    df["Outlier"] = outlier
    df["Reason"] = reasons
    df["IQR Lo"] = lo
    df["IQR Hi"] = hi
    df["Oil EUR Rank"] = df["Oil EUR"].rank(ascending=False, method="first")
    return df


def outlier_scatter(outlier_df: pd.DataFrame, excluded: list[str]) -> go.Figure:
    df = outlier_df.reset_index()
    df = df.sort_values("Oil EUR", ascending=False).reset_index(drop=True)
    df["Rank"] = np.arange(1, len(df) + 1)

    fig = go.Figure()
    for label, color, symbol, mask in [
        ("Normal", "#2ECC71", "circle", (~df["Outlier"]) & (~df["Well"].isin(excluded))),
        ("Outlier", OUTLIER_COLOR, "diamond", (df["Outlier"]) & (~df["Well"].isin(excluded))),
        ("Excluded", "#888888", "x", (df["Well"].isin(excluded))),
    ]:
        dsub = df[mask]
        fig.add_trace(
            go.Scatter(
                x=dsub["Rank"],
                y=dsub["Oil EUR"],
                mode="markers",
                name=label,
                marker=dict(color=color, size=8, symbol=symbol, opacity=0.9),
                hovertemplate="Well=%{text}<br>Oil EUR=%{y:,.0f}<extra></extra>",
                text=dsub["Well"],
            )
        )

    lo = float(outlier_df["IQR Lo"].iloc[0])
    hi = float(outlier_df["IQR Hi"].iloc[0])
    for y, lbl, dash in [(lo, "IQR Lo", "dot"), (hi, "IQR Hi", "dot")]:
        fig.add_hline(
            y=y,
            line=dict(color=OUTLIER_COLOR, dash=dash, width=1.5),
            annotation_text=lbl,
            annotation_position="right",
        )

    fig.update_layout(
        title=dict(text="<b>Oil EUR — Outlier Detection (IQR Method)</b>", x=0.5),
        xaxis_title="Well Rank (by Oil EUR)",
        yaxis_title="Oil EUR (BBL)",
        height=420,
        template="plotly_dark",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#161b22",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=80, b=60, l=70, r=90),
    )
    return fig

