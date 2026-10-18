# Chapter 5 prompts (data described in terms of our original files)

Paste the two blocks into ONE LLM conversation, in order. Block 1 contains the shared context and the first chart; block 2 only adds the second chart and refers back to the context. All data comes from the files already in the repo (`world_bank_gdp_growth.csv` and `imf_gdp_growth_oct2019_long.csv`); the index, gaps and band are computed in code, so there are no extra CSVs. If you use the same conversation as Chapter 1, tell the LLM to reuse its Chapter 1 `load_data()` pieces (DISPLAY_NAMES, COUNTRY_COLOURS) and extend them.

---

```text
# CHAPTER 5 - CHART 1: RECOVERY TRAJECTORIES
I am building one page of a multi-page Plotly Dash dashboard called "The World That Never Happened" (a university data-storytelling project on the economic impact of COVID-19). This page is Chapter 5, "The recovery wasn't equal". The question it answers: after the 2020 shock, who returned to the economic path that was expected before COVID-19, and who did not? The benchmark is the IMF World Economic Outlook forecast of October 2019, made before the pandemic. Important idea for the whole page: a REBOUND (high growth in 2021) is not the same as a RECOVERY (output back on the expected path). A country can grow fast after a deep fall and still be behind where it was expected to be.

TECH: Python 3.12, Dash 2.x, Plotly (plotly.graph_objects and/or plotly.express), pandas, dash-bootstrap-components. Use the Plotly "plotly_white" template.

## CONTEXT (project and data)

DATA FILES (already cleaned by our team; they sit in `data/processed/`; keep the folder as a constant DATA_DIR at the top of the file; read them with pandas.read_csv, they have Windows line endings, which pandas handles):

1) `world_bank_gdp_growth.csv` = ACTUAL growth. 143 rows = 11 countries x 13 years (2010-2022), one row per country-year, rows NOT sorted (sort by ISO3 and year after loading). No missing values. Columns:
   - ISO3 (str): BRA, CHN, DEU, ESP, IND, KOR, SAU, SWE, THA, USA, ZAF
   - country (str): World Bank name (Korea is "Korea, Rep."; see DISPLAY_NAMES below)
   - year (int): 2010 to 2022
   - gdp_growth_pct (float): actual annual real GDP growth in % (World Bank WDI, indicator NY.GDP.MKTP.KD.ZG), e.g. India 2020 = -5.778

2) `imf_gdp_growth_oct2019_long.csv` = IMF FORECAST, long format. 66 rows = 11 countries x 6 years (2019-2024). No missing values. Columns:
   - ISO3 (str): same codes as above
   - Country (str): IMF name (capital C; Korea is "Korea")
   - WEO Country Code (int), WEO Subject Code (str, always NGDP_RPCH = real GDP growth, % change), Estimates Start After (int, always 2018, meaning the IMF treats 2019 onwards as projections in this edition): not needed, ignore them. Note that column names contain spaces.
   - year (int): 2019 to 2024. ONLY USE 2019-2022 (our actuals end in 2022); ignore 2023 and 2024.
   - imf_gdp_growth_pct (float): IMF World Economic Outlook, October 2019, forecast of real GDP growth in %, e.g. India 2020 = 7.033

3) `imf_gdp_growth_oct2019.csv` is the same IMF data in WIDE format (one column per year). Do NOT use it; use the long file in (2).

(The other files in the folder, `world_bank_vulnerability_2019.csv`, `oxcgrt_policy_2020_2022.csv`, `owid_covid_health_2020_2022.csv`, are used by other chapters and are NOT needed here.)

DISPLAY_NAMES (use these everywhere on screen; do NOT use the `country`/`Country` columns of the files, because they differ between files: the World Bank file says "Korea, Rep." and the IMF file says "Korea"):
BRA Brazil, CHN China, DEU Germany, ESP Spain, IND India, KOR South Korea, SAU Saudi Arabia, SWE Sweden, THA Thailand, USA United States, ZAF South Africa.

HOW TO BUILD THE WORKING TABLE (write one function `load_data()` in a shared module and use it for every chart on the page; return a single DataFrame `df`, one row per country-year for 2019-2022, 44 rows):
- Read file 1 and file 2. Keep years 2019-2022 only (drop 2010-2018 for the working table, but FIRST use 2012-2019 of file 1 to compute the pre-COVID band below). From file 2 keep only ISO3, year, imf_gdp_growth_pct for 2019-2022.
- Merge the two on [ISO3, year] (inner merge; all 44 rows match, no missing values). Add `country` = DISPLAY_NAMES[ISO3].
- `forecast_error_pp` = gdp_growth_pct - imf_gdp_growth_pct (percentage points; negative = below forecast).
- `actual_index` = real GDP level index with 2019 = 100, built from ACTUAL growth, per country: index(2019) = 100; index(y) = index(y-1) * (1 + gdp_growth_pct(y)/100) for y = 2020, 2021, 2022.
- `imf_expected_index` = the same index built from the IMF FORECAST growth (imf_gdp_growth_pct) for 2020-2022, also starting at 100 in 2019. It is the "expected path". Both indices share the same starting point (actual 2019 = 100), so the IMF's small 2019 forecast miss is ignored on purpose.
- `output_gap_vs_imf_pct` = (actual_index / imf_expected_index - 1) * 100. Negative = output is BELOW the path the IMF expected; positive = above it. This is the lasting loss (or gain) relative to expectations.
- `output_vs_2019_pct` = actual_index - 100 (how far output sits above or below its 2019 level).
- `above_2019_level` = actual_index >= 100; `above_imf_path` = output_gap_vs_imf_pct >= 0.
- `rank_output_gap_in_year_1_worst` = rank of output_gap_vs_imf_pct among the 11 countries within each year 2020-2022 (1 = furthest below the expected path); empty for 2019.
- Pre-COVID band (used by chart 1 only): from file 1 compute, per country, the mean and the sample standard deviation (pandas .std(), ddof=1) of gdp_growth_pct over 2012-2019 (8 observations, so only indicative). `band_low_pct` = mean - SD and `band_high_pct` = mean + SD, same value on all four rows of a country. Example: China mean 7.07, SD 0.60; Spain mean 1.43, SD 2.36.
- Sort by ISO3 and year. Assert in the code: 44 rows, 11 countries, no NaN except rank for 2019.

Example rows (Spain): 2019: index 100, expected 100, gap 0 | 2020: gdp_growth_pct -10.94, imf_gdp_growth_pct 1.85, actual_index 89.06, imf_expected_index 101.85, gap -12.56 | 2021: growth 6.68, actual_index 95.01, imf_expected_index 103.58, gap -8.27 | 2022: growth 6.37, actual_index 101.06, imf_expected_index 105.31, gap -4.03.

VALUES YOU MUST REPRODUCE (use them to check your work; index points and %, tolerance +/-0.01 for rounding):
Country | Actual index 2022 | IMF-expected index 2022 | Gap 2020 (%) | Gap 2021 (%) | Gap 2022 (%)
Brazil | 104.39 | 106.92 | -5.21 | -3.00 | -2.37
China | 114.59 | 118.45 | -3.29 | -0.85 | -3.26
Germany | 101.42 | 104.08 | -5.31 | -3.01 | -2.55
India | 111.22 | 123.55 | -11.97 | -10.13 | -9.98
Saudi Arabia | 114.76 | 106.96 | -5.86 | -1.90 | +7.30
South Africa | 100.42 | 104.34 | -7.17 | -4.04 | -3.76
South Korea | 106.71 | 108.07 | -2.85 | -1.09 | -1.25
Spain | 101.06 | 105.31 | -12.56 | -8.27 | -4.03
Sweden | 104.49 | 105.59 | -3.35 | -0.34 | -1.04
Thailand | 97.89 | 110.49 | -8.83 | -10.54 | -11.41
United States | 106.57 | 105.49 | -4.09 | +0.07 | +1.02
Also: by 2022 only Saudi Arabia (+7.3%) and the United States (+1.0%) are above the expected path; Thailand is the only country below its 2019 level in 2022 (index 97.89). Actual growth in 2021: India 9.69, China 8.57, Spain 6.68, Saudi Arabia 6.52, United States 6.15, Thailand 1.56 (lowest). Actual growth in 2022: Saudi Arabia 12.00 (an outlier in the source data), India 7.61, Spain 6.37.

FIXED COLOUR PER COUNTRY (must be identical on every chart of the whole dashboard; define it once as a dict constant COUNTRY_COLOURS keyed by display name):
Brazil #1b9e77, China #d95f02, Germany #7570b3, India #e7298a, Saudi Arabia #66a61e, South Africa #e6ab02, South Korea #a6761d, Spain #1f78b4, Sweden #666666, Thailand #b2182b, United States #08306b.
Other colours: "below" red #b2182b, "above" blue #2166ac.

SOURCES (small footnote under the chart): IMF World Economic Outlook, October 2019 (real GDP growth forecasts); World Bank World Development Indicators (NY.GDP.MKTP.KD.ZG, actual growth). Indices and gaps are our own calculation from these growth rates.

GENERAL DESIGN RULES: professional and publication-ready; Bootstrap styling (dash-bootstrap-components); a clear title that states the finding; every axis titled with units; readable fonts; no dual axes, no 3D, no pie charts; a reference line wherever there is a meaningful baseline (0 for growth and errors, 100 for the index); country names (not ISO codes) shown to the user; hover tooltips with values rounded to 1 decimal and explicit units. Never hard-code data values in the chart code: read everything from the CSV files. Handle edge cases gracefully (nothing selected -> show a friendly "Select at least one country" message instead of an error).

DELIVERABLE FORMAT: (1) the shared `load_data()` function described above; (2) a pure function that takes the DataFrame plus the control values and returns a plotly Figure, so it can be tested without running the app; (3) a Dash layout component with the controls and a callback that calls that function; give every component id the prefix shown below so it cannot clash with other pages; (4) a short snippet showing how to register it as a page. Keep the code commented. AFTER the code, explain in plain English why each design decision was made (why this chart type, why this baseline, why fixed axes, etc.) and how data flows from control to callback to figure, because I have to explain it in an oral presentation. If something in the spec is ambiguous, state your assumption in one line and proceed instead of asking me questions. Finally, print a quick self-check that compares your figure's data with the verification table above.

#---------CHART 1-------
## THE CHART TO BUILD: recovery trajectories (component id prefix `ch5-traj-`)

PURPOSE: show which countries rebounded sharply in 2021, which had a more gradual recovery, and whether actual growth returned to or exceeded the original IMF expectation.

SPEC:
- Data: rows for the selected countries, all four years (2019-2022).
- Lines: x = year (2019, 2020, 2021, 2022; show only these four integer ticks), y = gdp_growth_pct, one solid line with markers per selected country, colour = fixed COUNTRY_COLOURS value.
- IMF overlay: imf_gdp_growth_pct as a DASHED line in the same colour as the country, from 2019 to 2022. A checkbox "Show IMF October 2019 forecast" turns it on or off (default on).
- 2020 highlight: light grey vertical band around 2020 labelled "COVID shock"; light blue band for 2021-2022 labelled "Recovery period".
- Typical-range band (optional toggle, default off): checkbox "Show typical pre-COVID growth range (mean +/- 1 SD, 2012-2019)". It draws a light horizontal band from band_low_pct to band_high_pct. Because the band differs per country, draw it ONLY when exactly one country is selected (or in each panel of the small-multiples view); when several countries are selected, disable the checkbox and show a small hint explaining why. Purpose: show whether the 2021 rebound was large relative to the country's normal ups and downs. State in the footnote that the band is based on only 8 observations and is only indicative.
- Zero line: thin grey horizontal line at y = 0.
- Controls: (a) multi-select dropdown of countries, default = Spain, India, Thailand, United States, with "Select all" and "Clear"; (b) the two checkboxes above; (c) view switch "Together / Small multiples" (small multiples = one panel per selected country, 4 columns, shared x-axis, each panel with its own y-scale, country name as panel title; in each panel use black for actual and the country colour or blue for the forecast).
- Hover: country, year, actual growth (%), IMF forecast (%), error (pp, with sign).
- Title: "GDP growth 2019-2022: rebound versus the pre-COVID forecast" (or a dynamic version). Y-axis title: "Annual real GDP growth (%)".
- Dynamic caption computed from the data for the selected countries: "In 2021, X of N selected countries grew faster than the IMF expected; in 2022, Y of N." (use forecast_error_pp > 0).
- Fixed caption sentence (must appear under the chart): "A high growth rate in 2021 can reflect a rebound from a low base. It does not mean the economy has fully recovered; compare with the recovery-gap ranking."
- Footnote: sources, plus "Saudi Arabia's 2022 growth (12.0%) is an outlier in the source data; read with caution" (show it only when Saudi Arabia is selected).
```

---

```text
#----------CHART 2-------
Use the same context, DATA_DIR, DISPLAY_NAMES, COUNTRY_COLOURS and load_data() as in the previous message (same conversation). Do not redefine them differently.

## THE CHART TO BUILD: recovery-gap ranking (component id prefix `ch5-rank-`)

PURPOSE: rank the 11 countries by how far their output sits from the path the IMF expected, so the audience sees who returned to the expected path and who did not. Unlike the Chapter 1 forecast-error bars (one year's growth miss), this ranks ACCUMULATED output after the shock.

SPEC:
- Data: rows for ONE selected year among 2020, 2021, 2022 (default 2022).
- Chart: horizontal bars. Y-axis = country names, X-axis = the chosen metric. Bars sorted from most negative at the top to most positive at the bottom (handle the Plotly category order correctly, e.g. autorange="reversed" or categoryarray, and explain it). Vertical black line at 0.
- Metric switch (radio buttons): (1) "Output gap vs IMF-expected path (%)", default, column output_gap_vs_imf_pct; (2) "Output vs 2019 level (%)", column output_vs_2019_pct. Explain in a one-line note under the switch what each metric means: (1) how far output is from where it was expected to be; (2) how far output is from where it was in 2019. Metric 2 is descriptive and does not use the forecast.
- Colour by sign: negative bars red #b2182b, positive bars blue #2166ac. Show the value at the end of each bar with a sign and one decimal, e.g. "-11.4", "+7.3".
- Fixed x-axis ranges so that bars in different years can be compared (explain why this matters): metric 1 from -14 to +9; metric 2 from -13 to +17. Keep these in constants.
- Controls: (a) year selector 2020 / 2021 / 2022; (b) metric radio; (c) "Highlight country" dropdown (None + the 11 countries): the chosen country keeps full opacity with a dark outline, the others fade to about 30% opacity.
- Hover: country, actual index, IMF-expected index, output gap vs expected path (%), output vs 2019 level (%), regained 2019 level? (yes/no from above_2019_level), rank (rank_output_gap_in_year_1_worst as an integer, 1 = furthest below the expected path).
- Dynamic title built from the data: for metric 1: "2022: only 2 of 11 countries ended above their expected path" (count rows with output_gap_vs_imf_pct >= 0 in that year and phrase it correctly for every year, e.g. 2020: "2020: all 11 countries were below their expected path"; 2021: "2021: only 1 of 11 countries was back on its expected path"). For metric 2: count countries above their 2019 level, e.g. "2022: 10 of 11 countries were above their 2019 output level".
- Annotation for year 2022 only, next to the Saudi Arabia bar: "Outlier in source data, interpret with caution".
- Fixed caption (must appear under the chart): "Positive bars mean output has overtaken the path the IMF expected before COVID; negative bars mean output is still below it. India and Thailand show the largest lasting gaps in 2022."  Make the India/Thailand sentence data-driven (pick the two most negative countries in the selected year and metric) so it stays correct when the controls change; for other years/metrics rephrase it generically.
- Footnote: how the gap is calculated: (actual index / expected index - 1) x 100, both indices starting at 100 in 2019; sources; "This describes distance from expectations; it is not a causal estimate of the pandemic's effect."
```
