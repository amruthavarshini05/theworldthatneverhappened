"""Shared data module for Chapter 1 - "The future we expected".

Every chart on the page uses load_data() so that all of them look at exactly
the same table.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Constants (change DATA_DIR here only)
# --------------------------------------------------------------------------
DATA_DIR = Path("data/processed")
if not (DATA_DIR / "world_bank_gdp_growth.csv").exists():
    # Fallback: CSV files sitting next to this module
    DATA_DIR = Path(__file__).resolve().parent

WB_FILE = "world_bank_gdp_growth.csv"
IMF_FILE = "imf_gdp_growth_oct2019_long.csv"

# Display names used everywhere on screen (the files disagree, e.g. "Korea, Rep." vs "Korea")
DISPLAY_NAMES = {
    "BRA": "Brazil", "CHN": "China", "DEU": "Germany", "IND": "India",
    "ESP": "Spain", "KOR": "South Korea", "SAU": "Saudi Arabia",
    "SWE": "Sweden", "THA": "Thailand", "USA": "United States",
    "ZAF": "South Africa",
}

# One fixed colour per country, identical on every chart of the dashboard
COUNTRY_COLOURS = {
    "Brazil": "#1b9e77", "China": "#d95f02", "Germany": "#7570b3",
    "India": "#e7298a", "Saudi Arabia": "#66a61e", "South Africa": "#e6ab02",
    "South Korea": "#a6761d", "Spain": "#1f78b4", "Sweden": "#666666",
    "Thailand": "#b2182b", "United States": "#08306b",
}
BELOW_COLOUR = "#b2182b"   # growth below the forecast
ABOVE_COLOUR = "#2166ac"   # growth above the forecast

SOURCES = (
    "Sources: IMF World Economic Outlook, October 2019 (real GDP growth forecasts); "
    "World Bank World Development Indicators (NY.GDP.MKTP.KD.ZG, actual growth)."
)
ALL_COUNTRIES = sorted(DISPLAY_NAMES.values())
FORECAST_YEARS = [2020, 2021, 2022]


def load_data() -> pd.DataFrame:
    """Build the single working table (143 rows = 11 countries x 2010-2022)."""
    wb = pd.read_csv(DATA_DIR / WB_FILE)
    imf = pd.read_csv(DATA_DIR / IMF_FILE)

    # Keep only what we need from the IMF file, and only 2019-2022 (actuals end in 2022)
    imf = imf[["ISO3", "year", "imf_gdp_growth_pct"]]
    imf = imf[imf["year"].between(2019, 2022)]

    # LEFT merge: forecast is NaN for 2010-2018 (it does not exist). No filling.
    df = wb.merge(imf, on=["ISO3", "year"], how="left")

    # Overwrite the World Bank name with our display name
    df["country"] = df["ISO3"].map(DISPLAY_NAMES)

    # Forecast error in percentage points (negative = below forecast)
    df["forecast_error_pp"] = df["gdp_growth_pct"] - df["imf_gdp_growth_pct"]

    # Rank within each year, 1 = most negative error; NaN where no forecast
    df["rank_in_year_1_worst"] = (
        df.groupby("year")["forecast_error_pp"].rank(method="min", ascending=True)
    )

    df = df.sort_values(["ISO3", "year"]).reset_index(drop=True)

    assert len(df) == 143, f"expected 143 rows, got {len(df)}"
    assert df["ISO3"].nunique() == 11, "expected 11 countries"
    assert df["forecast_error_pp"].notna().sum() == 44, "expected 44 rows with a forecast"
    return df


# ==========================================================================
# Chapters 2 and 3: health and policy data
# ==========================================================================
HEALTH_FILE = "owid_covid_health_2020_2022.csv"
POLICY_FILE = "oxcgrt_policy_2020_2022.csv"
PANDEMIC_YEARS = [2020, 2021, 2022]


def load_health() -> pd.DataFrame:
    """Daily OWID health data (12,056 rows). Missing values stay NaN (never 0)."""
    h = pd.read_csv(DATA_DIR / HEALTH_FILE, parse_dates=["date"])
    h["country"] = h["code"].map(DISPLAY_NAMES)
    h["year"] = h["date"].dt.year
    h["month"] = h["date"].dt.to_period("M").dt.to_timestamp()
    assert len(h) == 12056 and h["code"].nunique() == 11
    return h


def health_yearly(h: pd.DataFrame) -> pd.DataFrame:
    """Average daily cases/deaths per million, by country and year."""
    return (h.groupby(["country", "code", "year"], as_index=False)
            .agg(avg_daily_cases_per_million=("new_cases_smoothed_per_million", "mean"),
                 avg_daily_deaths_per_million=("new_deaths_smoothed_per_million", "mean")))


def health_monthly_deaths(h: pd.DataFrame) -> pd.DataFrame:
    return (h.groupby(["country", "code", "month"], as_index=False)
            .agg(avg_daily_deaths_per_million=("new_deaths_smoothed_per_million", "mean")))


def vaccination_monthly(h: pd.DataFrame) -> pd.DataFrame:
    """Monthly mean of % fully vaccinated, using only days that have data
    (missing is NOT zero: months with no data are simply absent -> gaps in the line)."""
    v = h.dropna(subset=["people_fully_vaccinated_per_hundred"])
    return (v.groupby(["country", "code", "month"], as_index=False)
            ["people_fully_vaccinated_per_hundred"].mean())


def load_policy() -> pd.DataFrame:
    """Daily OxCGRT policy data (12,056 rows)."""
    p = pd.read_csv(DATA_DIR / POLICY_FILE, parse_dates=["Date"])
    p["country"] = p["CountryCode"].map(DISPLAY_NAMES)
    p["year"] = p["Date"].dt.year
    p["month"] = p["Date"].dt.to_period("M").dt.to_timestamp()
    assert len(p) == 12056 and p["CountryCode"].nunique() == 11
    return p


def policy_monthly(p: pd.DataFrame) -> pd.DataFrame:
    """Monthly average stringency and economic support (396 rows = 11 x 36)."""
    m = (p.groupby(["country", "month"], as_index=False)
         .agg(stringency=("StringencyIndex_Average", "mean"),
              economic_support=("EconomicSupportIndex", "mean")))
    assert len(m) == 396
    return m


def policy_country_avg(p: pd.DataFrame) -> pd.DataFrame:
    """Average of both indices over 2020-2022, one row per country."""
    return (p.groupby("country", as_index=False)
            .agg(avg_stringency=("StringencyIndex_Average", "mean"),
                 avg_economic_support=("EconomicSupportIndex", "mean")))


def tradeoff_2020(p: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """2020 average policy indices joined with 2020 GDP growth (11 rows)."""
    a = (p[p["year"] == 2020].groupby("country", as_index=False)
         .agg(avg_stringency=("StringencyIndex_Average", "mean"),
              avg_economic_support=("EconomicSupportIndex", "mean")))
    g = df.loc[df["year"] == 2020, ["country", "gdp_growth_pct"]]
    out = a.merge(g, on="country", how="inner", validate="one_to_one")
    assert len(out) == 11
    return out


def mortality_economy(h: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Country-year table (2020-2022, 33 rows): deaths per million, GDP growth, forecast and error."""
    hy = health_yearly(h)
    m = hy.merge(df[["country", "year", "gdp_growth_pct", "imf_gdp_growth_pct", "forecast_error_pp"]],
                 on=["country", "year"], how="inner", validate="one_to_one")
    assert len(m) == 33
    return m


def health_annual_deaths(h: pd.DataFrame) -> pd.DataFrame:
    """Estimated reported COVID-19 deaths per million over each calendar year.

    = mean of the smoothed daily rate x number of days in the year. Using the mean
    (instead of a plain sum) keeps the estimate fair when a few days have no data.
    """
    g = (h.groupby(["country", "code", "year"], as_index=False)
         .agg(avg_daily=("new_deaths_smoothed_per_million", "mean"),
              days_with_data=("new_deaths_smoothed_per_million", "count"),
              days_in_year=("date", "nunique")))
    g["annual_deaths_per_million"] = g["avg_daily"] * g["days_in_year"]
    assert len(g) == 33
    return g[["country", "code", "year", "annual_deaths_per_million", "days_with_data", "days_in_year"]]


# ==========================================================================
# Chapter 5: recovery (indices, output gap vs the IMF-expected path, pre-COVID band)
# ==========================================================================
BAND_YEARS = (2012, 2019)          # years used for the typical pre-COVID growth range
RECOVERY_YEARS = [2020, 2021, 2022]


def load_recovery_data() -> pd.DataFrame:
    """Working table for Chapter 5: one row per country-year for 2019-2022 (44 rows).

    Both indices start at 100 in 2019 (actual 2019 level), so the IMF's small 2019 miss is
    ignored on purpose. index(y) = index(y-1) * (1 + growth(y)/100) for 2020-2022.
    """
    wb = pd.read_csv(DATA_DIR / WB_FILE)
    imf = pd.read_csv(DATA_DIR / IMF_FILE)[["ISO3", "year", "imf_gdp_growth_pct"]]
    imf = imf[imf["year"].between(2019, 2022)]

    # Pre-COVID band from 2012-2019 actual growth (8 observations: indicative only)
    pre = wb[wb["year"].between(*BAND_YEARS)]
    band = pre.groupby("ISO3")["gdp_growth_pct"].agg(["mean", "std"])      # std = sample SD (ddof=1)
    band["band_low_pct"] = band["mean"] - band["std"]
    band["band_high_pct"] = band["mean"] + band["std"]
    band = band.rename(columns={"mean": "pre_mean_pct", "std": "pre_sd_pct"}).reset_index()

    d = (wb[wb["year"].between(2019, 2022)]
         .merge(imf, on=["ISO3", "year"], how="inner", validate="one_to_one")
         .merge(band, on="ISO3", how="left", validate="many_to_one"))
    d["country"] = d["ISO3"].map(DISPLAY_NAMES)
    d = d.sort_values(["ISO3", "year"]).reset_index(drop=True)
    d["forecast_error_pp"] = d["gdp_growth_pct"] - d["imf_gdp_growth_pct"]

    def _index(growth: pd.Series, years: pd.Series) -> pd.Series:
        g = growth.where(years > 2019, 0.0)          # 2019 is the base: factor 1
        return 100 * (1 + g / 100).cumprod()

    d["actual_index"] = d.groupby("ISO3", group_keys=False).apply(
        lambda x: _index(x["gdp_growth_pct"], x["year"]), include_groups=False)
    d["imf_expected_index"] = d.groupby("ISO3", group_keys=False).apply(
        lambda x: _index(x["imf_gdp_growth_pct"], x["year"]), include_groups=False)

    d["output_gap_vs_imf_pct"] = (d["actual_index"] / d["imf_expected_index"] - 1) * 100
    d["output_vs_2019_pct"] = d["actual_index"] - 100
    d["above_2019_level"] = d["actual_index"] >= 100
    d["above_imf_path"] = d["output_gap_vs_imf_pct"] >= 0
    rank = d[d["year"] >= 2020].groupby("year")["output_gap_vs_imf_pct"].rank(method="min", ascending=True)
    d["rank_output_gap_in_year_1_worst"] = rank          # NaN for 2019 by construction

    assert len(d) == 44 and d["ISO3"].nunique() == 11
    no_nan = d.drop(columns=["rank_output_gap_in_year_1_worst"])
    assert not no_nan.isna().any().any(), "unexpected NaN in recovery table"
    assert d.loc[d["year"] == 2019, "rank_output_gap_in_year_1_worst"].isna().all()
    return d


# ==========================================================================
# Chapter 4: structural vulnerabilities (World Bank 2019) vs forecast shortfall
# ==========================================================================
VULN_FILE = "chapter4_vulnerability_dataset.csv"

# column -> label shown on screen
VULN_VARS = {
    "tourism_receipts_pct_exports": "Tourism receipts (% of exports)",
    "trade_pct_gdp": "Trade openness (% of GDP)",
    "services_value_added_pct_gdp": "Services value added (% of GDP)",
    "oil_rents_pct_gdp": "Oil rents (% of GDP)",
}
INCOME_COLOURS = {"High income": "#2b6cb0", "Upper-middle income": "#dd8452", "Lower-middle income": "#c44e52"}
SHORTFALL_COLS = ["shortfall_2019", "shortfall_2020", "shortfall_2021", "shortfall_2022"]
TRADE_OPEN_THRESHOLD = 60.0   # % of GDP: "very open" cut-off used in the group comparison


def load_vulnerability() -> pd.DataFrame:
    """One row per country (11): 2019 vulnerabilities + shortfalls + 2020 context (team's export).

    Tourism receipts are genuinely missing for Spain, Sweden and China: they stay NaN
    (never 0, never filled).
    """
    v = pd.read_csv(DATA_DIR / VULN_FILE)
    v["country"] = v["ISO3"].map(DISPLAY_NAMES)          # one display name everywhere
    assert len(v) == 11 and v["ISO3"].nunique() == 11
    assert v["tourism_receipts_pct_exports"].isna().sum() == 3
    assert v[[c for c in v.columns if c not in ("tourism_receipts_pct_exports",)]].notna().all().all()
    return v


def spearman_table(v: pd.DataFrame, target: str, variables=None) -> pd.DataFrame:
    """Spearman rho (+ p-value) and Pearson r of each vulnerability with `target`.
    Rows with a missing value are dropped for that variable only (tourism: n = 8)."""
    from scipy import stats
    rows = []
    for col in (variables or list(VULN_VARS)):
        s = v[[col, target]].dropna()
        rho, p = stats.spearmanr(s[col], s[target])
        r, _ = stats.pearsonr(s[col], s[target])
        rows.append({"variable": col, "label": VULN_VARS.get(col, col), "n": len(s),
                     "spearman_rho": rho, "p_value": p, "pearson_r": r})
    return pd.DataFrame(rows).set_index("variable")


def leave_one_out(v: pd.DataFrame, target: str) -> pd.DataFrame:
    """Spearman rho recomputed after removing each country in turn.
    Rows = removed country, columns = vulnerability variables."""
    out = {}
    for col in VULN_VARS:
        s = v[["country", col, target]].dropna().set_index("country")
        out[col] = pd.Series({c: s.drop(c)[col].corr(s.drop(c)[target], method="spearman") for c in s.index})
    return pd.DataFrame(out)


def partial_spearman(v: pd.DataFrame, x: str, y: str, z: str):
    """Partial Spearman correlation of x and y controlling for z (on ranks). Illustrative, n <= 11."""
    s = v[[x, y, z]].dropna().rank()
    rx = s[x] - np.polyval(np.polyfit(s[z], s[x], 1), s[z])
    ry = s[y] - np.polyval(np.polyfit(s[z], s[y], 1), s[z])
    return float(np.corrcoef(rx, ry)[0, 1]), len(s)


def context_correlations(v: pd.DataFrame, target="shortfall_2020") -> pd.Series:
    cols = ["deaths_per_million_2020", "stringency_2020", "travel_controls_2020", "econ_support_2020",
            "tourism_receipts_pct_exports", "trade_pct_gdp"]
    return v[cols + [target]].corr(method="spearman")[target].drop(target)


GROUPINGS = {
    "income_group": "Income group",
    "tourism_group": "Tourism dependence",
    "trade_group": "Trade openness",
    "services_group": "Services share",
}
GROUP_TARGETS = {
    "shortfall_2020": "Shortfall 2020 (pp)", "shortfall_2021": "Shortfall 2021 (pp)",
    "shortfall_2022": "Shortfall 2022 (pp)", "level_gap_2022": "Output gap end-2022 (%)",
}


def add_groups(v: pd.DataFrame) -> pd.DataFrame:
    """Add the group columns (median splits for tourism and services, 60% of GDP for trade)."""
    g = v.copy()
    t = g["tourism_receipts_pct_exports"]
    g["tourism_group"] = np.where(t.isna(), "Data missing", np.where(t >= t.median(), "High tourism", "Low tourism"))
    g["trade_group"] = np.where(g["trade_pct_gdp"] >= TRADE_OPEN_THRESHOLD,
                                f"Very open (>= {TRADE_OPEN_THRESHOLD:.0f}% of GDP)",
                                f"Less open (< {TRADE_OPEN_THRESHOLD:.0f}% of GDP)")
    s = g["services_value_added_pct_gdp"]
    g["services_group"] = np.where(s >= s.median(), "High services", "Low services")
    return g


def group_summary(v: pd.DataFrame) -> pd.DataFrame:
    """Mean of each target by group, for every grouping (long table)."""
    g = add_groups(v)
    parts = {}
    for col in GROUPINGS:
        m = g.groupby(col)[list(GROUP_TARGETS)].mean()
        m["n"] = g.groupby(col).size()
        parts[GROUPINGS[col]] = m.rename(columns=GROUP_TARGETS)
    return pd.concat(parts, names=["grouping", "group"])