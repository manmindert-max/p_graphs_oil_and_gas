# -*- coding: utf-8 -*-

from __future__ import annotations

import io

import numpy as np
import pandas as pd

from .constants import ENVERUS_REQUIRED_COLS


def load_data(raw_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw_bytes))
    df.columns = df.columns.str.strip()
    missing = ENVERUS_REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["ProducingMonth"] = pd.to_datetime(df["ProducingMonth"], errors="coerce")
    df = df.sort_values(["WellName", "TotalProdMonths"])

    for col in ["LiquidsProd_BBL", "GasProd_MCF", "WaterProd_BBL", "ProducingDays", "TotalProdMonths"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["LiquidsProd_BBL"] = df["LiquidsProd_BBL"].fillna(0).clip(lower=0)
    df["GasProd_MCF"] = df["GasProd_MCF"].fillna(0).clip(lower=0)
    df["WaterProd_BBL"] = df["WaterProd_BBL"].fillna(0).clip(lower=0)
    df["ProducingDays"] = df["ProducingDays"].fillna(0).clip(lower=0)

    days = df["ProducingDays"].replace(0, np.nan)
    df["OilRate_BPD"] = df["LiquidsProd_BBL"] / days
    df["GasRate_MCFD"] = df["GasProd_MCF"] / days
    df["WaterRate_BPD"] = df["WaterProd_BBL"] / days

    return df

