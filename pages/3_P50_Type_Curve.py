# -*- coding: utf-8 -*-

import streamlit as st

from app.app_context import get_app_context
from app.typecurves import build_p50_profile, fit_p50_curve, p50_type_curve_figure


st.set_page_config(page_title="P50 Type Curve", page_icon="📈", layout="wide")

ctx = get_app_context()

st.markdown(f"## 📈 P50 Type Curve — Hyperbolic Arps Fit ({len(ctx['active_wells'])} wells)")
st.caption(
    "The P50 composite profile is the **median rate at each time step** across all active-well Arps curves. "
    "A new **hyperbolic** Arps curve is then fitted to this synthetic median profile."
)

with st.spinner("Building P50 profile and fitting…"):
    profiles = build_p50_profile(ctx["all_fits"], ctx["forecast_extension_months"])
    p50_fits = fit_p50_curve(profiles, ctx["q_min"])
    fig, params_df = p50_type_curve_figure(profiles, p50_fits, ctx["q_min"])

st.plotly_chart(fig, use_container_width=True)

if not params_df.empty:
    st.markdown("### P50 Type-Curve Fitted Parameters")
    st.dataframe(params_df.set_index("Fluid"), use_container_width=True)

    st.markdown("### P50 Type-Curve EUR (integrated from t = 0)")
    c1, c2, c3 = st.columns(3)
    for col, fluid, unit in zip([c1, c2, c3], ["Oil", "Gas", "Water"], ["BBL", "MCF", "BBL"]):
        fit = p50_fits.get(fluid)
        eur_val = float(fit.get("eur", 0)) if fit else 0
        col.metric(f"P50 {fluid} EUR ({unit})", f"{eur_val:,.0f}")

    st.markdown("### How to Read the Parameters")
    st.markdown(
        """
| Parameter | Meaning |
|-----------|---------|
| **qi** | Initial rate of the P50 type-curve (BPD or MCFD) at t = 0 |
| **Di** | Nominal decline rate (month⁻¹) — higher = faster early decline |
| **b** | Hyperbolic exponent: b=0 exponential, b=1 harmonic, 0<b<1 typical shale |
| **R²** | Goodness-of-fit to the P50 composite profile (1.0 = perfect) |
| **EUR** | Estimated Ultimate Recovery from t=0 to end of the type-curve time grid |
        """
    )
else:
    st.warning("Could not fit P50 type curve — insufficient data.")

