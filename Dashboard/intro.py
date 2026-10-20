"""Introduction page: the question, the benchmark, the chapter guide, the data and how to read it."""
import pandas as pd
import streamlit as st

from data import COUNTRY_COLOURS
from summary import compute_headlines


@st.cache_data
def get_headlines():
    return compute_headlines()


h = get_headlines()

st.title("The World That Never Happened")
st.subheader("COVID-19 and the economic path the world expected")
st.markdown(
    "In October 2019 the IMF published its forecast of economic growth for the years ahead. Then the "
    "pandemic arrived. This dashboard asks one question: **what did economists expect before COVID-19, and "
    "how far did reality fall from that expectation?** We follow 11 economies from the expected future of "
    "2019 to the outcomes of 2020-2022."
)

c1, c2, c3 = st.columns(3)
c1.metric("Countries followed", h["n_countries"])
c2.metric("Average miss in 2020", f"{h['mean_err'][2020]:+.1f} pp",
          help="Actual growth minus IMF October 2019 forecast, mean of the 11 countries.")
c3.metric("Average miss in 2021", f"{h['mean_err'][2021]:+.1f} pp")

st.header("The idea in one sentence")
st.info(
    "A **rebound** (fast growth after a fall) is not the same as a **recovery** (output back on the path "
    "that was expected). A country can grow fast in 2021 and still sit well below where it was supposed to be."
)
st.markdown(
    "**Forecast error** = actual growth minus forecast growth, in percentage points (pp). Negative means "
    "reality came in below the IMF's October 2019 forecast. The forecast is a *benchmark*, not a measure of "
    "what the world would have looked like without the pandemic."
)

st.header("How the story unfolds")
st.markdown(
    "| Chapter | Question |\n|---|---|\n"
    "| **1. The future we expected** | How far did growth fall from the IMF forecast, country by country? |\n"
    "| **2. The shock hits** | What did the pandemic look like in deaths and vaccination, and did the health "
    "toll line up with the economic shortfall? |\n"
    "| **3. Governments make their choices** | How strict were restrictions and how much support was recorded? |\n"
    "| **4. Not every country starts with the same cards** | Which structural vulnerabilities came before the shock? |\n"
    "| **5. The recovery wasn't equal** | Who returned to the expected path, and who did not? |\n"
    "| **Conclusion** | What the evidence supports, and what it cannot show. |"
)
st.caption("Use the menu on the left to move between chapters.")

st.header("The 11 countries")
chips = " ".join(
    f"<span style='display:inline-block;margin:2px 6px 2px 0;padding:3px 10px;border-radius:12px;"
    f"background:{colour};color:white;font-size:0.9rem'>{name}</span>"
    for name, colour in COUNTRY_COLOURS.items()
)
st.markdown(chips, unsafe_allow_html=True)
st.caption("Each country keeps the same colour in every chart of the dashboard.")

st.header("Data")
sources = pd.DataFrame([
    ("Actual GDP growth", "World Bank WDI (NY.GDP.MKTP.KD.ZG)", "2010-2022, annual"),
    ("Pre-pandemic forecast", "IMF World Economic Outlook, October 2019", "2019-2022 used, annual"),
    ("Cases, deaths, vaccination", "Our World in Data", "2020-2022, daily"),
    ("Policy stringency and economic support", "Oxford COVID-19 Government Response Tracker", "2020-2022, daily"),
    ("Structural vulnerabilities", "World Bank WDI (tourism, trade, services, oil rents)", "2019"),
], columns=["Topic", "Source", "Coverage"])
st.dataframe(sources, hide_index=True, use_container_width=True)

st.header("How to read the charts")
st.markdown(
    "- **Descriptive, not causal.** With 11 countries we describe patterns; we do not prove that one factor "
    "caused another.\n"
    "- **Missing is not zero.** Where a value does not exist (for example tourism receipts for Spain, Sweden "
    "and China, or vaccination before the rollout) it is shown as unavailable.\n"
    "- **Reported figures differ from reality.** Cases and deaths depend on testing and registration; GDP "
    "estimates can be revised after the forecast.\n"
    "- **Outliers are flagged.** Saudi Arabia's 2022 growth (12.0%) is an outlier in the source data."
)
