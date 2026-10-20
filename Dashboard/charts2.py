"""Pure figure functions for Chapter 2 - "The shock hits" (no Streamlit inside)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from charts import TEMPLATE, empty_figure, hex_to_rgba
from data import COUNTRY_COLOURS

NO_COUNTRY = "Select at least one country."


def _keep(countries):
    return [c for c in countries if c in COUNTRY_COLOURS]


def _line_figure(d, x, y, countries, title, ytitle, xtitle, hover_unit, markers=False, zero_line=False,
                 yrange=None, xdtick=None):
    """Generic one-line-per-country chart using the fixed country colours.
    Missing values are NOT filled: Plotly leaves gaps where y is NaN or the row is absent."""
    countries = _keep(countries)
    if not countries:
        return empty_figure(NO_COUNTRY)
    fig = go.Figure()
    for c in countries:
        g = d[d["country"] == c].sort_values(x)
        if g[y].notna().sum() == 0:
            continue
        fig.add_trace(go.Scatter(
            x=g[x], y=g[y], mode="lines+markers" if markers else "lines", name=c,
            line=dict(color=COUNTRY_COLOURS[c], width=2.5), marker=dict(size=7),
            connectgaps=False,
            hovertemplate=f"<b>{c}</b><br>%{{x}}<br>%{{y:.1f}}{hover_unit}<extra></extra>",
        ))
    if zero_line:
        fig.add_hline(y=0, line_dash="dash", line_color="grey", line_width=1)
    fig.update_xaxes(title_text=xtitle, dtick=xdtick)
    fig.update_yaxes(title_text=ytitle, range=yrange)
    fig.update_layout(template=TEMPLATE, title=title, height=520, hovermode="x unified",
                      legend_title_text="Country", font=dict(size=13))
    return fig


# ---- 1. GDP growth 2019-2022 ---------------------------------------------
def gdp_growth_figure(df, countries):
    d = df[df["year"].between(2019, 2022)]
    return _line_figure(d, "year", "gdp_growth_pct", countries,
                        "Annual GDP growth across countries, 2019-2022", "Real GDP growth (%)", "Year",
                        "%", markers=True, zero_line=True, xdtick=1)


# ---- 2. Forecast-error heatmap -------------------------------------------
def error_matrix(df, countries):
    d = df[df["year"].between(2019, 2022)].dropna(subset=["forecast_error_pp"])
    d = d[d["country"].isin(_keep(countries))]
    m = d.pivot(index="country", columns="year", values="forecast_error_pp")
    return m.loc[m.mean(axis=1).sort_values().index] if len(m) else m


def error_heatmap_figure(df, countries):
    m = error_matrix(df, countries)
    if m.empty:
        return empty_figure(NO_COUNTRY)
    lim = float(np.nanmax(np.abs(m.values)))          # symmetric scale => 0 is the white midpoint
    fig = go.Figure(go.Heatmap(
        z=m.values, x=[str(y) for y in m.columns], y=list(m.index),
        colorscale="RdBu", zmid=0, zmin=-lim, zmax=lim,
        text=np.round(m.values, 1), texttemplate="%{text:+.1f}",
        colorbar=dict(title="Error (pp)"),
        hovertemplate="<b>%{y}</b><br>%{x}<br>Forecast error: %{z:+.1f} pp<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", title_text="Country (sorted by mean error)")
    fig.update_xaxes(title_text="Year", type="category")
    fig.update_layout(template=TEMPLATE, height=120 + 48 * len(m),
                      title="GDP forecast errors, 2019-2022 (actual minus IMF Oct 2019 forecast)",
                      font=dict(size=13))
    return fig


def error_stats(df):
    """Mean error by year and the 2021 count above forecast (for dynamic text)."""
    d = df.dropna(subset=["forecast_error_pp"])
    return d.groupby("year")["forecast_error_pp"].mean()


# ---- 3. Monthly deaths ----------------------------------------------------
def deaths_figure(hm, countries):
    return _line_figure(hm, "month", "avg_daily_deaths_per_million", countries,
                        "Monthly average daily COVID-19 deaths per million, 2020-2022",
                        "Average daily deaths per million", "Month", " per million")


# ---- 3b. Map of the annual health shock -----------------------------------
def deaths_map_figure(annual, year, highlight=None):
    """Choropleth of estimated annual COVID-19 deaths per million for ONE year.

    The colour scale is FIXED across years (max over all years) so that 2020, 2021
    and 2022 can be compared by eye. Only the 11 study countries are coloured;
    all other countries stay grey (= not in the study, not 'zero deaths').
    """
    d = annual[annual["year"] == year]
    if d.empty:
        return empty_figure("No data for this year.")
    zmax = float(annual["annual_deaths_per_million"].max())
    fig = go.Figure(go.Choropleth(
        locations=d["code"], z=d["annual_deaths_per_million"], text=d["country"],
        locationmode="ISO-3", colorscale="YlOrRd", zmin=0, zmax=zmax,
        marker_line_color=["#111111" if (highlight and c == highlight) else "white" for c in d["country"]],
        marker_line_width=[2.5 if (highlight and c == highlight) else 0.6 for c in d["country"]],
        colorbar=dict(title="Deaths per<br>million"),
        hovertemplate=("<b>%{text}</b><br>" + str(year) +
                       ": %{z:,.0f} reported deaths per million<extra></extra>"),
    ))
    fig.update_geos(showcountries=True, countrycolor="#cccccc", showcoastlines=False,
                    showland=True, landcolor="#eeeeee", showframe=False,
                    projection_type="natural earth")
    top = d.loc[d["annual_deaths_per_million"].idxmax()]
    fig.update_layout(template=TEMPLATE, height=520, margin=dict(l=0, r=0, t=70, b=0),
                      title=f"{year}: reported COVID-19 deaths per million, highest in {top['country']} "
                            f"({top['annual_deaths_per_million']:,.0f})",
                      font=dict(size=13))
    return fig


# ---- 4. Vaccination -------------------------------------------------------
def vaccination_figure(vm, countries):
    fig = _line_figure(vm, "month", "people_fully_vaccinated_per_hundred", countries,
                       "Full vaccination coverage by country, 2020-2022",
                       "Population fully vaccinated (%)", "Month", "%", yrange=[0, 100])
    return fig


def vaccination_gaps(vm, countries):
    """Countries whose series is sparse (many months without data) - used for a data-quality note."""
    out = []
    for c in _keep(countries):
        n = int((vm["country"] == c).sum())
        if n < 20:      # vaccination starts late 2020, so ~25 months is the maximum possible
            out.append(f"{c} ({n} months with data)")
    return out


# ---- 5/6. Scatter plots ---------------------------------------------------
def _scatter(me, ycol, ytitle, title, countries, years, zero_label=None):
    d = me[me["country"].isin(_keep(countries)) & me["year"].isin(years)].dropna(
        subset=["avg_daily_deaths_per_million", ycol])
    if d.empty:
        return empty_figure("Select at least one country and one year.")
    fig = go.Figure()
    symbols = {2020: "circle", 2021: "square", 2022: "diamond"}
    for c in sorted(d["country"].unique()):
        g = d[d["country"] == c]
        fig.add_trace(go.Scatter(
            x=g["avg_daily_deaths_per_million"], y=g[ycol], mode="markers", name=c,
            marker=dict(color=COUNTRY_COLOURS[c], size=11, line=dict(width=1, color="white"),
                        symbol=[symbols[y] for y in g["year"]]),
            customdata=np.column_stack([g["year"], g["imf_gdp_growth_pct"], g["gdp_growth_pct"]]),
            hovertemplate=(f"<b>{c}</b> (%{{customdata[0]}})<br>Deaths: %{{x:.2f}} per million per day"
                           f"<br>{ytitle.split(' (')[0]}: %{{y:.1f}}"
                           "<br>Actual growth: %{customdata[2]:.1f}%<extra></extra>"),
        ))
    fig.add_hline(y=0, line_dash="dash", line_color="grey",
                  annotation_text=zero_label, annotation_position="top left")
    fig.update_xaxes(title_text="Average daily COVID-19 deaths per million", rangemode="tozero")
    fig.update_yaxes(title_text=ytitle)
    fig.update_layout(template=TEMPLATE, title=title, height=560, legend_title_text="Country",
                      font=dict(size=13))
    fig.add_annotation(text="Marker shape: circle = 2020, square = 2021, diamond = 2022",
                       xref="paper", yref="paper", x=0, y=-0.18, showarrow=False,
                       font=dict(size=11, color="#666"))
    return fig


def mortality_growth_figure(me, countries, years):
    return _scatter(me, "gdp_growth_pct", "Real GDP growth (%)",
                    "COVID-19 mortality and GDP growth, 2020-2022", countries, years)


def mortality_error_figure(me, countries, years):
    return _scatter(me, "forecast_error_pp", "GDP forecast error (percentage points)",
                    "Health impact and economic shortfall, 2020-2022", countries, years,
                    zero_label="Actual growth matched forecast")


def correlation_text(me, xcol, ycol, countries, years):
    d = me[me["country"].isin(_keep(countries)) & me["year"].isin(years)].dropna(subset=[xcol, ycol])
    if len(d) < 3:
        return "Too few observations to compute a correlation."
    r = d[xcol].corr(d[ycol].astype(float))
    strength = "very weak" if abs(r) < 0.2 else "weak" if abs(r) < 0.4 else "moderate" if abs(r) < 0.6 else "strong"
    sign = "negative" if r < 0 else "positive"
    return (f"Correlation across {len(d)} country-year observations: **{r:+.3f}** "
            f"({strength} {sign} linear relationship). Descriptive only; not evidence of causation.")