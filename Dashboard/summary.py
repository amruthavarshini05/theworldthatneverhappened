"""Headline numbers for the introduction and conclusion pages.

Everything is computed from the data files (nothing typed by hand), so the text can never
drift away from the charts. No Streamlit and no Plotly in this module: easy to test.
"""
from data import (context_correlations, load_data, load_health, load_policy, load_recovery_data,
                  load_vulnerability, mortality_economy, policy_country_avg, spearman_table)


def compute_headlines() -> dict:
    df, rec, vul = load_data(), load_recovery_data(), load_vulnerability()
    me = mortality_economy(load_health(), df)
    avg = policy_country_avg(load_policy()).set_index("country")
    err = df.dropna(subset=["forecast_error_pp"])
    by_year = err.groupby("year")["forecast_error_pp"]

    y22 = rec[rec["year"] == 2022].set_index("country")
    worst2 = y22["output_gap_vs_imf_pct"].nsmallest(2)
    y20 = df[df["year"] == 2020].set_index("country")["forecast_error_pp"]
    rho20 = spearman_table(vul, "shortfall_2020")
    ctx = context_correlations(vul)
    inc = vul.groupby("income_group")["level_gap_2022"].mean()

    return {
        "n_countries": df["ISO3"].nunique(),
        "mean_err": by_year.mean().to_dict(),                                  # {2019:.., 2020:.., ...}
        "n_below": {y: int((g < 0).sum()) for y, g in by_year},
        "n_above": {y: int((g > 0).sum()) for y, g in by_year},
        "worst_2020": y20.nsmallest(2).to_dict(),                              # two largest 2020 misses
        "above_path_2022": sorted(y22.index[y22["above_imf_path"]]),
        "below_2019_2022": sorted(y22.index[~y22["above_2019_level"]]),
        "n_below_path_2022": int((~y22["above_imf_path"]).sum()),
        "worst_gap_2022": worst2.to_dict(),                                    # {country: gap %}
        "corr_deaths_growth": float(me["avg_daily_deaths_per_million"].corr(me["gdp_growth_pct"])),
        "corr_deaths_error": float(me["avg_daily_deaths_per_million"].corr(me["forecast_error_pp"])),
        "n_obs_mortality": len(me),
        "stringency_max": (avg["avg_stringency"].idxmax(), float(avg["avg_stringency"].max())),
        "stringency_min": (avg["avg_stringency"].idxmin(), float(avg["avg_stringency"].min())),
        "support_max": (avg["avg_economic_support"].idxmax(), float(avg["avg_economic_support"].max())),
        "rho_tourism": (float(rho20.loc["tourism_receipts_pct_exports", "spearman_rho"]),
                        int(rho20.loc["tourism_receipts_pct_exports", "n"])),
        "n_significant": int((rho20["p_value"] < 0.05).sum()),
        "rho_travel_controls": float(ctx["travel_controls_2020"]),
        "income_gap_2022": inc.to_dict(),
    }
