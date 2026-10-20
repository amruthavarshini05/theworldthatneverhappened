"""Conclusion page: the findings of all chapters, with numbers computed from the data."""
import streamlit as st

from charts5 import rank_figure
from data import load_recovery_data
from summary import compute_headlines


@st.cache_data
def get_tables():
    return compute_headlines(), load_recovery_data()


h, rec = get_tables()
me = h["mean_err"]


def names(items):
    items = list(items)
    return ", ".join(items[:-1]) + f" and {items[-1]}" if len(items) > 1 else (items[0] if items else "none")


st.title("Conclusion")
st.subheader("What the evidence supports, and what it cannot show")

c1, c2, c3 = st.columns(3)
c1.metric("Countries below forecast in 2020", f"{h['n_below'][2020]} of {h['n_countries']}",
          help=f"Mean miss {me[2020]:+.1f} pp")
c2.metric("Above the expected path in 2022", f"{len(h['above_path_2022'])} of {h['n_countries']}",
          help=names(h["above_path_2022"]))
c3.metric("Correlation: deaths vs forecast error", f"{h['corr_deaths_error']:+.2f}",
          help=f"{h['n_obs_mortality']} country-year observations")

st.header("Five findings")
w2 = h["worst_2020"]
(g1, v1), (g2, v2) = h["worst_gap_2022"].items()
st.markdown(
    f"**1. A widespread shock.** In 2020 {h['n_below'][2020]} of {h['n_countries']} countries grew less than the "
    f"IMF expected, by {me[2020]:+.1f} pp on average. The largest misses were "
    f"{names(f'{c} ({x:+.1f} pp)' for c, x in w2.items())}.\n\n"
    f"**2. A rebound is not a recovery.** In 2021 {h['n_above'][2021]} of {h['n_countries']} countries beat the "
    f"forecast ({me[2021]:+.1f} pp on average), yet in 2022 {h['n_below_path_2022']} of {h['n_countries']} were "
    f"still below the *level* the IMF had expected. Only {names(h['above_path_2022'])} ended above their expected "
    f"path, and {names(h['below_2019_2022'])} "
    f"{'was' if len(h['below_2019_2022']) == 1 else 'were'} still below 2019 output.\n\n"
    f"**3. The health toll did not line up with the economic shortfall.** Across {h['n_obs_mortality']} "
    f"country-years, reported deaths per million had a correlation of {h['corr_deaths_error']:+.2f} with the "
    f"forecast error and {h['corr_deaths_growth']:+.2f} with GDP growth: very weak.\n\n"
    f"**4. Policy choices differed widely.** Average stringency in 2020-2022 ranged from "
    f"{h['stringency_min'][1]:.0f} ({h['stringency_min'][0]}) to {h['stringency_max'][1]:.0f} "
    f"({h['stringency_max'][0]}); reported economic support was highest in {h['support_max'][0]} "
    f"({h['support_max'][1]:.0f}). Neither stringency nor support alone explains who suffered most.\n\n"
    f"**5. Structure predisposes but does not condemn.** Of the four structural vulnerabilities, "
    f"{h['n_significant']} showed a statistically significant link with the 2020 shock. Tourism had the most "
    f"consistent sign (rho = {h['rho_tourism'][0]:+.2f}, n = {h['rho_tourism'][1]}, Spain missing), and "
    f"international travel controls correlated at {h['rho_travel_controls']:+.2f}."
)

st.header("The final picture")
st.plotly_chart(rank_figure(rec, 2022), use_container_width=True, key="concl-rank-chart")
st.caption(f"Output at end-2022 versus the path expected in October 2019. {g1} ({v1:+.1f}%) and {g2} "
           f"({v2:+.1f}%) show the largest lasting gaps. Saudi Arabia's 2022 growth is an outlier in the "
           "source data.")

st.header("Income and the road ahead")
inc = h["income_gap_2022"]
st.markdown(
    "Lower-income groups ended further from their expected path: by end-2022 the average output gap was "
    + ", ".join(f"{x:+.1f}% for {k.lower()} countries" for k, x in inc.items())
    + ". The lower-middle-income group is India alone, and Saudi Arabia's oil boom lifts the high-income "
    "average, so read this as an illustration rather than a rule."
)

st.header("What this dashboard cannot show")
st.markdown(
    "- **No causal claims.** The forecast is a benchmark, not a counterfactual; a gap also reflects oil prices, "
    "the war in Ukraine and slowdowns already under way (India was 2.3 pp below forecast in 2019).\n"
    "- **Small panel.** Eleven countries cannot be generalised to the world, and correlations are fragile "
    "(one country can create or destroy them).\n"
    "- **Imperfect data.** Reported deaths depend on testing and registration; tourism data is missing for Spain, "
    "Sweden and China; GDP estimates can be revised.\n"
    "- **Averages hide timing.** When restrictions were introduced, and how long they lasted, matters as "
    "much as their average strictness."
)
st.caption("Sources: IMF World Economic Outlook (October 2019); World Bank WDI; Our World in Data; "
           "OxCGRT. Indices, gaps and correlations are our own calculations.")
