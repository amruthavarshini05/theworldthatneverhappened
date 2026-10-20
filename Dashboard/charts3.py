"""Pure figure functions for Chapter 3 - "Governments make their choices" (no Streamlit inside)."""
import numpy as np
import plotly.graph_objects as go

from charts import TEMPLATE, empty_figure
from charts2 import NO_COUNTRY, _keep, _line_figure
from data import COUNTRY_COLOURS

STRINGENCY_COLOUR = "#3569A8"
SUPPORT_COLOUR = "#E69F00"


def stringency_figure(pm, countries):
    return _line_figure(pm, "month", "stringency", countries,
                        "Government policy stringency across countries, 2020-2022",
                        "Monthly average Stringency Index (0-100)", "Month", " (index)", yrange=[0, 100])


def support_figure(pm, countries):
    return _line_figure(pm, "month", "economic_support", countries,
                        "Government economic support across countries, 2020-2022",
                        "Monthly average Economic Support Index (0-100)", "Month", " (index)", yrange=[0, 100])


def grouped_bar_figure(avg, countries):
    d = avg[avg["country"].isin(_keep(countries))].sort_values("country")
    if d.empty:
        return empty_figure(NO_COUNTRY)
    fig = go.Figure()
    fig.add_bar(x=d["country"], y=d["avg_stringency"], name="Stringency Index",
                marker_color=STRINGENCY_COLOUR,
                hovertemplate="<b>%{x}</b><br>Avg stringency: %{y:.1f} (0-100)<extra></extra>")
    fig.add_bar(x=d["country"], y=d["avg_economic_support"], name="Economic Support Index",
                marker_color=SUPPORT_COLOUR,
                hovertemplate="<b>%{x}</b><br>Avg economic support: %{y:.1f} (0-100)<extra></extra>")
    fig.update_layout(template=TEMPLATE, barmode="group", height=520, xaxis_tickangle=-35,
                      title="Average policy stringency and economic support by country, 2020-2022",
                      legend_title_text="Policy measure", font=dict(size=13))
    fig.update_yaxes(title_text="Average index (0-100)", range=[0, 100])
    fig.update_xaxes(title_text="Country")
    return fig


def bubble_figure(t, countries, highlight=None):
    """Stringency (x) vs 2020 GDP growth (y); bubble size AND colour = economic support index.
    Bubble area (not diameter) is proportional to the index via sizemode='area'."""
    d = t[t["country"].isin(_keep(countries))]
    if d.empty:
        return empty_figure(NO_COUNTRY)
    sizeref = 2.0 * t["avg_economic_support"].max() / (38 ** 2)
    opacity = [0.25 if (highlight and c != highlight) else 0.85 for c in d["country"]]
    fig = go.Figure(go.Scatter(
        x=d["avg_stringency"], y=d["gdp_growth_pct"], mode="markers+text", text=d["country"],
        textposition="top center",
        marker=dict(size=d["avg_economic_support"], sizemode="area", sizeref=sizeref, sizemin=6,
                    color=d["avg_economic_support"], colorscale="Teal", cmin=0, cmax=100,
                    opacity=opacity, line=dict(width=1, color="white"),
                    colorbar=dict(title="Support Index")),
        customdata=np.column_stack([d["avg_economic_support"]]),
        hovertemplate=("<b>%{text}</b><br>Avg stringency 2020: %{x:.1f} (0-100)"
                       "<br>GDP growth 2020: %{y:.2f}%"
                       "<br>Economic support: %{customdata[0]:.1f} (0-100)<extra></extra>"),
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="grey")
    fig.update_xaxes(title_text="Average policy stringency, 2020 (0-100)")
    fig.update_yaxes(title_text="Real GDP growth, 2020 (%)")
    fig.update_layout(template=TEMPLATE, height=620, font=dict(size=13),
                      title="The stringency paradox: policy choices and GDP growth in 2020")
    return fig


def extremes_text(avg):
    """Dynamic sentence for the key findings (highest/lowest stringency, top support)."""
    hi, lo = avg.loc[avg["avg_stringency"].idxmax()], avg.loc[avg["avg_stringency"].idxmin()]
    top = avg.nlargest(3, "avg_economic_support")
    tops = ", ".join(f"{r.country} ({r.avg_economic_support:.1f})" for r in top.itertuples())
    return (f"Highest average stringency 2020-2022: **{hi.country}** ({hi.avg_stringency:.1f}); "
            f"lowest: **{lo.country}** ({lo.avg_stringency:.1f}). "
            f"Highest reported economic support: {tops}.")
