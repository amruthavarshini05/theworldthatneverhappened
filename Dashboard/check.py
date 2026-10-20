"""Self-check: compare the data in the figures with the verification table.

Run:  python check.py
The data-layer checks need only pandas. The figure-level checks need plotly
and are skipped (with a message) if it is not installed.
"""
import numpy as np

from data import load_data

# Verification table (2020): country -> (imf forecast, actual, error)
TABLE_2020 = {
    "Brazil": (2.04, -3.28, -5.32), "China": (5.82, 2.34, -3.48), "Germany": (1.25, -4.13, -5.38),
    "India": (7.03, -5.78, -12.81), "Saudi Arabia": (2.18, -3.80, -5.99),
    "South Africa": (1.08, -6.17, -7.25), "South Korea": (2.22, -0.70, -2.92),
    "Spain": (1.85, -10.94, -12.79), "Sweden": (1.46, -1.93, -3.40),
    "Thailand": (3.01, -6.09, -9.10), "United States": (2.09, -2.08, -4.17),
}
TOL = 0.01


def close(a, b):
    return abs(a - b) <= TOL


def main():
    df = load_data()
    ok = True

    def report(label, passed):
        nonlocal ok
        ok &= bool(passed)
        print(f"[{'OK' if passed else 'FAIL'}] {label}")

    report("143 rows, 11 countries, 44 forecast rows",
           len(df) == 143 and df.ISO3.nunique() == 11 and df.forecast_error_pp.notna().sum() == 44)
    report("no forecast before 2019", df.loc[df.year < 2019, "imf_gdp_growth_pct"].isna().all())

    # Independent recomputation of the error
    recomputed = df["gdp_growth_pct"] - df["imf_gdp_growth_pct"]
    report("forecast_error_pp equals actual - forecast (independent recompute)",
           np.allclose(recomputed.dropna(), df["forecast_error_pp"].dropna())
           and recomputed.isna().equals(df["forecast_error_pp"].isna()))

    d20 = df[df.year == 2020].set_index("country")
    for c, (f, a, e) in TABLE_2020.items():
        r = d20.loc[c]
        report(f"2020 {c}: forecast {r.imf_gdp_growth_pct:.2f} / actual {r.gdp_growth_pct:.2f} / "
               f"error {r.forecast_error_pp:.2f}",
               close(r.imf_gdp_growth_pct, f) and close(r.gdp_growth_pct, a) and close(r.forecast_error_pp, e))

    d21 = df[df.year == 2021]
    below21 = d21[d21.forecast_error_pp < 0]
    report("2021: only Thailand below forecast (1.56 vs 3.49, -1.93)",
           list(below21.country) == ["Thailand"] and close(below21.iloc[0].gdp_growth_pct, 1.56)
           and close(below21.iloc[0].imf_gdp_growth_pct, 3.49) and close(below21.iloc[0].forecast_error_pp, -1.93))
    d22 = df[df.year == 2022].set_index("country")
    # The brief quotes these errors to 1 decimal, so compare at that precision.
    report("2022: Saudi Arabia error +9.6, China error -2.6 (1 decimal)",
           round(d22.loc["Saudi Arabia", "forecast_error_pp"], 1) == 9.6
           and round(d22.loc["China", "forecast_error_pp"], 1) == -2.6)
    # The brief's component figures differ slightly from the CSVs; the CSVs are the source of truth.
    s, ch = d22.loc["Saudi Arabia"], d22.loc["China"]
    print(f"[NOTE] 2022 CSV values: Saudi Arabia {s.gdp_growth_pct:.2f} vs forecast {s.imf_gdp_growth_pct:.3f} "
          f"(brief says 12.00 vs 2.37); China {ch.gdp_growth_pct:.3f} vs {ch.imf_gdp_growth_pct:.2f} "
          f"(brief says 3.15 vs 5.70)")
    report("2020: rank 1 = India (largest negative surprise)",
           d20.loc["India", "rank_in_year_1_worst"] == 1)

    # Lowest-growth-year claim: 2020 for everyone except Brazil
    low = {c: int(g.loc[g.gdp_growth_pct.idxmin(), "year"]) for c, g in df.groupby("country")}
    report("2020 is the lowest year for every country except Brazil",
           all(y == 2020 for c, y in low.items() if c != "Brazil") and low["Brazil"] != 2020)

    # ---- Figure-level checks (need plotly) ----
    try:
        import plotly  # noqa: F401
    except ImportError:
        print("[SKIP] figure-level checks: plotly is not installed in this environment")
        print("ALL DATA CHECKS PASSED" if ok else "SOME CHECKS FAILED")
        raise SystemExit(0 if ok else 1)

    from charts import (benchmark_2019_line, error_figure, lowest_year_fact, slope_figure,
                        slope_title, slope_data, timeline_figure, error_title, error_data)

    fig = slope_figure(df, 2020)
    pts = {t.name: t.y for t in fig.data}
    report("slope chart 2020: 11 lines, each (forecast, actual) matches the table",
           len(pts) == 11 and all(close(pts[c][0], f) and close(pts[c][1], a) for c, (f, a, _) in TABLE_2020.items()))
    report("slope title 2020", fig.layout.title.text == "2020: all 11 countries grew less than the IMF expected")
    report("slope title 2021", slope_title(slope_data(df, 2021), 2021) == "2021: 10 of 11 countries grew more than the IMF expected")

    bar = error_figure(df, 2020).data[0]
    xs = dict(zip(bar.y, bar.x))
    report("error bars 2020 match the table",
           all(close(xs[c], e) for c, (_, _, e) in TABLE_2020.items()))
    report("error bars 2020 sorted most negative first (India on top)", bar.y[0] == "India")
    report("error title 2020",
           error_figure(df, 2020).layout.title.text == "2020: every country fell short of its pre-COVID forecast, by 6.6 pp on average")
    report("error title 2021",
           error_figure(df, 2021).layout.title.text == "2021: 10 of 11 countries beat the forecast, by 2.7 pp on average")
    report("2019 benchmark = 0.75 pp", "0.75 pp" in benchmark_2019_line(df))
    report("fixed x range", tuple(error_figure(df, 2021).layout.xaxis.range) == (-16, 12))

    tl = timeline_figure(df, ["Spain", "India"], True, "Together")
    fc = [t for t in tl.data if t.line.dash == "dash"]
    report("timeline: forecast overlay only 2019-2022", all(min(t.x) == 2019 and max(t.x) == 2022 for t in fc))
    report("timeline: overlay can be switched off",
           not [t for t in timeline_figure(df, ["Spain"], False, "Together").data if t.line.dash == "dash"])
    report("timeline: small multiples builds", len(timeline_figure(df, ["Spain", "India", "China"], True, "Small multiples").data) == 6)
    report("timeline: empty selection returns a friendly figure",
           "Select at least one country" in timeline_figure(df, [], True, "Together").layout.annotations[0].text)
    report("fact text names Brazil as exception", "Brazil" in lowest_year_fact(df, ["Brazil", "Spain"]))

    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
