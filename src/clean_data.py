
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

COUNTRIES = {
    "USA": "United States",
    "DEU": "Germany",
    "ESP": "Spain",
    "SWE": "Sweden",
    "CHN": "China",
    "IND": "India",
    "BRA": "Brazil",
    "ZAF": "South Africa",
    "THA": "Thailand",
    "KOR": "Korea, Rep.",
    "SAU": "Saudi Arabia",
}

def save(df, filename):
    df.to_csv(OUT / filename, index=False)
    print(f"Saved {filename}: {len(df)} rows")

# 1. IMF — October 2019 GDP growth benchmark
print("\n=== IMF ===")
imf = pd.read_csv(RAW / "imf" / "WEO_Data.xls", sep="\t", dtype=str)

imf_map = {
    "United States": "USA", "Germany": "DEU", "Spain": "ESP",
    "Sweden": "SWE", "China": "CHN", "India": "IND",
    "Brazil": "BRA", "South Africa": "ZAF", "Thailand": "THA",
    "Korea": "KOR", "Saudi Arabia": "SAU",
}

imf = imf[
    imf["WEO Subject Code"].eq("NGDP_RPCH")
    & imf["Country"].isin(imf_map)
].copy()

imf["ISO3"] = imf["Country"].map(imf_map)

years = [str(y) for y in range(2019, 2025)]
for year in years:
    imf[year] = pd.to_numeric(
        imf[year].str.replace(",", "", regex=False),
        errors="coerce"
    )

imf_clean = imf[
    ["ISO3", "Country", "WEO Country Code",
     "WEO Subject Code", "Estimates Start After"] + years
]
save(imf_clean, "imf_gdp_growth_oct2019.csv")

imf_long = imf_clean.melt(
    id_vars=[
        "ISO3", "Country", "WEO Country Code",
        "WEO Subject Code", "Estimates Start After"
    ],
    value_vars=years,
    var_name="year",
    value_name="imf_gdp_growth_pct"
)
imf_long["year"] = imf_long["year"].astype(int)
save(imf_long, "imf_gdp_growth_oct2019_long.csv")

# 2. World Bank
print("\n=== WORLD BANK ===")
wb = pd.read_csv(
    RAW / "world_bank" /
    "9dfdde55-47df-4dd6-9b54-493b1e142ec2_Data.csv",
    dtype=str
)
wb = wb[wb["Country Code"].isin(COUNTRIES)].copy()

# Annual GDP growth
gdp = wb[wb["Series Code"].eq("NY.GDP.MKTP.KD.ZG")].copy()
year_cols = [c for c in gdp.columns if c[:4].isdigit() and "[YR" in c]

gdp_long = gdp.melt(
    id_vars=["Country Name", "Country Code"],
    value_vars=year_cols,
    var_name="year_label",
    value_name="gdp_growth_pct"
)
gdp_long["year"] = gdp_long["year_label"].str[:4].astype(int)
gdp_long["gdp_growth_pct"] = pd.to_numeric(
    gdp_long["gdp_growth_pct"].replace("..", pd.NA),
    errors="coerce"
)
gdp_long = gdp_long.rename(
    columns={"Country Code": "ISO3", "Country Name": "country"}
)
save(
    gdp_long[["ISO3", "country", "year", "gdp_growth_pct"]],
    "world_bank_gdp_growth.csv"
)

# 2019 vulnerability indicators
indicators = {
    "ST.INT.RCPT.XP.ZS": "tourism_receipts_pct_exports",
    "NE.TRD.GNFS.ZS": "trade_pct_gdp",
    "NV.SRV.TOTL.ZS": "services_value_added_pct_gdp",
    "NY.GDP.PETR.RT.ZS": "oil_rents_pct_gdp",
}
v = wb[wb["Series Code"].isin(indicators)].copy()
col2019 = next(c for c in v.columns if c.startswith("2019 [YR2019]"))
v["value"] = pd.to_numeric(v[col2019].replace("..", pd.NA), errors="coerce")
v["indicator"] = v["Series Code"].map(indicators)

v = v.pivot_table(
    index=["Country Code", "Country Name"],
    columns="indicator",
    values="value",
    aggfunc="first"
).reset_index().rename(
    columns={"Country Code": "ISO3", "Country Name": "country"}
)

v = pd.DataFrame({"ISO3": list(COUNTRIES)}).merge(v, on="ISO3", how="left")
save(v, "world_bank_vulnerability_2019.csv")
print("Missing tourism values:", v["tourism_receipts_pct_exports"].isna().sum())

# 3. Our World in Data
print("\n=== OWID ===")
owid = pd.read_csv(RAW / "owid" / "compact.csv", low_memory=False)
owid = owid[
    owid["code"].isin(COUNTRIES)
    & owid["date"].between("2020-01-01", "2022-12-31")
].copy()

keep = [
    "country", "code", "date",
    "new_cases_smoothed_per_million",
    "new_deaths_smoothed_per_million",
    "people_fully_vaccinated_per_hundred",
    "excess_mortality",
]
keep = [c for c in keep if c in owid.columns]
save(owid[keep], "owid_covid_health_2020_2022.csv")

# 4. Oxford COVID-19 Government Response Tracker
print("\n=== OXCGRT ===")
ox = pd.read_csv(
    RAW / "oxcgrt" / "OxCGRT_compact_national_v1.csv",
    low_memory=False
)

ox["Date"] = pd.to_datetime(
    ox["Date"].astype(str).str.replace("-", "", regex=False),
    format="%Y%m%d",
    errors="coerce"
).dt.strftime("%Y-%m-%d")
ox = ox[
    ox["CountryCode"].isin(COUNTRIES)
    & ox["Jurisdiction"].eq("NAT_TOTAL")
    & ox["Date"].str[:4].between("2020", "2022")
].copy()

wanted = [
    "CountryName", "CountryCode", "Date",
    "C1M_School closing", "C2M_Workplace closing",
    "C3M_Cancel public events", "C4M_Restrictions on gatherings",
    "C5M_Close public transport", "C6M_Stay at home requirements",
    "C7M_Restrictions on internal movement",
    "C8EV_International travel controls",
    "E1_Income support", "E2_Debt/contract relief",
    "StringencyIndex_Average", "EconomicSupportIndex",
]
keep = [c for c in wanted if c in ox.columns]
save(ox[keep], "oxcgrt_policy_2020_2022.csv")

# 5. Coverage report
print("\n=== COVERAGE ===")
checks = [
    ("imf_gdp_growth_oct2019_long.csv", "ISO3"),
    ("world_bank_gdp_growth.csv", "ISO3"),
    ("world_bank_vulnerability_2019.csv", "ISO3"),
    ("owid_covid_health_2020_2022.csv", "code"),
    ("oxcgrt_policy_2020_2022.csv", "CountryCode"),
]
for filename, col in checks:
    df = pd.read_csv(OUT / filename)
    found = set(df[col].dropna().unique())
    print(f"{filename}: {len(found)}/11 countries; missing {sorted(set(COUNTRIES)-found)}")

print("\nAll done!")
