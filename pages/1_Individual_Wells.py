# -*- coding: utf-8 -*-

import streamlit as st

from app.app_context import get_app_context
from app.plots import semilog_well_figure


st.set_page_config(page_title="Individual Wells", page_icon="🔍", layout="wide")

ctx = get_app_context()

st.markdown("## 🔍 Individual Wells")
selected_well = st.selectbox("Select Well", ctx["active_wells"])
sub = ctx["all_subs"][selected_well]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Producing Months", len(sub))
k2.metric("Cum Oil (BBL)", f"{sub['LiquidsProd_BBL'].sum():,.0f}")
k3.metric("Cum Gas (MCF)", f"{sub['GasProd_MCF'].sum():,.0f}")
k4.metric("Cum Water (BBL)", f"{sub['WaterProd_BBL'].sum():,.0f}")

st.markdown("### Production Plot")
fig, params_df = semilog_well_figure(
    sub,
    selected_well,
    ctx["decline_mode"],
    ctx["forecast_extension_months"],
    ctx["q_min"],
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### Arps Fitted Parameters")
if not params_df.empty:
    st.dataframe(params_df.set_index("Fluid"), use_container_width=True)
else:
    st.warning("Could not fit decline curves (insufficient data points).")

st.markdown("### Estimated Ultimate Recovery (EUR)")
e1, e2, e3 = st.columns(3)
e1.metric("Oil EUR (BBL)", f"{ctx['all_eurs_full'][selected_well].get('Oil', 0):,.0f}")
e2.metric("Gas EUR (MCF)", f"{ctx['all_eurs_full'][selected_well].get('Gas', 0):,.0f}")
e3.metric("Water EUR (BBL)", f"{ctx['all_eurs_full'][selected_well].get('Water', 0):,.0f}")

with st.expander("📄 Raw production data"):
    st.dataframe(
        sub[
            [
                "ProducingMonth",
                "TotalProdMonths",
                "ProducingDays",
                "LiquidsProd_BBL",
                "GasProd_MCF",
                "WaterProd_BBL",
                "OilRate_BPD",
                "GasRate_MCFD",
                "WaterRate_BPD",
            ]
        ],
        use_container_width=True,
    )

