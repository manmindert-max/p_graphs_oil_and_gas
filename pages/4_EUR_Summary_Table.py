# -*- coding: utf-8 -*-

import io

import pandas as pd
import streamlit as st

from app.app_context import get_app_context
from app.constants import FLUIDS


st.set_page_config(page_title="EUR Summary", page_icon="📋", layout="wide")

ctx = get_app_context()

st.markdown("## 📋 Complete EUR & Fitted Parameter Summary")
st.caption(f"Active wells: {len(ctx['active_wells'])} | Excluded: {len(ctx['excluded_wells'])}")

rows = []
for wname in ctx["active_wells"]:
    fits = ctx["all_fits"][wname]
    eurs = ctx["all_eurs"][wname]
    row = {"Well": wname, "Status": "Active"}
    for fluid in FLUIDS:
        fit = fits.get(fluid)
        row[f"{fluid} EUR"] = f"{eurs.get(fluid, 0):,.0f}"
        row[f"{fluid} qi"] = f"{fit['qi']:.2f}" if fit else "—"
        row[f"{fluid} Di"] = f"{fit['Di']:.5f}" if fit else "—"
        row[f"{fluid} b"] = f"{fit['b']:.3f}" if fit else "—"
        row[f"{fluid} R²"] = f"{fit['r2']:.3f}" if fit else "—"
        row[f"{fluid} Decline"] = fit["label"] if fit else "—"
    rows.append(row)

for wname in ctx["excluded_wells"]:
    fits = ctx["all_fits_full"][wname]
    eurs = ctx["all_eurs_full"][wname]
    row = {"Well": f"[EXCL] {wname}", "Status": "Excluded"}
    for fluid in FLUIDS:
        fit = fits.get(fluid)
        row[f"{fluid} EUR"] = f"{eurs.get(fluid, 0):,.0f}"
        row[f"{fluid} qi"] = f"{fit['qi']:.2f}" if fit else "—"
        row[f"{fluid} Di"] = f"{fit['Di']:.5f}" if fit else "—"
        row[f"{fluid} b"] = f"{fit['b']:.3f}" if fit else "—"
        row[f"{fluid} R²"] = f"{fit['r2']:.3f}" if fit else "—"
        row[f"{fluid} Decline"] = fit["label"] if fit else "—"
    rows.append(row)

eur_table = pd.DataFrame(rows).set_index("Well")
st.dataframe(eur_table, use_container_width=True)

csv_buf = io.StringIO()
eur_table.to_csv(csv_buf)
st.download_button(
    "⬇️ Download EUR & Parameter Table (CSV)",
    data=csv_buf.getvalue(),
    file_name="eur_summary_table.csv",
    mime="text/csv",
)

