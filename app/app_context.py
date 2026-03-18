# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from .data import load_data
from .fitting import fit_all_wells
from .outliers import detect_outliers, outlier_scatter


@st.cache_data(show_spinner=False)
def load_data_cached(raw_bytes: bytes):
    return load_data(raw_bytes)


@st.cache_data(show_spinner=False)
def fit_all_wells_cached(raw_bytes: bytes, decline_mode: str, forecast_extension_months: int, q_min: float):
    return fit_all_wells(raw_bytes, decline_mode, forecast_extension_months, q_min)


def sidebar_settings():
    st.title("⚙️ Settings")
    st.markdown("---")
    decline_mode = st.selectbox("Arps Decline Type", ["hyperbolic", "exponential", "harmonic"], index=0)
    forecast_extension_months = st.slider("Forecast Extension (months beyond last actual)", 0, 600, 360, step=30)
    q_min = st.number_input("Economic Limit (BPD / MCFD)", value=0.1, min_value=0.0, step=0.05)
    st.markdown("---")
    iqr_factor = st.slider(
        "Outlier IQR Factor",
        1.0,
        3.0,
        1.5,
        step=0.1,
        help="Wells with Oil EUR outside Q1 − k·IQR or Q3 + k·IQR are flagged.",
    )
    return decline_mode, forecast_extension_months, q_min, iqr_factor


def get_app_context():
    default_path = Path(__file__).resolve().parents[1] / "env_csv-Production-e788d_2026-03-16.csv"
    if not default_path.exists():
        st.error(f"Default data file not found: {default_path}")
        st.stop()

    raw_bytes = default_path.read_bytes()
    try:
        df = load_data_cached(raw_bytes)
    except Exception as e:
        st.error(f"❌ Could not load file: {e}")
        st.stop()

    # Sidebar controls (now that we know the date range in the dataset)
    prod_min = df["ProducingMonth"].min()
    prod_max = df["ProducingMonth"].max()
    min_date = prod_min.date() if prod_min is not None and prod_min == prod_min else None
    max_date = prod_max.date() if prod_max is not None and prod_max == prod_max else None

    with st.sidebar:
        decline_mode, forecast_extension_months, q_min, iqr_factor = sidebar_settings()
        st.markdown("---")
        enable_prod_date_filter = st.checkbox(
            "Filter wells by production date",
            value=False,
            help="Keep only wells that have at least one non-zero production record on/after the cutoff date.",
        )
        prod_date_cutoff = st.date_input(
            "Include wells with production on/after",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            disabled=not enable_prod_date_filter,
        )

    all_wells_total = sorted(df["WellName"].unique())
    eligible_wells = set(all_wells_total)
    if enable_prod_date_filter and prod_date_cutoff is not None:
        cutoff_ts = df["ProducingMonth"].dt.tz_localize(None) >= pd.Timestamp(prod_date_cutoff)
        nonzero = (df["LiquidsProd_BBL"] > 0) | (df["GasProd_MCF"] > 0) | (df["WaterProd_BBL"] > 0)
        eligible_wells = set(df.loc[cutoff_ts & nonzero, "WellName"].unique().tolist())

    all_wells = sorted(eligible_wells)
    st.success(
        f"✅ Loaded `{default_path.name}`: **{len(df):,}** records across **{len(all_wells_total)}** wells."
    )
    if enable_prod_date_filter:
        st.info(
            f"Date filter active: **{len(all_wells)} / {len(all_wells_total)}** wells have non-zero production "
            f"on/after **{prod_date_cutoff.isoformat()}**."
        )
        if not all_wells:
            st.error("No wells match the selected production-date filter.")
            st.stop()

    with st.spinner("Fitting Arps curves for all wells…"):
        all_fits_full, all_eurs_full, all_subs_full = fit_all_wells_cached(
            raw_bytes, decline_mode, forecast_extension_months, q_min
        )
        # Re-scope to eligible wells (if a date filter is active)
        all_fits_full = {w: all_fits_full[w] for w in all_wells}
        all_eurs_full = {w: all_eurs_full[w] for w in all_wells}
        all_subs_full = {w: all_subs_full[w] for w in all_wells}

    outlier_df = detect_outliers(all_eurs_full, iqr_factor=iqr_factor)
    flagged = outlier_df[outlier_df["Outlier"]].index.tolist()

    with st.expander(
        f"🚨 Outlier Detection — {len(flagged)} well(s) flagged (expand to review & exclude)",
        expanded=(len(flagged) > 0),
    ):
        st.markdown(
            "Wells are flagged using the **IQR method on Oil EUR**. "
            "Adjust the *IQR Factor* in the sidebar to tighten or relax the threshold."
        )
        st.plotly_chart(outlier_scatter(outlier_df, []), use_container_width=True)

        col_tbl, col_ctrl = st.columns([2, 1])
        with col_tbl:
            display_df = outlier_df.copy()
            for c in ["Oil EUR", "Gas EUR", "Water EUR"]:
                display_df[c] = display_df[c].map(lambda x: f"{x:,.0f}" if x == x else "—")
            st.dataframe(display_df[["Oil EUR", "Gas EUR", "Water EUR", "Outlier", "Reason"]], use_container_width=True)
        with col_ctrl:
            st.markdown("**Manually exclude additional wells:**")
            extra_exclude = st.multiselect(
                "Add to exclusion list",
                options=[w for w in all_wells if w not in flagged],
                default=[],
                key="extra_exclude",
            )
            st.markdown("**Auto-flagged outliers to keep:**")
            keep_flagged = st.multiselect(
                "Re-include flagged wells",
                options=flagged,
                default=[],
                key="keep_flagged",
            )

    excluded_wells = [w for w in flagged if w not in keep_flagged] + extra_exclude
    active_wells = [w for w in all_wells if w not in excluded_wells]

    if excluded_wells:
        st.warning(f"⚠️ **{len(excluded_wells)} well(s) excluded**: " + ", ".join(excluded_wells))
    else:
        st.info(f"✅ All **{len(active_wells)}** wells active (none excluded).", icon="✅")

    all_fits = {w: all_fits_full[w] for w in active_wells}
    all_eurs = {w: all_eurs_full[w] for w in active_wells}
    all_subs = {w: all_subs_full[w] for w in active_wells}

    return {
        "data_file_path": str(default_path),
        "data_file_name": default_path.name,
        "raw_bytes": raw_bytes,
        "df": df,
        "decline_mode": decline_mode,
        "forecast_extension_months": forecast_extension_months,
        "q_min": q_min,
        "enable_prod_date_filter": enable_prod_date_filter,
        "prod_date_cutoff": prod_date_cutoff,
        "iqr_factor": iqr_factor,
        "all_wells": all_wells,
        "active_wells": active_wells,
        "excluded_wells": excluded_wells,
        "all_fits_full": all_fits_full,
        "all_eurs_full": all_eurs_full,
        "all_subs_full": all_subs_full,
        "all_fits": all_fits,
        "all_eurs": all_eurs,
        "all_subs": all_subs,
    }
