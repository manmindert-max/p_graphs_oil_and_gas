# -*- coding: utf-8 -*-

import streamlit as st

from app.app_context import get_app_context
from app.plots import cumulative_bar_chart, p10p90_ratio_figure, percentile_analysis


st.set_page_config(page_title="P10/P50/P90 Analysis", page_icon="📊", layout="wide")

ctx = get_app_context()

st.markdown(f"## 📊 P10 / P50 / P90 Analysis — {len(ctx['active_wells'])} Active Wells")
st.caption("P10 = high case (90th percentile) · P90 = low case (10th percentile)")

with st.spinner("Computing percentiles…"):
    summary_df, eur_fig, tc_fig, ratios = percentile_analysis(
        ctx["all_eurs"],
        ctx["forecast_extension_months"],
        ctx["all_fits"],
    )

st.markdown("### P10 / P90 EUR Ratio")
r1, r2, r3 = st.columns(3)
for col, fluid in zip([r1, r2, r3], ["Oil", "Gas", "Water"]):
    ratio = ratios.get(fluid)
    col.metric(f"{fluid} P10/P90", f"{ratio:.2f}×" if ratio == ratio else "N/A")
st.plotly_chart(p10p90_ratio_figure(ctx["all_eurs"]), use_container_width=True)

st.markdown("### EUR Percentiles Summary")
st.dataframe(summary_df, use_container_width=True)

st.markdown("### EUR Distributions")
st.plotly_chart(eur_fig, use_container_width=True)

st.markdown("### Type Curve Envelope")
st.plotly_chart(tc_fig, use_container_width=True)

st.markdown("### EUR Ranking by Well")
st.plotly_chart(cumulative_bar_chart(ctx["all_eurs"]), use_container_width=True)

