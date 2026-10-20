"""Chapter 1 - "The future we expected" (Streamlit page).

Data flow: widget (st.radio / st.selectbox / st.multiselect ...)
   -> Streamlit re-runs this script top to bottom
   -> the widget value is passed to a pure function in charts.py
   -> the function returns a plotly Figure (+ title/caption strings)
   -> st.plotly_chart / st.caption display them.
Widget keys use the prefixes ch1-slope-, ch1-timeline-, ch1-error- so that
other chapters (pages) can never clash with them.
"""
import streamlit as st

from charts import (benchmark_2019_line, error_data, error_figure, lowest_year_fact,
                    slope_caption, slope_data, slope_figure, timeline_figure)
from data import ALL_COUNTRIES, FORECAST_YEARS, SOURCES, load_data


@st.cache_data
def get_data():
    """load_data() is run once and cached; every chart uses the same table."""
    return load_data()


df = get_data()
NONE = "None"

st.title("Chapter 1 - The future we expected")
st.markdown(
    "What did economists expect before COVID-19, and how far did reality fall from that "
    "expectation? The benchmark is the IMF World Economic Outlook forecast of October 2019."
)

# ==========================================================================
# CHART 1 - slope chart
# ==========================================================================
st.header("1. Forecast vs actual growth")
c1, c2 = st.columns(2)
slope_year = c1.radio("Year", FORECAST_YEARS, index=0, horizontal=True, key="ch1-slope-year")
slope_hl = c2.selectbox("Highlight country", [NONE] + ALL_COUNTRIES, key="ch1-slope-highlight")
slope_hl = None if slope_hl == NONE else slope_hl

st.plotly_chart(slope_figure(df, slope_year, slope_hl), use_container_width=True,
                key="ch1-slope-chart")
sd = slope_data(df, slope_year)
if not sd.empty:
    st.markdown(slope_caption(sd))
foot = "Forecast error = actual growth minus forecast growth, in percentage points. " + SOURCES
if slope_year == 2022:
    foot += " Saudi Arabia's 2022 growth (12.0%) is an outlier in the source data; read with caution."
st.caption(foot)

st.divider()

# ==========================================================================
# CHART 2 - timeline
# ==========================================================================
st.header("2. Growth 2010-2022 and the IMF forecast")
TL_KEY = "ch1-timeline-countries"
if TL_KEY not in st.session_state:                      # default selection (set before the widget)
    st.session_state[TL_KEY] = ["Spain", "India", "United States", "China"]


def _select_all():
    st.session_state[TL_KEY] = list(ALL_COUNTRIES)


def _clear():
    st.session_state[TL_KEY] = []


b1, b2, _ = st.columns([1, 1, 6])
b1.button("Select all", on_click=_select_all, key="ch1-timeline-all")
b2.button("Clear", on_click=_clear, key="ch1-timeline-clear")
tl_countries = st.multiselect("Countries", ALL_COUNTRIES, key=TL_KEY)
k1, k2 = st.columns(2)
show_fc = k1.checkbox("Show IMF October 2019 forecast", value=True, key="ch1-timeline-forecast")
view = k2.radio("View", ["Together", "Small multiples"], horizontal=True, key="ch1-timeline-view")

if not tl_countries:
    st.info("Select at least one country.")
else:
    st.plotly_chart(timeline_figure(df, tl_countries, show_fc, view), use_container_width=True,
                    key="ch1-timeline-chart")
    st.markdown(
        "Before 2020, growth in most of these economies moved within a fairly narrow range. "
        "2020 is a break from that pattern, not a continuation of it. "
        "The dashed line is what the IMF expected."
    )
    st.markdown(lowest_year_fact(df, tl_countries))
    if view == "Together":
        st.caption("With many countries selected this chart becomes hard to read; "
                   "try the Small multiples view.")
st.caption(SOURCES)

st.divider()

# ==========================================================================
# CHART 3 - forecast error bars
# ==========================================================================
st.header("3. Who lost the most? Forecast error by country")
e1, e2, e3 = st.columns(3)
err_year = e1.radio("Year", FORECAST_YEARS, index=0, horizontal=True, key="ch1-error-year")
err_sort = e2.radio("Sort", ["By error", "Alphabetical"], horizontal=True, key="ch1-error-sort")
err_hl = e3.selectbox("Highlight country (e.g. Saudi Arabia)", [NONE] + ALL_COUNTRIES,
                      key="ch1-error-highlight")
err_hl = None if err_hl == NONE else err_hl

bench = benchmark_2019_line(df)
if bench:
    st.caption(bench)
st.plotly_chart(error_figure(df, err_year, err_sort, err_hl), use_container_width=True,
                key="ch1-error-chart")
st.markdown("The gap between actual and forecast growth, in percentage points. "
            "Red bars are growth below the forecast, blue bars above it.")
st.caption("Forecast error = actual growth - forecast growth. This measures how far reality fell "
           "from expectations; it is not a causal estimate of the pandemic's effect. " + SOURCES)
