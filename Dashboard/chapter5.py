"""Chapter 5 - "The recovery wasn't equal" (Streamlit page).

Flow: widget -> script re-run -> pure function in charts5.py -> Plotly figure -> st.plotly_chart.
Widget keys use the prefix ch5-traj- / ch5-rank- so they cannot clash with other chapters.
"""
import streamlit as st

from charts5 import (DEFAULT_METRIC, METRICS, band_available, rank_caption, rank_data, rank_figure,
                     trajectories_caption, trajectories_figure)
from data import ALL_COUNTRIES, RECOVERY_YEARS, SOURCES, load_recovery_data

CH5_SOURCES = (SOURCES + " Indices and gaps are our own calculation from these growth rates.")
NONE = "None"


@st.cache_data
def get_data():
    return load_recovery_data()


df = get_data()

st.title("Chapter 5 - The recovery wasn't equal")
st.markdown(
    "After the 2020 shock, who returned to the economic path expected before COVID-19, and who did "
    "not? A **rebound** (fast growth in 2021) is not the same as a **recovery** (output back on the "
    "expected path)."
)

# ==========================================================================
# CHART 1 - trajectories
# ==========================================================================
st.header("1. Rebound versus the pre-COVID forecast")
KEY = "ch5-traj-countries"
if KEY not in st.session_state:
    st.session_state[KEY] = ["Spain", "India", "Thailand", "United States"]
a, b, _ = st.columns([1, 1, 6])
a.button("Select all", key="ch5-traj-all", on_click=lambda: st.session_state.update({KEY: list(ALL_COUNTRIES)}))
b.button("Clear", key="ch5-traj-clear", on_click=lambda: st.session_state.update({KEY: []}))
countries = st.multiselect("Countries", ALL_COUNTRIES, key=KEY)
k1, k2, k3 = st.columns([2, 3, 2])
show_fc = k1.checkbox("Show IMF October 2019 forecast", value=True, key="ch5-traj-forecast")
view = k3.radio("View", ["Together", "Small multiples"], horizontal=True, key="ch5-traj-view")
ok_band = band_available(countries, view)
show_band = k2.checkbox("Show typical pre-COVID growth range (mean ± 1 SD, 2012-2019)", value=False,
                        key="ch5-traj-band", disabled=not ok_band)
if not ok_band and countries:
    k2.caption("The range differs by country: select exactly one country, or switch to Small multiples.")

if not countries:
    st.info("Select at least one country.")
else:
    st.plotly_chart(trajectories_figure(df, countries, show_fc, show_band and ok_band, view),
                    use_container_width=True, key="ch5-traj-chart")
    st.markdown(trajectories_caption(df, countries))
    st.markdown("A high growth rate in 2021 can reflect a rebound from a low base. It does not mean the "
                "economy has fully recovered; compare with the recovery-gap ranking below.")
foot = CH5_SOURCES
if show_band and ok_band:
    foot += " The typical range uses only 8 observations (2012-2019) and is only indicative."
if "Saudi Arabia" in countries:
    foot += " Saudi Arabia's 2022 growth (12.0%) is an outlier in the source data; read with caution."
st.caption(foot)

st.divider()

# ==========================================================================
# CHART 2 - recovery-gap ranking
# ==========================================================================
st.header("2. Recovery-gap ranking")
r1, r2, r3 = st.columns([2, 3, 2])
year = r1.radio("Year", RECOVERY_YEARS, index=RECOVERY_YEARS.index(2022), horizontal=True, key="ch5-rank-year")
metric = r2.radio("Metric", list(METRICS), index=list(METRICS).index(DEFAULT_METRIC), key="ch5-rank-metric")
hl = r3.selectbox("Highlight country", [NONE] + ALL_COUNTRIES, key="ch5-rank-highlight")
st.caption(METRICS[metric]["note"])

st.plotly_chart(rank_figure(df, year, metric, None if hl == NONE else hl), use_container_width=True,
                key="ch5-rank-chart")
st.markdown(rank_caption(rank_data(df, year, metric), year, metric))
foot2 = ("Gap = (actual index / expected index - 1) x 100, both indices starting at 100 in 2019. "
         + CH5_SOURCES + " This describes distance from expectations; it is not a causal estimate of "
         "the pandemic's effect.")
if year == 2022:
    foot2 += " Saudi Arabia's 2022 growth (12.0%) is an outlier in the source data; read with caution."
st.caption(foot2)
