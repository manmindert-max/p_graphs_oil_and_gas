# -*- coding: utf-8 -*-

from __future__ import annotations

import numpy as np

from .arps import calc_eur_tail, fit_arps
from .data import load_data


def fit_all_wells(raw_bytes: bytes, mode: str, forecast_extension_months: int, q_min: float):
    df = load_data(raw_bytes)
    wells = sorted(df["WellName"].unique())

    all_fits, all_eurs, all_subs = {}, {}, {}
    for wname in wells:
        sub = df[df["WellName"] == wname].copy()
        t = sub["TotalProdMonths"].values

        fits, eurs = {}, {}
        for fluid, rate_col, vol_col in [
            ("Oil", "OilRate_BPD", "LiquidsProd_BBL"),
            ("Gas", "GasRate_MCFD", "GasProd_MCF"),
            ("Water", "WaterRate_BPD", "WaterProd_BBL"),
        ]:
            fit = fit_arps(t, sub[rate_col].values, mode=mode)
            fits[fluid] = fit
            eurs[fluid] = calc_eur_tail(
                fit,
                float(np.nansum(sub[vol_col].values)),
                forecast_extension_months=forecast_extension_months,
                q_min=q_min,
            )

        all_fits[wname] = fits
        all_eurs[wname] = eurs
        all_subs[wname] = sub

    return all_fits, all_eurs, all_subs

