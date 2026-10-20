"""Chapter 2 - "The shock hits" (Streamlit page).

Flow: widgets -> script re-run -> pure functions in charts2.py -> Plotly figure -> st.plotly_chart.
Widget keys use the prefix ch2- so they cannot clash with other chapters.
"""
import streamlit as st

from charts2 import (correlation_text, deaths_figure, deaths_map_figure, error_heatmap_figure, error_stats,
                     gdp_growth_figure, mortality_error_figure, mortality_growth_figure,
                     vaccination_figure, vaccination_gaps)
from data import (ALL_COUNTRIES, PANDEMIC_YEARS, SOURCES, health_annual_deaths, health_monthly_deaths, load_data,
                  load_health, mortality_economy, vaccination_monthly)

CH2_SOURCES = ("Sources: World Bank WDI (actual GDP growth); IMF World Economic Outlook, October 2019 "
               "(forecasts); Our World in Data (cases, deaths, vaccination).")


@st.cache_data
def get_tables():
    df = load_data()
    h = load_health()
    return (df, health_monthly_deaths(h), vaccination_monthly(h), mortality_economy(h, df),
            health_annual_deaths(h))


df, hm, vm, me, annual = get_tables()

st.title("Chapter 2 - The shock hits")
st.markdown(
    "How did the pandemic affect public health and economic growth between 2020 and 2022? "
    "All comparisons are descriptive: they do not show that one factor caused another."
)

# One country selector shared by the whole chapter (same fixed colours everywhere)
KEY = "ch2-countries"
if KEY not in st.session_state:
    st.session_state[KEY] = list(ALL_COUNTRIES)
a, b, _ = st.columns([1, 1, 6])
a.button("Select all", key="ch2-all", on_click=lambda: st.session_state.update({KEY: list(ALL_COUNTRIES)}))
b.button("Clear", key="ch2-clear", on_click=lambda: st.session_state.update({KEY: []}))
countries = st.multiselect("Countries", ALL_COUNTRIES, key=KEY)
if not countries:
    st.info("Select at least one country.")

# ---- 1. GDP growth ----------------------------------------------------------
st.header("1. GDP growth during the pandemic")
st.plotly_chart(gdp_growth_figure(df, countries), use_container_width=True, key="ch2-gdp-chart")
st.caption("Negative growth is a contraction; positive growth is an expansion, not necessarily a full "
           "recovery. " + CH2_SOURCES)

# ---- 2. Forecast error heatmap ---------------------------------------------
st.header("2. The gap between expectations and reality")
st.plotly_chart(error_heatmap_figure(df, countries), use_container_width=True, key="ch2-heatmap-chart")
means = error_stats(df)
st.markdown(
    f"Across all 11 countries the mean forecast error was **{means[2020]:+.2f} pp in 2020**, "
    f"**{means[2021]:+.2f} pp in 2021** and **{means[2022]:+.2f} pp in 2022**. "
    "Growth above forecast does not mean that all economic losses were recovered."
)
st.caption("Forecast error = actual growth minus IMF October 2019 forecast, in percentage points. "
           "It reflects all unexpected developments, not the isolated effect of COVID-19. "
           "Actuals may have been revised after the forecast. " + CH2_SOURCES)

# ---- 3. Deaths ---------------------------------------------------------------
st.header("3. When did the pandemic hit hardest?")
st.plotly_chart(deaths_figure(hm, countries), use_container_width=True, key="ch2-deaths-chart")
st.caption("Reported deaths depend on testing, death registration and reporting practices, so "
           "cross-country comparisons need care. " + CH2_SOURCES)

# ---- 3b. Map of the health shock ---------------------------------------------
st.subheader("The health shock on the map")
m1, m2 = st.columns(2)
map_year = m1.radio("Year", PANDEMIC_YEARS, horizontal=True, key="ch2-map-year")
map_hl = m2.selectbox("Highlight country", ["None"] + ALL_COUNTRIES, key="ch2-map-highlight")
st.plotly_chart(deaths_map_figure(annual, map_year, None if map_hl == "None" else map_hl),
                use_container_width=True, key="ch2-map-chart")
st.caption("Estimated reported deaths per million people over the calendar year (average smoothed daily "
           "rate x days in the year). Same colour scale for all years. Only the 11 study countries are "
           "coloured; grey = not in the study, not zero deaths. Reported deaths depend on testing and "
           "registration practices. " + CH2_SOURCES)

# ---- 4. Vaccination ----------------------------------------------------------
st.header("4. Vaccination")
st.plotly_chart(vaccination_figure(vm, countries), use_container_width=True, key="ch2-vacc-chart")
gaps = vaccination_gaps(vm, countries)
if gaps:
    st.warning("Sparse reporting (lines have gaps; missing is not zero): " + ", ".join(gaps) + ".")
st.caption("Share of the population fully vaccinated, monthly mean of days with data. " + CH2_SOURCES)

# ---- 5 & 6. Scatter plots ----------------------------------------------------
st.header("5. Health impact and economic outcomes")
years = st.multiselect("Years", PANDEMIC_YEARS, default=PANDEMIC_YEARS, key="ch2-years")
t1, t2 = st.tabs(["Mortality vs GDP growth", "Mortality vs forecast error"])
with t1:
    st.plotly_chart(mortality_growth_figure(me, countries, years), use_container_width=True,
                    key="ch2-scatter-growth")
    st.markdown(correlation_text(me, "avg_daily_deaths_per_million", "gdp_growth_pct", countries, years))
with t2:
    st.plotly_chart(mortality_error_figure(me, countries, years), use_container_width=True,
                    key="ch2-scatter-error")
    st.markdown(correlation_text(me, "avg_daily_deaths_per_million", "forecast_error_pp", countries, years))
    st.caption("Reported mortality alone did not consistently explain economic shortfalls relative to "
               "pre-pandemic forecasts.")
st.caption("Each marker is one country-year. " + CH2_SOURCES)