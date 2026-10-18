```text
# PROMPT 1 - Forecast vs actual SLOPE CHART

## CONTEXT (project and data)

I am building one page of a multi-page Plotly Dash dashboard called "The World That Never Happened" (a university data-storytelling project on the economic impact of COVID-19). This page is Chapter 1, "The future we expected". The question it answers: what did economists expect before COVID-19, and how far did reality fall from that expectation? The benchmark is the IMF World Economic Outlook forecast of October 2019, made before the pandemic.

TECH: Python 3.12, Dash 2.x, Plotly (plotly.graph_objects and/or plotly.express), pandas, dash-bootstrap-components. Use the Plotly "plotly_white" template.

DATA FILE: `data/ch1_forecast_vs_actual.csv` (keep the path as a constant at the top of the file). 143 rows = 11 countries x 13 years (2010-2022). One row per country-year. Columns:
- iso3 (str): USA, DEU, ESP, SWE, CHN, IND, BRA, ZAF, THA, KOR, SAU
- country (str): display name. Exactly these 11: Brazil, China, Germany, India, Saudi Arabia, South Africa, South Korea, Spain, Sweden, Thailand, United States
- year (int): 2010-2022
- actual_growth_pct (float): actual annual real GDP growth in %, World Bank (indicator NY.GDP.MKTP.KD.ZG). No missing values.
- imf_oct2019_forecast_pct (float): IMF Oct 2019 forecast of real GDP growth in %. ONLY filled for 2019-2022 (44 rows); empty (NaN) for 2010-2018. All 11 countries have a forecast for every year 2019-2022.
- forecast_error_pp (float): actual_growth_pct minus imf_oct2019_forecast_pct, in percentage points (pp). Negative = growth BELOW the forecast, positive = ABOVE. Empty where there is no forecast.
- direction (str): "below forecast" or "above forecast" (empty where no forecast)
- rank_in_year_1_worst (float): rank of the error within that year (1 = largest negative surprise); only for 2019-2022
- period (str): pre_covid, "pre_covid (IMF forecast year)" (2019), shock (2020), recovery (2021-2022)

Example rows (India):
IND, India, 2019, actual 3.871, forecast 6.124, error -2.253
IND, India, 2020, actual -5.778, forecast 7.033, error -12.811
IND, India, 2021, actual 9.690, forecast 7.442, error 2.248
IND, India, 2022, actual 7.609, forecast 7.436, error 0.173

VALUES YOU MUST REPRODUCE (use them to check your work; 2020, in %, shown to 2 decimals):
Country | IMF forecast | Actual | Error (pp)
Brazil | 2.04 | -3.28 | -5.32
China | 5.82 | 2.34 | -3.48
Germany | 1.25 | -4.13 | -5.38
India | 7.03 | -5.78 | -12.81
Saudi Arabia | 2.18 | -3.80 | -5.99
South Africa | 1.08 | -6.17 | -7.25
South Korea | 2.22 | -0.70 | -2.92
Spain | 1.85 | -10.94 | -12.79
Sweden | 1.46 | -1.93 | -3.40
Thailand | 3.01 | -6.09 | -9.10
United States | 2.09 | -2.08 | -4.17

FIXED COLOUR PER COUNTRY (must be identical on every chart of the whole dashboard; define it once as a dict constant COUNTRY_COLOURS):
Brazil #1b9e77, China #d95f02, Germany #7570b3, India #e7298a, Saudi Arabia #66a61e, South Africa #e6ab02, South Korea #a6761d, Spain #1f78b4, Sweden #666666, Thailand #b2182b, United States #08306b.
Other colours: "below forecast" red #b2182b, "above forecast" blue #2166ac.

SOURCES (put in a small footnote under the chart): IMF World Economic Outlook, October 2019 (real GDP growth); World Bank World Development Indicators (NY.GDP.MKTP.KD.ZG).

GENERAL DESIGN RULES: professional and publication-ready; Bootstrap styling (dash-bootstrap-components); a clear title that states the finding; every axis titled with units ("Annual real GDP growth (%)", "percentage points"); readable fonts; no dual axes, no 3D, no pie charts; a zero reference line wherever growth or error is plotted; country names (not ISO codes) shown to the user; hover tooltips with rounded values (1 decimal) and explicit units. Never hard-code data values in the chart code: read everything from the CSV. Handle edge cases gracefully (nothing selected -> show a friendly "Select at least one country" message instead of an error).

DELIVERABLE FORMAT: (1) a pure function that takes a pandas DataFrame plus the control values and returns a plotly Figure, so it can be tested without running the app; (2) a Dash layout component with the controls and a callback that calls that function; give every component id the prefix shown below so it cannot clash with other pages; (3) a short snippet showing how to register it as a page. Keep the code commented. AFTER the code, explain in plain English why each design decision was made (why this chart type, why this sorting, why fixed axes, etc.) and how data flows from control to callback to figure, because I have to explain it in an oral presentation. If something in the spec is ambiguous, state your assumption in one line and proceed instead of asking me questions. Finally, print a quick self-check that compares your figure's data with the verification table above.


#-----CHART 1-----
## THE CHART TO BUILD: forecast-vs-actual slope chart (component id prefix `ch1-slope-`)

PURPOSE: show, for one chosen year, which countries performed furthest below (or above) their pre-pandemic expectations. Each country is one line that connects what the IMF expected to what actually happened.

SPEC:
- Data: rows for ONE selected year. Only use the years 2020, 2021, 2022 (the forecast exists for all 11 countries in those years). Drop rows where imf_oct2019_forecast_pct is empty.
- Layout: two vertical positions on the x-axis: left = "IMF forecast (Oct 2019)", right = "Actual (World Bank)". Y-axis = annual real GDP growth (%). One line per country with markers at both ends, from imf_oct2019_forecast_pct (left) to actual_growth_pct (right). Line colour = the fixed COUNTRY_COLOURS value.
- Labels: at the right-hand end of each line write "Country (+/-error pp)", e.g. "India (-12.8)". Labels will overlap when values are close, so implement a simple vertical de-overlap (sort by y, enforce a minimum gap, keep label colour equal to the line colour). Explain this in your answer.
- Zero line: thin grey horizontal line at y = 0.
- Controls: (a) year selector, radio buttons or dropdown with 2020, 2021, 2022, default 2020; (b) optional "Highlight country" dropdown (None + the 11 countries); when a country is chosen, draw its line thicker and fade the others to about 25% opacity.
- Hover on a line or marker: country, forecast (%), actual (%), error (pp, with sign).
- Dynamic title built from the data, not typed by hand: e.g. "2020: all 11 countries grew less than the IMF expected" (count how many have error < 0 and phrase it correctly for any year, such as "2021: 10 of 11 countries grew more than the IMF expected").
- Dynamic caption under the chart (computed from the data): number of countries below forecast, mean error in pp, and the worst and best country with their errors. Add this fixed sentence: "Steeper downward lines mean larger negative surprises."
- Footnote with the sources above and: "Forecast error = actual growth minus forecast growth, in percentage points."
- Watch out: this chart must only show country-years where the original IMF forecast genuinely exists. Do not interpolate or fill anything.
- Note for the footnote when year = 2022: "Saudi Arabia's 2022 growth (12.0%) is an outlier in the source data; read with caution."
```

---

```text
#-------CHART 2------
## THE CHART TO BUILD: GDP growth timeline 2010-2022 with the IMF forecast overlay (component id prefix `ch1-timeline-`)

PURPOSE: give the audience historical context before they see the forecast error: was 2020 an unusually severe break from each country's own pattern, and how did growth evolve afterwards?

SPEC:
- Data: all rows (2010-2022) for the countries selected by the user.
- Lines: x = year, y = actual_growth_pct, one solid line with small markers per selected country, colour = fixed COUNTRY_COLOURS value.
- Forecast overlay: for 2019-2022 only, draw imf_oct2019_forecast_pct as a DASHED line in the same colour as the country (so the pair is visually linked), with no markers or small ones. A checkbox "Show IMF October 2019 forecast" turns the overlay on and off (default on). Do not draw the forecast for 2010-2018 (no data).
- Reference line: a vertical line at 2020 labelled "COVID shock" (add_vline or a shape plus annotation). Light shading for 2021-2022 labelled "Recovery period".
- Zero line: thin grey horizontal line at y = 0.
- Controls: (a) multi-select dropdown of countries, default = Spain, India, United States, China, with a "Select all" and a "Clear" option; (b) the forecast checkbox above; (c) a view switch "Together / Small multiples": "Together" = all selected countries on one chart; "Small multiples" = one panel per selected country (use make_subplots or px facet_col with 4 columns, shared x-axis, each panel with its own y-scale and the country name as panel title). In small multiples keep black/grey for actual and the country colour or blue for the forecast, and add the annotation "2020 miss: -12.8 pp" in each panel (computed from forecast_error_pp for 2020).
- Hover: year, country, actual growth (%), forecast (%) if available, error (pp) if available.
- Title (dynamic where possible): "GDP growth, 2010-2022, with the pre-COVID IMF forecast". Y-axis title: "Annual real GDP growth (%)". X-axis: year, ticks every year or every 2 years.
- Caption under the chart (static text): "Before 2020, growth in most of these economies moved within a fairly narrow range. 2020 is a break from that pattern, not a continuation of it. The dashed line is what the IMF expected."
- Computed fact under the chart: for the selected countries, state in which of them 2020 was the lowest-growth year of 2010-2022 (compute from the data; it should be true for every country except Brazil, whose 2015-16 recession was deeper).
- Footnote with sources. In "Together" view, tell the user that with many countries selected the chart becomes hard to read and suggest the small-multiples view.
```

---

```text
#-------CHART 3-----
## THE CHART TO BUILD: forecast-error horizontal bar chart (component id prefix `ch1-error-`)

PURPOSE: make the ranking and magnitude of the surprises easy to read. The slope chart shows the comparison; this chart shows who lost the most.

DEFINITION: forecast error = actual growth - IMF forecast growth, in percentage points. It is already in the column forecast_error_pp (verify it equals actual_growth_pct - imf_oct2019_forecast_pct and show that this holds in your self-check).

SPEC:
- Data: rows for ONE selected year among 2020, 2021, 2022 (default 2020). Drop rows with empty forecast_error_pp.
- Chart: horizontal bars. Y-axis = country names, X-axis = forecast_error_pp (title: "Actual minus forecast growth (percentage points)"). Bars sorted from most negative at the top to most positive at the bottom (reverse the y-axis order correctly: in Plotly the first category appears at the bottom unless you set autorange="reversed" or categoryarray; handle it and explain it).
- Colour by sign: negative bars red #b2182b, positive bars blue #2166ac. Show the value at the end of each bar with a sign and one decimal, e.g. "-12.8", "+5.0". Vertical black line at x = 0.
- Fixed x-axis range across years, from -16 to +12, so that bars in different years can be compared visually (explain why a fixed range matters). Keep the range in a constant that is easy to change.
- Controls: (a) year selector 2020 / 2021 / 2022; (b) sort toggle: "By error" (default) or "Alphabetical"; (c) "Highlight country" dropdown (None + 11 countries, with Saudi Arabia as a suggested example in the label text): the chosen country keeps full opacity with a dark outline, the others fade to about 30% opacity.
- Hover: country, forecast (%), actual (%), error (pp, with sign), and the rank in that year (rank_in_year_1_worst, shown as an integer, 1 = largest negative surprise).
- Dynamic title built from the data, e.g. for 2020: "2020: every country fell short of its pre-COVID forecast, by 6.6 pp on average" (mean of forecast_error_pp for that year; phrase it correctly when some countries are above forecast, e.g. 2021: "2021: 10 of 11 countries beat the forecast, by 2.7 pp on average"; the mean there is across all 11 countries).
- Annotation for year 2022 only: a small text note next to the Saudi Arabia bar: "Outlier in source data, interpret with caution".
- Caption under the chart (static): "The gap between actual and forecast growth, in percentage points. Red bars are growth below the forecast, blue bars above it."
- Footnote: "Forecast error = actual growth - forecast growth. This measures how far reality fell from expectations; it is not a causal estimate of the pandemic's effect." plus the sources.
- Optional extra (only if it stays clean): a small context line under the title with the 2019 benchmark: "For comparison, the IMF's average absolute miss across these countries in 2019 was 0.75 pp" (compute it from the 2019 rows, do not hard-code).
```
