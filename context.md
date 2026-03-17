# Enverus Well Production Analyzer (Streamlit)

## Goal
Interactive Streamlit app to analyze monthly Enverus production data for a set of wells:
- Semi-log rate plots for **Oil / Gas / Water** (scatter) with fitted **Arps decline** curves (+ forecast extension).
- Per-well fitted parameters (`qi`, `Di`, `b`, `R²`) and **EUR**.
- Set-level **P10 / P50 / P90** EUR analysis and **P10/P90 ratio**.
- **Outlier detection + optional exclusion** that propagates through all group analyses.
- **P50 type curve**: median-of-rates-by-month composite, then hyperbolic Arps fit + parameters.

## Input schema (Enverus CSV)
Required columns:
- `WellName`
- `ProducingMonth` (parseable as date)
- `TotalProdMonths` (1, 2, 3, …)
- `ProducingDays`
- `LiquidsProd_BBL`
- `GasProd_MCF`
- `WaterProd_BBL`

Derived daily rates:
- `OilRate_BPD   = LiquidsProd_BBL / ProducingDays`
- `GasRate_MCFD  = GasProd_MCF     / ProducingDays`
- `WaterRate_BPD = WaterProd_BBL   / ProducingDays`

## Key definitions
### Arps decline fit
Fitted per well and per fluid (Oil/Gas/Water), using one of:
- Hyperbolic, Exponential, Harmonic

Parameters:
- `qi`: initial rate at `t=0` (first positive-rate month used in fit)
- `Di`: nominal decline rate (1/month)
- `b`: hyperbolic exponent (`b=0` exponential, `b=1` harmonic)
- `R²`: goodness-of-fit to the fitted points

### EUR (per well, per fluid)
**EUR = cumulative actual to date + forecast tail**

- `CumActual` = sum of reported monthly volumes for that fluid.
- `Forecast tail` = integral of the fitted decline curve **from the last positive-rate month** (`t_last`)
  to `t_last + ForecastExtensionMonths`, with rates below the economic limit set to zero.

### P10 / P50 / P90 (EUR distribution)
Computed across **active wells** (after optional exclusion), per fluid:
- **P10 (high case)** = 90th percentile of EUR distribution
- **P50** = median
- **P90 (low case)** = 10th percentile

Also shown:
- **P10/P90 ratio** per fluid as an uncertainty/spread metric.

### Outliers and exclusion
Outliers are **flagged on Oil EUR only** using an IQR rule:
- bounds = `[Q1 − k·IQR, Q3 + k·IQR]`

UI allows:
- Re-including auto-flagged wells
- Manually excluding additional wells

All group analyses (P10/P50/P90, type curves, P50 type curve fit) use only **active wells**.

### P50 type curve
1) Evaluate each active-well fitted curve on a common time grid (`t=0..t_max`) and clip each well to
   `t <= t_last + ForecastExtensionMonths`.
2) Take the **median rate at each time step** to form the P50 composite profile.
3) Fit a **hyperbolic** Arps curve to that P50 profile (above economic limit).

## How to run
From repo root:
1) `python -m venv .venv`
2) Activate venv
3) `pip install -r requirements.txt`
4) `streamlit run streamlit_app.py`

The app is configured to use the bundled sample file by default:
- `env_csv-Production-e788d_2026-03-16.csv`

## Known limitations
- Fits can be unstable with very sparse/noisy data or many shut-in months (zeros).
- This is a classic Arps decline approach; it does not model operational changes, re-fracs, workovers, etc.
- Economic limit and forecast extension materially affect EUR; treat as scenario controls.
