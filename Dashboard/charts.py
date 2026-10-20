"""Pure figure functions for Chapter 1 (no Streamlit inside, so they can be tested alone).

Each chart has:
  * a *_figure(df, ...) function returning a plotly Figure
  * small helpers returning the dynamic title / caption / facts as plain strings
"""
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data import ABOVE_COLOUR, BELOW_COLOUR, COUNTRY_COLOURS

TEMPLATE = "plotly_white"
ERROR_X_RANGE = (-16, 12)      # fixed axis for the bar chart (easy to change)
FADE_SLOPE = 0.25              # opacity of non-highlighted lines
FADE_BARS = 0.30               # opacity of non-highlighted bars


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def hex_to_rgba(hex_colour: str, alpha: float) -> str:
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def empty_figure(message: str) -> go.Figure:
    """Friendly placeholder instead of an error (e.g. nothing selected)."""
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font=dict(size=16, color="#666"))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(template=TEMPLATE, height=300)
    return fig


def deoverlap(values, min_gap: float) -> np.ndarray:
    """Vertical de-overlap for labels.

    Sort by y, push each label up until it is at least `min_gap` above the
    previous one, then re-centre the group so labels stay close to their
    true positions. Returns positions in the ORIGINAL order.
    """
    values = np.asarray(values, dtype=float)
    order = np.argsort(values)
    y = values[order]
    adj = y.copy()
    for i in range(1, len(adj)):
        adj[i] = max(adj[i], adj[i - 1] + min_gap)
    adj += y.mean() - adj.mean()
    out = np.empty_like(adj)
    out[order] = adj
    return out


def _sign(x: float) -> str:
    return f"{x:+.1f}"


# --------------------------------------------------------------------------
# CHART 1 - slope chart
# --------------------------------------------------------------------------
def slope_data(df: pd.DataFrame, year: int) -> pd.DataFrame:
    d = df[df["year"] == year].dropna(subset=["imf_gdp_growth_pct"])
    return d.sort_values("country").reset_index(drop=True)


def slope_title(d: pd.DataFrame, year: int) -> str:
    n = len(d)
    below = int((d["forecast_error_pp"] < 0).sum())
    above = int((d["forecast_error_pp"] > 0).sum())
    if n == 0:
        return f"{year}: no forecast available"
    if below == n:
        return f"{year}: all {n} countries grew less than the IMF expected"
    if above == n:
        return f"{year}: all {n} countries grew more than the IMF expected"
    if below >= above:
        return f"{year}: {below} of {n} countries grew less than the IMF expected"
    return f"{year}: {above} of {n} countries grew more than the IMF expected"


def slope_caption(d: pd.DataFrame) -> str:
    n = len(d)
    below = int((d["forecast_error_pp"] < 0).sum())
    mean = d["forecast_error_pp"].mean()
    worst = d.loc[d["forecast_error_pp"].idxmin()]
    best = d.loc[d["forecast_error_pp"].idxmax()]
    return (
        f"{below} of {n} countries grew below the forecast; mean error {_sign(mean)} pp. "
        f"Worst: {worst['country']} ({_sign(worst['forecast_error_pp'])} pp). "
        f"Best: {best['country']} ({_sign(best['forecast_error_pp'])} pp). "
        "Steeper downward lines mean larger negative surprises."
    )


def slope_figure(df: pd.DataFrame, year: int, highlight=None) -> go.Figure:
    d = slope_data(df, year)
    if d.empty:
        return empty_figure("No forecast available for this year.")

    fig = go.Figure()
    for _, r in d.iterrows():
        name = r["country"]
        colour = COUNTRY_COLOURS[name]
        faded = bool(highlight) and name != highlight
        thick = bool(highlight) and name == highlight
        alpha = FADE_SLOPE if faded else 1.0
        hover = (
            f"<b>{name}</b><br>IMF forecast: {r['imf_gdp_growth_pct']:.1f}%"
            f"<br>Actual: {r['gdp_growth_pct']:.1f}%"
            f"<br>Error: {_sign(r['forecast_error_pp'])} pp<extra></extra>"
        )
        fig.add_trace(go.Scatter(
            x=[0, 1], y=[r["imf_gdp_growth_pct"], r["gdp_growth_pct"]],
            mode="lines+markers", name=name, showlegend=False,
            line=dict(color=hex_to_rgba(colour, alpha), width=5 if thick else 2.5),
            marker=dict(color=hex_to_rgba(colour, alpha), size=10 if thick else 8),
            hovertemplate=hover,
        ))

    # Right-hand labels, de-overlapped vertically
    ys = d["gdp_growth_pct"].to_numpy()
    span = max(float(np.nanmax(np.r_[ys, d["imf_gdp_growth_pct"]]) -
                     np.nanmin(np.r_[ys, d["imf_gdp_growth_pct"]])), 1.0)
    label_y = deoverlap(ys, min_gap=0.045 * span)
    for (_, r), ly in zip(d.iterrows(), label_y):
        name = r["country"]
        faded = bool(highlight) and name != highlight
        fig.add_annotation(
            x=1, y=float(ly), xanchor="left", xshift=14, showarrow=False,
            text=f"{name} ({_sign(r['forecast_error_pp'])})",
            font=dict(size=12, color=hex_to_rgba(COUNTRY_COLOURS[name], FADE_SLOPE if faded else 1.0)),
        )

    fig.add_hline(y=0, line_width=1, line_color="grey")
    fig.update_xaxes(
        tickmode="array", tickvals=[0, 1],
        ticktext=["IMF forecast (Oct 2019)", "Actual (World Bank)"],
        range=[-0.25, 1.9], showgrid=False, tickfont=dict(size=13),
    )
    fig.update_yaxes(title_text="Annual real GDP growth (%)", zeroline=False)
    fig.update_layout(
        template=TEMPLATE, title=slope_title(d, year), height=600,
        margin=dict(r=40), font=dict(size=13),
    )
    return fig


# --------------------------------------------------------------------------
# CHART 2 - timeline
# --------------------------------------------------------------------------
def _fmt_pct(v) -> str:
    return "n/a" if pd.isna(v) else f"{v:.1f}%"


def _fmt_err(v) -> str:
    return "n/a" if pd.isna(v) else f"{v:+.1f} pp"


def _timeline_custom(d: pd.DataFrame) -> list:
    return [[_fmt_pct(f), _fmt_err(e)] for f, e in zip(d["imf_gdp_growth_pct"], d["forecast_error_pp"])]


def timeline_figure(df: pd.DataFrame, countries, show_forecast: bool = True,
                    view: str = "Together") -> go.Figure:
    countries = [c for c in countries if c in COUNTRY_COLOURS]
    if not countries:
        return empty_figure("Select at least one country.")
    title = "GDP growth, 2010-2022, with the pre-COVID IMF forecast"

    if view == "Small multiples":
        ncols = min(4, len(countries))
        nrows = math.ceil(len(countries) / ncols)
        fig = make_subplots(rows=nrows, cols=ncols, subplot_titles=countries,
                            shared_xaxes=True, vertical_spacing=0.14 if nrows > 1 else 0.1,
                            horizontal_spacing=0.06)
        for k, c in enumerate(countries):
            row, col = k // ncols + 1, k % ncols + 1
            d = df[df["country"] == c].sort_values("year")
            first = k == 0
            fig.add_trace(go.Scatter(
                x=d["year"], y=d["gdp_growth_pct"], mode="lines+markers", name="Actual",
                legendgroup="Actual", showlegend=first,
                line=dict(color="#222222", width=2), marker=dict(size=4),
                customdata=_timeline_custom(d),
                hovertemplate=(f"<b>{c}</b><br>Year: %{{x}}<br>Actual: %{{y:.1f}}%"
                               "<br>IMF forecast: %{customdata[0]}<br>Error: %{customdata[1]}<extra></extra>"),
            ), row=row, col=col)
            if show_forecast:
                f = d.dropna(subset=["imf_gdp_growth_pct"])
                fig.add_trace(go.Scatter(
                    x=f["year"], y=f["imf_gdp_growth_pct"], mode="lines", name="IMF forecast (Oct 2019)",
                    legendgroup="Forecast", showlegend=first,
                    line=dict(color=COUNTRY_COLOURS[c], width=2, dash="dash"),
                    hovertemplate=f"<b>{c}</b><br>Year: %{{x}}<br>IMF forecast: %{{y:.1f}}%<extra></extra>",
                ), row=row, col=col)
            fig.add_hline(y=0, line_width=1, line_color="grey", row=row, col=col)
            fig.add_vline(x=2020, line_width=1, line_dash="dot", line_color="#444", row=row, col=col)
            fig.add_vrect(x0=2020.5, x1=2022.5, fillcolor="grey", opacity=0.08, line_width=0,
                          row=row, col=col)
            miss = d.loc[d["year"] == 2020, "forecast_error_pp"]
            if len(miss) and pd.notna(miss.iloc[0]):
                idx = k + 1
                xref = "x domain" if idx == 1 else f"x{idx} domain"
                yref = "y domain" if idx == 1 else f"y{idx} domain"
                fig.add_annotation(x=0.03, y=0.04, xref=xref, yref=yref, xanchor="left",
                                   yanchor="bottom", showarrow=False,
                                   text=f"2020 miss: {miss.iloc[0]:+.1f} pp",
                                   font=dict(size=11, color=BELOW_COLOUR))
        fig.update_xaxes(dtick=2, tickangle=0)
        fig.update_yaxes(title_text="Growth (%)", col=1)
        fig.update_layout(template=TEMPLATE, title=title, height=300 * nrows + 120,
                          legend=dict(orientation="h", y=-0.1), font=dict(size=12))
        fig.add_annotation(text="x-axis: year", x=0.5, y=-0.16 if nrows == 1 else -0.08,
                           xref="paper", yref="paper", showarrow=False, font=dict(size=11, color="#666"))
        return fig

    # ---- Together ----
    fig = go.Figure()
    for c in countries:
        d = df[df["country"] == c].sort_values("year")
        colour = COUNTRY_COLOURS[c]
        fig.add_trace(go.Scatter(
            x=d["year"], y=d["gdp_growth_pct"], mode="lines+markers", name=c, legendgroup=c,
            line=dict(color=colour, width=2.5), marker=dict(size=5),
            customdata=_timeline_custom(d),
            hovertemplate=(f"<b>{c}</b><br>Year: %{{x}}<br>Actual: %{{y:.1f}}%"
                           "<br>IMF forecast: %{customdata[0]}<br>Error: %{customdata[1]}<extra></extra>"),
        ))
        if show_forecast:
            f = d.dropna(subset=["imf_gdp_growth_pct"])
            fig.add_trace(go.Scatter(
                x=f["year"], y=f["imf_gdp_growth_pct"], mode="lines", name=f"{c} - IMF forecast",
                legendgroup=c, showlegend=False,
                line=dict(color=colour, width=2, dash="dash"),
                hovertemplate=f"<b>{c}</b><br>Year: %{{x}}<br>IMF forecast: %{{y:.1f}}%<extra></extra>",
            ))
    fig.add_hline(y=0, line_width=1, line_color="grey")
    fig.add_vline(x=2020, line_width=1, line_dash="dot", line_color="#444")
    fig.add_annotation(x=2020, y=1, yref="paper", text="COVID shock", showarrow=False,
                       xanchor="right", xshift=-4, yanchor="top", font=dict(size=12, color="#444"))
    fig.add_vrect(x0=2020.5, x1=2022.5, fillcolor="grey", opacity=0.08, line_width=0)
    fig.add_annotation(x=2021.5, y=1, yref="paper", text="Recovery period", showarrow=False,
                       yanchor="top", font=dict(size=12, color="#666"))
    fig.update_xaxes(title_text="Year", dtick=2, range=[2009.5, 2022.5])
    fig.update_yaxes(title_text="Annual real GDP growth (%)", zeroline=False)
    fig.update_layout(template=TEMPLATE, title=title, height=560, hovermode="closest",
                      legend=dict(title="Country"), font=dict(size=13))
    return fig


def lowest_year_fact(df: pd.DataFrame, countries) -> str:
    """For the selected countries: in which of them was 2020 the lowest-growth year of 2010-2022?"""
    yes, exceptions = [], []
    for c in countries:
        d = df[df["country"] == c]
        if d.empty:
            continue
        low_year = int(d.loc[d["gdp_growth_pct"].idxmin(), "year"])
        (yes if low_year == 2020 else exceptions).append((c, low_year))
    if not yes and not exceptions:
        return ""
    parts = []
    if yes:
        parts.append("2020 was the lowest-growth year of 2010-2022 for: " + ", ".join(c for c, _ in yes) + ".")
    if exceptions:
        parts.append("Not the lowest: " + ", ".join(f"{c} (lowest in {y})" for c, y in exceptions) + ".")
    return " ".join(parts)


# --------------------------------------------------------------------------
# CHART 3 - forecast error bars
# --------------------------------------------------------------------------
def error_data(df: pd.DataFrame, year: int, sort_by: str = "By error") -> pd.DataFrame:
    d = df[df["year"] == year].dropna(subset=["forecast_error_pp"])
    if sort_by == "Alphabetical":
        d = d.sort_values("country")
    else:
        d = d.sort_values("forecast_error_pp")      # most negative first
    return d.reset_index(drop=True)


def error_title(d: pd.DataFrame, year: int) -> str:
    n = len(d)
    if n == 0:
        return f"{year}: no forecast available"
    err = d["forecast_error_pp"]
    below, above, mean = int((err < 0).sum()), int((err > 0).sum()), float(err.mean())
    if below == n:
        return f"{year}: every country fell short of its pre-COVID forecast, by {abs(mean):.1f} pp on average"
    if above == n:
        return f"{year}: every country beat its pre-COVID forecast, by {abs(mean):.1f} pp on average"
    if above > below:
        if mean > 0:
            return f"{year}: {above} of {n} countries beat the forecast, by {mean:.1f} pp on average"
        return f"{year}: {above} of {n} countries beat the forecast (mean error across all {n}: {_sign(mean)} pp)"
    if mean < 0:
        return f"{year}: {below} of {n} countries fell short of the forecast, by {abs(mean):.1f} pp on average"
    return f"{year}: {below} of {n} countries fell short of the forecast (mean error across all {n}: {_sign(mean)} pp)"


def benchmark_2019_line(df: pd.DataFrame) -> str:
    d = df[df["year"] == 2019].dropna(subset=["forecast_error_pp"])
    if d.empty:
        return ""
    mae = d["forecast_error_pp"].abs().mean()
    return f"For comparison, the IMF's average absolute miss across these countries in 2019 was {mae:.2f} pp."


def error_figure(df: pd.DataFrame, year: int, sort_by: str = "By error", highlight=None) -> go.Figure:
    d = error_data(df, year, sort_by)
    if d.empty:
        return empty_figure("No forecast available for this year.")

    colours = [BELOW_COLOUR if e < 0 else ABOVE_COLOUR for e in d["forecast_error_pp"]]
    opac = [FADE_BARS if (highlight and c != highlight) else 1.0 for c in d["country"]]
    line_w = [2.5 if (highlight and c == highlight) else 0 for c in d["country"]]
    custom = np.column_stack([
        d["imf_gdp_growth_pct"], d["gdp_growth_pct"], d["forecast_error_pp"], d["rank_in_year_1_worst"],
    ])
    fig = go.Figure(go.Bar(
        x=d["forecast_error_pp"], y=d["country"], orientation="h",
        marker=dict(color=colours, opacity=opac, line=dict(color="#111111", width=line_w)),
        text=[_sign(e) for e in d["forecast_error_pp"]], textposition="outside", cliponaxis=False,
        customdata=custom,
        hovertemplate=("<b>%{y}</b><br>IMF forecast: %{customdata[0]:.1f}%<br>Actual: %{customdata[1]:.1f}%"
                       "<br>Error: %{customdata[2]:+.1f} pp<br>Rank (1 = largest negative surprise): "
                       "%{customdata[3]:.0f}<extra></extra>"),
    ))
    # Plotly draws the FIRST category at the bottom; autorange="reversed" puts it at the top,
    # so the most negative error (first row) is at the top.
    fig.update_yaxes(categoryorder="array", categoryarray=list(d["country"]), autorange="reversed",
                     title_text="")
    fig.update_xaxes(title_text="Actual minus forecast growth (percentage points)",
                     range=list(ERROR_X_RANGE), zeroline=False)
    fig.add_vline(x=0, line_width=1.5, line_color="black")

    if year == 2022 and "Saudi Arabia" in set(d["country"]):
        fig.add_annotation(x=-0.3, y="Saudi Arabia", xanchor="right", showarrow=False,
                           text="Outlier in source data, interpret with caution",
                           font=dict(size=11, color="#555"))
    fig.update_layout(template=TEMPLATE, title=error_title(d, year), height=520, showlegend=False,
                      font=dict(size=13), margin=dict(l=20, r=40))
    return fig
