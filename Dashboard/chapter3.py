"""Chapter 3 - "Governments make their choices" (Streamlit page).

Widget keys use the prefix ch3- so they cannot clash with other chapters.
"""
import streamlit as st

from charts3 import bubble_figure, extremes_text, grouped_bar_figure, stringency_figure, support_figure
from data import (ALL_COUNTRIES, load_data, load_policy, policy_country_avg, policy_monthly,
                  tradeoff_2020)

CH3_SOURCES = ("Sources: Oxford COVID-19 Government Response Tracker (OxCGRT); "
               "World Bank WDI (actual GDP growth).")
NONE = "None"


@st.cache_data
def get_tables():
    p = load_policy()
    return policy_monthly(p), policy_country_avg(p), tradeoff_2020(p, load_data())


pm, avg, trade = get_tables()

st.title("Chapter 3 - Governments make their choices")
st.markdown(
    "Governments combined public-health restrictions with economic support in different ways. "
    "The indices describe what governments did, not how well it worked."
)

KEY = "ch3-countries"
if KEY not in st.session_state:
    st.session_state[KEY] = list(ALL_COUNTRIES)
a, b, _ = st.columns([1, 1, 6])
a.button("Select all", key="ch3-all", on_click=lambda: st.session_state.update({KEY: list(ALL_COUNTRIES)}))
b.button("Clear", key="ch3-clear", on_click=lambda: st.session_state.update({KEY: []}))
countries = st.multiselect("Countries", ALL_COUNTRIES, key=KEY)
if not countries:
    st.info("Select at least one country.")

st.header("1. Policy stringency over time")
st.plotly_chart(stringency_figure(pm, countries), use_container_width=True, key="ch3-stringency-chart")
st.caption("The Stringency Index (0-100) summarises the strictness of selected policies. Higher means "
           "stricter; it does not measure effectiveness or public compliance. " + CH3_SOURCES)

st.header("2. Economic support over time")
st.plotly_chart(support_figure(pm, countries), use_container_width=True, key="ch3-support-chart")
st.caption("The Economic Support Index (0-100) reflects the recorded scope of income support and debt/"
           "contract relief, not the money spent or received. Sudden changes should be read cautiously. "
           + CH3_SOURCES)

st.header("3. Stringency and economic support compared")
st.plotly_chart(grouped_bar_figure(avg, countries), use_container_width=True, key="ch3-bars-chart")
st.markdown(extremes_text(avg))
st.caption("Average over 2020-2022. The two indices measure different dimensions and are not directly "
           "equivalent. " + CH3_SOURCES)

st.header("4. The stringency paradox (2020)")
hl = st.selectbox("Highlight country", [NONE] + ALL_COUNTRIES, key="ch3-bubble-highlight")
st.plotly_chart(bubble_figure(trade, countries, None if hl == NONE else hl),
                use_container_width=True, key="ch3-bubble-chart")
st.markdown(
    "China recorded positive growth (+2.34%) despite the highest average stringency in the sample, "
    "while Spain contracted by 10.94% despite a relatively high Economic Support Index; Thailand "
    "contracted by 6.09% alongside a high support index. Neither stringency nor reported support alone "
    "explains these outcomes."
)
st.caption("Bubble size and colour = average Economic Support Index in 2020. Economic structure, tourism "
           "and trade exposure, pandemic severity and pre-existing vulnerabilities also matter. "
           "Exploratory and descriptive: no causal claim. " + CH3_SOURCES)
