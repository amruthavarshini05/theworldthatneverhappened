"""Self-check for chapters 2 and 3: compare computed tables with the figures in the notebooks.

Run: python check2_3.py   (pandas only; figure-level checks run too if plotly is installed)
"""
import numpy as np

from data import (health_monthly_deaths, load_data, load_health, load_policy, mortality_economy,
                  policy_country_avg, policy_monthly, tradeoff_2020, vaccination_monthly)

ok = True


def report(label, passed):
    global ok
    ok &= bool(passed)
    print(f"[{'OK' if passed else 'FAIL'}] {label}")


def close(a, b, tol=0.01):
    return abs(a - b) <= tol


df, h, p = load_data(), load_health(), load_policy()
me = mortality_economy(h, df)

# ---- Chapter 2 ----
r1 = me["avg_daily_deaths_per_million"].corr(me["gdp_growth_pct"])
r2 = me["avg_daily_deaths_per_million"].corr(me["forecast_error_pp"])
report(f"33 country-year rows (got {len(me)})", len(me) == 33)
report(f"corr deaths~GDP growth = -0.11 (got {r1:.3f})", close(r1, -0.11, 0.005))
report(f"corr deaths~forecast error = +0.073 (got {r2:.3f})", close(r2, 0.073, 0.0005))
by_year = {y: g["avg_daily_deaths_per_million"].corr(g["forecast_error_pp"]) for y, g in me.groupby("year")}
report("by-year correlations -0.033 / +0.230 / -0.102",
       close(by_year[2020], -0.033, 0.001) and close(by_year[2021], 0.230, 0.001) and close(by_year[2022], -0.102, 0.001))
m = df.dropna(subset=["forecast_error_pp"]).groupby("year")["forecast_error_pp"].mean()
report("mean forecast error 2019-2022 = +0.08 / -6.60 / +2.73 / +1.13",
       all(close(m[y], v) for y, v in {2019: 0.08, 2020: -6.60, 2021: 2.73, 2022: 1.13}.items()))
report("2021: 10 of 11 above forecast", int((df[df.year == 2021].forecast_error_pp > 0).sum()) == 10)
report("largest 2022 error: Saudi Arabia +9.60", df[df.year == 2022].set_index("country").forecast_error_pp.idxmax() == "Saudi Arabia")
hm = health_monthly_deaths(h)
vm = vaccination_monthly(h)
report("monthly deaths: 396 rows (11 x 36)", len(hm) == 396)
report("vaccination: missing is not zero (no NaN rows kept, fewer than 396 months)", vm.iloc[:, -1].notna().all() and len(vm) < 396)
months = vm.groupby("country").size()
report("vaccination sparse series flagged by the <20-month rule: China (17) and Saudi Arabia (9) only",
       sorted(months[months < 20].index) == ["China", "Saudi Arabia"])

# ---- Chapter 3 ----
pm, avg, tr = policy_monthly(p), policy_country_avg(p).set_index("country"), tradeoff_2020(p, df).set_index("country")
report("monthly policy table: 396 rows", len(pm) == 396)
nb_avg = {"China": (73.31, 51.22), "Sweden": (36.69, 28.11), "Spain": (44.96, 62.16),
          "Germany": (44.04, 56.14), "Thailand": (42.96, 54.95), "Brazil": (48.54, 15.66)}
report("country averages 2020-2022 match notebook",
       all(close(avg.loc[c, "avg_stringency"], s) and close(avg.loc[c, "avg_economic_support"], e) for c, (s, e) in nb_avg.items()))
report("highest stringency China, lowest Sweden; top support Spain > Germany > Thailand",
       avg.avg_stringency.idxmax() == "China" and avg.avg_stringency.idxmin() == "Sweden"
       and list(avg.avg_economic_support.nlargest(3).index) == ["Spain", "Germany", "Thailand"])
nb_2020 = {"Spain": (56.27, 68.03, -10.94), "South Africa": (54.49, 47.06, -6.17), "Thailand": (46.12, 69.47, -6.09),
           "India": (64.77, 48.84, -5.78), "Germany": (51.81, 35.76, -4.13), "Saudi Arabia": (57.21, 46.07, -3.80),
           "Brazil": (57.51, 37.02, -3.28), "United States": (57.11, 47.81, -2.08), "Sweden": (49.01, 40.10, -1.93),
           "South Korea": (49.43, 38.73, -0.70), "China": (68.27, 28.72, 2.34)}
report("2020 trade-off table (11 rows) matches notebook",
       all(close(tr.loc[c, "avg_stringency"], s) and close(tr.loc[c, "avg_economic_support"], e)
           and close(tr.loc[c, "gdp_growth_pct"], g) for c, (s, e, g) in nb_2020.items()))

# ---- Figure-level (needs plotly) ----
try:
    import plotly  # noqa: F401
except ImportError:
    print("[SKIP] figure-level checks: plotly is not installed in this environment")
else:
    from charts2 import (deaths_figure, error_heatmap_figure, gdp_growth_figure, mortality_error_figure,
                         mortality_growth_figure, vaccination_figure)
    from charts3 import bubble_figure, grouped_bar_figure, stringency_figure, support_figure
    allc = sorted(df.country.unique())
    figs = [gdp_growth_figure(df, allc), error_heatmap_figure(df, allc), deaths_figure(hm, allc),
            vaccination_figure(vm, allc), mortality_growth_figure(me, allc, [2020, 2021, 2022]),
            mortality_error_figure(me, allc, [2020, 2021, 2022]), stringency_figure(pm, allc),
            support_figure(pm, allc), grouped_bar_figure(avg.reset_index(), allc), bubble_figure(tr.reset_index(), allc)]
    report("all 10 figures build", all(f is not None for f in figs))
    report("empty selection gives a friendly message (no error)",
           "Select at least one" in gdp_growth_figure(df, []).layout.annotations[0].text
           and "Select at least one" in bubble_figure(tr.reset_index(), []).layout.annotations[0].text)

print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
raise SystemExit(0 if ok else 1)
