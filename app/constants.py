# -*- coding: utf-8 -*-

OIL_COLOR = "#2ECC71"
GAS_COLOR = "#E74C3C"
WATER_COLOR = "#3498DB"
FIT_COLOR = "#F39C12"
OUTLIER_COLOR = "#E67E22"
P50_FIT_COLOR = "#9B59B6"

FLUIDS = ["Oil", "Gas", "Water"]

FLUID_COLORS = {"Oil": OIL_COLOR, "Gas": GAS_COLOR, "Water": WATER_COLOR}
FLUID_UNITS = {"Oil": "BPD", "Gas": "MCFD", "Water": "BPD"}
FLUID_VOL = {"Oil": "BBL", "Gas": "MCF", "Water": "BBL"}

ENVERUS_REQUIRED_COLS = {
    "WellName",
    "ProducingMonth",
    "LiquidsProd_BBL",
    "GasProd_MCF",
    "WaterProd_BBL",
    "TotalProdMonths",
    "ProducingDays",
}

