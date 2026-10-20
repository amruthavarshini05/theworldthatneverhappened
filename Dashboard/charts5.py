"""Pure figure functions for Chapter 5 - "The recovery wasn't equal" (no Streamlit inside).

Chart 1: recovery trajectories (growth 2019-2022 vs the IMF forecast, optional pre-COVID band).
Chart 2: recovery-gap ranking (accumulated output vs the IMF-expected path, or vs 2019).
"""
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from charts import FADE_BARS, TEMPLATE, _sign, empty_figure, hex_to_rgba
from data import ABOVE_COLOUR, BELOW_COLOUR, COUNTRY_COLOURS

NO_COUNTRY = "Select at least one country."

# Fixed x-axis ranges for the ranking (easy to change). Fixed so that 2020, 2021 and 2022
# can be compared by eye: if the axis rescaled each year, a bar of the same length would
# mean different things and the recovery over time would be invisible.
GAP_RANGE = (-14, 9)           # metric 1: output gap vs IMF-expected path (%)
VS2019_RANGE = (-13, 17)       # metric 2: output vs 2019 level (%)

METRICS = {
    "Output gap vs IMF-expected path (%)": dict(
        col="output_gap_vs_imf_pct", range=GAP_RANGE,
        note="How far output is from where the IMF expected it to be (both indices start at 100 in 2019)."),
    "Output vs 2019 level (%)": dict(
        col="output_vs_2019_pct", range=VS2019_RANGE,
        note="How far output is from where it was in 2019. Descriptive only: it does not use the forecast."),
}
DEFAULT_METRIC = "Output gap vs IMF-expected path (%)"


def _keep(countries):
    return [c for c in countries if c in COUNTRY_COLOURS]


# --------------------------------------------------------------------------
# CHART 1 - recovery trajectories
# --------------------------------------------------------------------------
def _shade(fig, **kw):
    """COVID-shock band (2020) and recovery band (2021-2022); kw = row/col for subplots."""
    fig.add_vrect(x0=2019.5, x1=2020.5, fillcolor="grey", opacity=0.15, line_width=0, layer="below", **kw)
    fig.add_vrect(x0=2020.5, x1=2022.5, fillcolor="#9ecae1", opacity=0.18, line_width=0, layer="below", **kw)


def band_available(countries, view) -> bool:
    """The typical-range band differs per country, so in the 'Together' view it is only
    drawn for exactly one country; in small multiples every panel has its own band."""
    n = len(_keep(countries))
    return n >= 1 if view == "Small multiples" else n == 1


def trajectories_figure(df, countries, show_forecast=True, show_band=False, view="Together"):
    countries = _keep(countries)
    if not countries:
        return empty_figure(NO_COUNTRY)
    show_band = bool(show_band) and band_available(countries, view)
    title = "GDP growth 2019-2022: rebound versus the pre-COVID forecast"

    def custom(g):
        return np.column_stack([g["imf_gdp_growth_pct"], g["forecast_error_pp"]])

    actual_hover = ("<b>{c}</b><br>Year: %{{x}}<br>Actual growth: %{{y:.1f}}%"
                    "<br>IMF forecast: %{{customdata[0]:.1f}}%"
                    "<br>Error: %{{customdata[1]:+.1f}} pp<extra></extra>")

    if view == "Small multiples":
        ncols = min(4, len(countries))
        nrows = math.ceil(len(countries) / ncols)
        fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=countries, shared_xaxes=True,
                            vertical_spacing=0.16 if nrows > 1 else 0.1, horizontal_spacing=0.06)
        for k, c in enumerate(countries):
            r, col = k // ncols + 1, k % ncols + 1
            g = df[df["country"] == c].sort_values("year")
            first = k == 0
            _shade(fig, row=r, col=col)
            if show_band:
                fig.add_hrect(y0=g["band_low_pct"].iloc[0], y1=g["band_high_pct"].iloc[0],
                              fillcolor=COUNTRY_COLOURS[c], opacity=0.15, line_width=0, row=r, col=col)
            fig.add_trace(go.Scatter(
                x=g["year"], y=g["gdp_growth_pct"], mode="lines+markers", name="Actual", legendgroup="a",
                showlegend=first, line=dict(color="#222222", width=2), marker=dict(size=6),
                customdata=custom(g), hovertemplate=actual_hover.format(c=c)), row=r, col=col)
            if show_forecast:
                fig.add_trace(go.Scatter(
                    x=g["year"], y=g["imf_gdp_growth_pct"], mode="lines", name="IMF forecast (Oct 2019)",
                    legendgroup="f", showlegend=first,
                    line=dict(color=COUNTRY_COLOURS[c], width=2, dash="dash"),
                    hovertemplate=f"<b>{c}</b><br>Year: %{{x}}<br>IMF forecast: %{{y:.1f}}%<extra></extra>"),
                    row=r, col=col)
            fig.add_hline(y=0, line_width=1, line_color="grey", row=r, col=col)
        fig.update_xaxes(tickvals=[2019, 2020, 2021, 2022], range=[2018.7, 2022.3])
        fig.update_yaxes(title_text="Growth (%)", col=1)
        fig.update_layout(template=TEMPLATE, title=title, height=300 * nrows + 130,
                          legend=dict(orientation="h", y=-0.12), font=dict(size=12))
        return fig

    # ---- Together ----
    fig = go.Figure()
    _shade(fig)
    if show_band:
        g0 = df[df["country"] == countries[0]].iloc[0]
        fig.add_hrect(y0=g0["band_low_pct"], y1=g0["band_high_pct"],
                      fillcolor=COUNTRY_COLOURS[countries[0]], opacity=0.15, line_width=0)
        fig.add_annotation(x=2019.55, y=g0["band_high_pct"], xanchor="left", yanchor="bottom",
                           showarrow=False, text="Typical 2012-2019 range (mean ± 1 SD)",
                           font=dict(size=11, color="#555"))
    for c in countries:
        g = df[df["country"] == c].sort_values("year")
        colour = COUNTRY_COLOURS[c]
        fig.add_trace(go.Scatter(
            x=g["year"], y=g["gdp_growth_pct"], mode="lines+markers", name=c, legendgroup=c,
            line=dict(color=colour, width=2.5), marker=dict(size=8), customdata=custom(g),
            hovertemplate=actual_hover.format(c=c)))
        if show_forecast:
            fig.add_trace(go.Scatter(
                x=g["year"], y=g["imf_gdp_growth_pct"], mode="lines", name=f"{c} - IMF forecast",
                legendgroup=c, showlegend=False, line=dict(color=colour, width=2, dash="dash"),
                hovertemplate=f"<b>{c}</b><br>Year: %{{x}}<br>IMF forecast: %{{y:.1f}}%<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color="grey")
    fig.add_annotation(x=2020, y=1, yref="paper", text="COVID shock", showarrow=False, yanchor="top",
                       font=dict(size=12, color="#444"))
    fig.add_annotation(x=2021.5, y=1, yref="paper", text="Recovery period", showarrow=False, yanchor="top",
                       font=dict(size=12, color="#3b6e8f"))
    fig.update_xaxes(title_text="Year", tickvals=[2019, 2020, 2021, 2022], range=[2018.7, 2022.3])
    fig.update_yaxes(title_text="Annual real GDP growth (%)", zeroline=False)
    fig.update_layout(template=TEMPLATE, title=title, height=560, hovermode="closest",
                      legend_title_text="Country", font=dict(size=13))
    return fig


def trajectories_caption(df, countries) -> str:
    countries = _keep(countries)
    if not countries:
        return ""
    n = len(countries)
    d = df[df["country"].isin(countries)]
    n21 = int((d[d["year"] == 2021]["forecast_error_pp"] > 0).sum())
    n22 = int((d[d["year"] == 2022]["forecast_error_pp"] > 0).sum())
    return (f"In 2021, {n21} of {n} selected countries grew faster than the IMF expected; "
            f"in 2022, {n22} of {n}.")


# --------------------------------------------------------------------------
# CHART 2 - recovery-gap ranking
# --------------------------------------------------------------------------
def rank_data(df, year, metric=DEFAULT_METRIC) -> pd.DataFrame:
    col = METRICS[metric]["col"]
    d = df[df["year"] == year].dropna(subset=[col])
    return d.sort_values(col).reset_index(drop=True)      # most negative first


def _plural(n, singular, plural):
    return singular if n == 1 else plural


def rank_title(d, year, metric=DEFAULT_METRIC) -> str:
    n = len(d)
    if n == 0:
        return f"{year}: no data"
    if metric == DEFAULT_METRIC:
        k = int((d["output_gap_vs_imf_pct"] >= 0).sum())
        if k == 0:
            return f"{year}: all {n} countries were below their expected path"
        if k == n:
            return f"{year}: all {n} countries were on or above their expected path"
        lead = "only " if k <= n / 2 else ""
        if year == 2022:
            return f"{year}: {lead}{k} of {n} countries ended above their expected path"
        verb = _plural(k, "was", "were")
        poss = _plural(k, "its", "their")
        return f"{year}: {lead}{k} of {n} countries {verb} back on {poss} expected path"
    k = int(d["above_2019_level"].sum())
    if k == 0:
        return f"{year}: none of the {n} countries was above its 2019 output level"
    if k == n:
        return f"{year}: all {n} countries were above their 2019 output level"
    lead = "only " if k <= n / 2 else ""
    verb = _plural(k, "was", "were")
    poss = _plural(k, "its", "their")
    return f"{year}: {lead}{k} of {n} countries {verb} above {poss} 2019 output level"


def rank_caption(d, year, metric=DEFAULT_METRIC) -> str:
    base = ("Positive bars mean output has overtaken the path the IMF expected before COVID; "
            "negative bars mean output is still below it."
            if metric == DEFAULT_METRIC else
            "Positive bars mean output is above its 2019 level; negative bars mean it is still below.")
    col = METRICS[metric]["col"]
    worst = d.nsmallest(2, col)
    worst = worst[worst[col] < 0]
    if len(worst) == 2:
        a, b = sorted(worst["country"])            # alphabetical, e.g. "India and Thailand"
        names = f"{a} and {b}"
        extra = f" {names} show the largest {'lasting ' if year == 2022 else ''}gaps in {year}."
    elif len(worst) == 1:
        extra = f" {worst.iloc[0]['country']} shows the only negative value in {year}."
    else:
        extra = f" No country is below the benchmark in {year}."
    return base + extra


def rank_figure(df, year, metric=DEFAULT_METRIC, highlight=None) -> go.Figure:
    d = rank_data(df, year, metric)
    if d.empty:
        return empty_figure("No data for this year.")
    col, xr = METRICS[metric]["col"], METRICS[metric]["range"]
    vals = d[col]
    colours = [BELOW_COLOUR if v < 0 else ABOVE_COLOUR for v in vals]
    opac = [FADE_BARS if (highlight and c != highlight) else 1.0 for c in d["country"]]
    lw = [2.5 if (highlight and c == highlight) else 0 for c in d["country"]]
    regained = np.where(d["above_2019_level"], "yes", "no")
    custom = np.column_stack([d["actual_index"], d["imf_expected_index"], d["output_gap_vs_imf_pct"],
                              d["output_vs_2019_pct"], regained, d["rank_output_gap_in_year_1_worst"]])
    fig = go.Figure(go.Bar(
        x=vals, y=d["country"], orientation="h",
        marker=dict(color=colours, opacity=opac, line=dict(color="#111111", width=lw)),
        text=[_sign(v) for v in vals], textposition="outside", cliponaxis=False, customdata=custom,
        hovertemplate=("<b>%{y}</b><br>Actual index: %{customdata[0]:.1f} (2019 = 100)"
                       "<br>IMF-expected index: %{customdata[1]:.1f}"
                       "<br>Output gap vs expected path: %{customdata[2]:+.1f}%"
                       "<br>Output vs 2019 level: %{customdata[3]:+.1f}%"
                       "<br>Regained 2019 level? %{customdata[4]}"
                       "<br>Rank (1 = furthest below expected path): %{customdata[5]:.0f}<extra></extra>"),
    ))
    # Plotly draws the FIRST category at the bottom. autorange="reversed" flips the axis so the
    # first row (most negative value, because we sorted ascending) is shown at the TOP.
    fig.update_yaxes(categoryorder="array", categoryarray=list(d["country"]), autorange="reversed",
                     title_text="")
    fig.update_xaxes(title_text=metric, range=list(xr), zeroline=False)
    fig.add_vline(x=0, line_width=1.5, line_color="black")
    if year == 2022 and "Saudi Arabia" in set(d["country"]):
        v = float(d.loc[d["country"] == "Saudi Arabia", col].iloc[0])
        # put the note on the empty side of the zero line, next to the Saudi Arabia bar
        fig.add_annotation(x=-0.3 if v >= 0 else 0.3, y="Saudi Arabia", xanchor="right" if v >= 0 else "left",
                           showarrow=False, text="Outlier in source data, interpret with caution",
                           font=dict(size=11, color="#555"))
    fig.update_layout(template=TEMPLATE, title=rank_title(d, year, metric), height=520, showlegend=False,
                      font=dict(size=13), margin=dict(l=20, r=40))
    return fig
