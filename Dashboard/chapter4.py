"""Chapter 4 - "Not every country starts with the same cards" (Streamlit page).

Flow: widget -> script re-run -> pure function in charts4.py / data.py -> figure -> st.plotly_chart.
Widget keys use the prefix ch4- so they cannot clash with other chapters.
"""
import streamlit as st

from charts4 import (DEFAULT_OUTCOME, OUTCOME_METRICS, context_figure, correlation_figure,
                     correlation_text, exposure_bubble_figure, group_figure, leave_one_out_figure,
                     leave_one_out_text, oil_figure, outcome_figure, pre_covid_bias_figure,
                     profile_heatmap_figure)
from data import (ALL_COUNTRIES, GROUP_TARGETS, GROUPINGS, VULN_VARS, context_correlations,
                  group_summary, load_vulnerability, partial_spearman)

CH4_SOURCES = ("Sources: World Bank WDI (2019 vulnerability indicators, actual GDP growth); IMF World "
               "Economic Outlook, October 2019 (forecasts); OxCGRT; Our World in Data. Income groups: "
               "World Bank classification (FY2020).")
NONE = "None"


@st.cache_data
def get_data():
    return load_vulnerability()


v = get_data()

st.title("Chapter 4 - Not every country starts with the same cards")
st.markdown(
    "Why were some economies more vulnerable than others? Chapters 1-3 showed *how far* each country "
    "fell from the IMF's October 2019 path. This chapter looks **before** the pandemic: which structural "
    "features did each economy carry into the shock?"
)
st.warning(
    "The October 2019 forecast is a benchmark, not the GDP of a world without COVID: a gap can also "
    "reflect other shocks (oil prices, the war in Ukraine, a slowdown already under way). With only 11 "
    "countries every correlation below is descriptive and proves no causal link."
)

# ---- 1. outcome --------------------------------------------------------------
st.header("1. The outcome to explain")
c1, c2 = st.columns([3, 2])
metric = c1.radio("Measure", list(OUTCOME_METRICS), index=list(OUTCOME_METRICS).index(DEFAULT_OUTCOME),
                  horizontal=True, key="ch4-outcome-metric")
hl = c2.selectbox("Highlight country", [NONE] + ALL_COUNTRIES, key="ch4-outcome-highlight")
st.plotly_chart(outcome_figure(v, metric, None if hl == NONE else hl), use_container_width=True,
                key="ch4-outcome-chart")
st.caption("The shock of 2020 hits everyone but not equally; by end-2022 the ranking changes. Saudi "
           "Arabia ends above its path because of the 2022 oil boom, not because of the pandemic. "
           + CH4_SOURCES)

# ---- 2. profiles -------------------------------------------------------------
st.header("2. The cards in hand in 2019")
st.plotly_chart(profile_heatmap_figure(v), use_container_width=True, key="ch4-profile-chart")
st.caption("Colour = rank within the 11-country panel (darker = more exposed); the printed number is the "
           "raw 2019 value. Grey cells marked n/a are missing data, not zero: tourism receipts are "
           "unavailable for Spain, Sweden and China. " + CH4_SOURCES)
st.plotly_chart(exposure_bubble_figure(v), use_container_width=True, key="ch4-bubble-chart")
st.caption("Thailand is first on both tourism and trade openness. Spain, Sweden and China have no tourism "
           "figure (parked below the axis), so the tourism analysis covers 8 countries and leaves out "
           "Spain, the most tourism-dependent economy of the panel. " + CH4_SOURCES)

# ---- 3. correlations ---------------------------------------------------------
st.header("3. Do vulnerabilities explain the shortfall?")
a, b = st.columns(2)
target_label = a.radio("Outcome", ["Shock: 2020 shortfall", "End-2022 output gap"], horizontal=True,
                       key="ch4-corr-target")
target = "shortfall_2020" if target_label.startswith("Shock") else "level_gap_2022"
var = b.selectbox("Vulnerability", list(VULN_VARS), format_func=lambda k: VULN_VARS[k], key="ch4-corr-var")
st.plotly_chart(correlation_figure(v, var, target), use_container_width=True, key="ch4-corr-chart")
st.markdown(correlation_text(v, target))
st.caption("Spearman rank correlation (robust with 11 points and extreme values such as Saudi oil rents "
           "and Thai trade). The oil relationship with the 2022 gap is carried by a single country. "
           + CH4_SOURCES)

st.subheader("Robustness: what if one country is removed?")
st.plotly_chart(leave_one_out_figure(v), use_container_width=True, key="ch4-loo-chart")
st.markdown(leave_one_out_text(v))
st.caption("Use these as guard-rails: the dashboard shows tendencies and cases, not laws.")

# ---- 4. groups ---------------------------------------------------------------
st.header("4. Comparing groups of countries")
g1, g2 = st.columns(2)
grouping = g1.radio("Group countries by", list(GROUPINGS), format_func=lambda k: GROUPINGS[k],
                    horizontal=True, key="ch4-group-by")
gtarget = g2.selectbox("Outcome", list(GROUP_TARGETS), index=3, format_func=lambda k: GROUP_TARGETS[k],
                       key="ch4-group-target")
st.plotly_chart(group_figure(v, grouping, gtarget), use_container_width=True, key="ch4-group-chart")
with st.expander("Group means table"):
    st.dataframe(group_summary(v).round(2), use_container_width=True)
st.caption("Income group is the most discriminating dimension of the panel. Saudi Arabia is classed as "
           "high income and lifts its group's mean for oil reasons; the lower-middle-income group is India "
           "alone (n = 1). " + CH4_SOURCES)

# ---- 5. structure vs crisis management ---------------------------------------
st.header("5. Structure or crisis management?")
st.plotly_chart(context_figure(v), use_container_width=True, key="ch4-context-chart")
cc = context_correlations(v)
names = {"deaths_per_million_2020": "COVID deaths per million", "stringency_2020": "Stringency",
         "travel_controls_2020": "International travel controls", "econ_support_2020": "Economic support",
         "tourism_receipts_pct_exports": "Tourism receipts", "trade_pct_gdp": "Trade openness"}
st.markdown("**Spearman rho with the 2020 shortfall:** " + "; ".join(f"{names[k]} {x:+.2f}" for k, x in cc.items()) + ".")
st.markdown(
    "Thailand had very few deaths and light restrictions yet a −9 pp shock: it was hit from the outside "
    "(world tourism and trade). Sweden, very open, kept restrictions light and limited the economic "
    "shock. Brazil and the United States, the most closed economies, had heavy health tolls but moderate "
    "economic shocks."
)
pr = [(VULN_VARS[k].split(" (")[0], *partial_spearman(v, k, "shortfall_2020", "stringency_2020")) for k in VULN_VARS]
st.markdown("**Partial correlation with the 2020 shortfall, controlling for stringency (illustrative):** "
            + "; ".join(f"{n} {r:+.2f} (n = {k})" for n, r, k in pr) + ".")
st.caption("Economic support correlates with a bigger shock because the hardest-hit countries supported "
           "their economies most (reverse causality), not because support worsens the shock. "
           "Deaths = sum of smoothed daily deaths per million over 2020 (days without data count as zero). "
           + CH4_SOURCES)

# ---- 6. oil ------------------------------------------------------------------
st.header("6. Oil: a vulnerability that cuts both ways")
oc = st.multiselect("Countries", ALL_COUNTRIES, default=["Saudi Arabia", "Brazil", "Thailand", "United States"],
                    key="ch4-oil-countries")
st.plotly_chart(oil_figure(v, oc), use_container_width=True, key="ch4-oil-chart")
st.caption("Saudi Arabia (oil rents = 24% of GDP) fell in 2020 with oil demand, then beat its forecast by "
           "almost 10 pp in 2022. The 2022 gap no longer measures COVID: for 'COVID damage' comparisons "
           "prefer the 2020 gap or the 2020-2021 total. " + CH4_SOURCES)

# ---- 7. 2019 bias ------------------------------------------------------------
st.header("7. A starting bias to keep in mind")
st.plotly_chart(pre_covid_bias_figure(v), use_container_width=True, key="ch4-bias-chart")
st.caption("If the IMF was already wrong in 2019, part of the 2020-2022 gap reflects initial optimism, "
           "not the pandemic. India was already 2.3 pp below forecast in 2019, so part of its cumulative "
           "gap cannot be attributed to the pandemic. " + CH4_SOURCES)

# ---- takeaways ---------------------------------------------------------------
st.header("What to remember")
st.markdown(
    "- **Nobody started with the same cards**: Thailand combines tourism dependence and extreme trade "
    "openness; Saudi Arabia depends on oil; the United States is service-based but closed.\n"
    "- **Structure explains only part of the story**: no single vulnerability ranks the countries well. "
    "Exposure predisposes; it does not condemn.\n"
    "- **Tourism is the most consistent channel** (stable expected sign, strong link with international "
    "travel controls), but Spain is missing from that analysis.\n"
    "- **Income matters**: middle-income countries ended further from their path than rich ones, a natural "
    "bridge to Chapter 5.\n"
    "- **Limits**: missing tourism data (Spain, Sweden, China); the Saudi 2022 gap is about oil; India's "
    "forecast was already too optimistic in 2019; small-panel correlations are descriptive."
)
