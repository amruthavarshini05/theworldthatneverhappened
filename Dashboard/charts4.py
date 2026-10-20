"""Pure figure functions for Chapter 4 - "Not every country starts with the same cards".

All functions take the DataFrame from data.load_vulnerability() and return a plotly Figure
(or a plain string/table), so they can be tested without running Streamlit.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from charts import FADE_BARS, TEMPLATE, _sign, empty_figure
from data import (ABOVE_COLOUR, BELOW_COLOUR, COUNTRY_COLOURS, GROUP_TARGETS, INCOME_COLOURS,
                  SHORTFALL_COLS, TRADE_OPEN_THRESHOLD, VULN_VARS, add_groups, leave_one_out,
                  spearman_table)

# Fixed x ranges so that the two outcome measures are always drawn on the same scale
OUTCOME_METRICS = {
    "Shock: shortfall in 2020 (pp)": dict(col="shortfall_2020", range=(-16, 4),
                                          xtitle="Actual minus IMF forecast growth, 2020 (percentage points)"),
    "End-2022: output gap vs expected path (%)": dict(col="level_gap_2022", range=(-14, 9),
                                                     xtitle="Output level vs IMF-expected level, end-2022 (%)"),
}
DEFAULT_OUTCOME = "Shock: shortfall in 2020 (pp)"
MISSING_TOURISM_Y = -1.5          # where countries without tourism data are parked on the bubble chart


def _short(label: str) -> str:
    return label.split(" (")[0]


# --------------------------------------------------------------------------
# 1. The outcome: who ended up furthest from the expected path?
# --------------------------------------------------------------------------
def outcome_figure(v, metric=DEFAULT_OUTCOME, highlight=None):
    m = OUTCOME_METRICS[metric]
    d = v.sort_values(m["col"]).reset_index(drop=True)            # most negative first
    vals = d[m["col"]]
    fig = go.Figure(go.Bar(
        x=vals, y=d["country"], orientation="h",
        marker=dict(color=[BELOW_COLOUR if x < 0 else ABOVE_COLOUR for x in vals],
                    opacity=[FADE_BARS if (highlight and c != highlight) else 1.0 for c in d["country"]],
                    line=dict(color="#111", width=[2.5 if (highlight and c == highlight) else 0 for c in d["country"]])),
        text=[_sign(x) for x in vals], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:+.1f}<extra></extra>",
    ))
    # first category is drawn at the bottom by default; reversed axis puts the most negative on top
    fig.update_yaxes(categoryorder="array", categoryarray=list(d["country"]), autorange="reversed")
    fig.update_xaxes(title_text=m["xtitle"], range=list(m["range"]), zeroline=False)
    fig.add_vline(x=0, line_width=1.5, line_color="black")
    worst = d.iloc[0]
    fig.update_layout(template=TEMPLATE, height=500, showlegend=False, font=dict(size=13),
                      title=f"Largest negative value: {worst['country']} ({_sign(worst[m['col']])})",
                      margin=dict(l=20, r=40))
    return fig


# --------------------------------------------------------------------------
# 2. Vulnerability profiles (heatmap of percentile ranks, raw values printed)
# --------------------------------------------------------------------------
def profile_heatmap_figure(v):
    order = v.sort_values("level_gap_2022")["country"].tolist()      # worst end-2022 gap on top
    d = v.set_index("country").loc[order]
    cols = list(VULN_VARS)
    rank = d[cols].rank(pct=True)           # 0 = least exposed in the panel, 1 = most exposed; NaN stays NaN
    text = d[cols].round(1).astype(object).where(d[cols].notna(), "n/a")
    fig = go.Figure(go.Heatmap(
        z=rank.values, x=[_short(VULN_VARS[c]) for c in cols], y=order, text=text.values,
        texttemplate="%{text}", colorscale="Reds", zmin=0, zmax=1, xgap=2, ygap=2,
        colorbar=dict(title="Rank in panel<br>(1 = most exposed)"), hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<br>Rank (0-1): %{z:.2f}<extra></extra>",
    ))
    for i, country in enumerate(order):                 # make missing data explicit (never shown as 0)
        for col in cols:
            if pd.isna(d.loc[country, col]):
                fig.add_annotation(x=_short(VULN_VARS[col]), y=country, text="n/a", showarrow=False,
                                   font=dict(size=12, color="#666"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top")
    fig.update_layout(template=TEMPLATE, height=560, font=dict(size=13), plot_bgcolor="#f0f0f0",
                      title="2019 vulnerability profiles (countries sorted by end-2022 output gap, worst first)")
    return fig


# --------------------------------------------------------------------------
# 3. Two channels of exposure: tourism x trade, bubble = 2020 shock
# --------------------------------------------------------------------------
def exposure_bubble_figure(v):
    fig = go.Figure()
    sizeref = 2.0 * v["shortfall_2020"].abs().max() / (42 ** 2)
    for grp, colour in INCOME_COLOURS.items():
        d = v[v["income_group"] == grp]
        if d.empty:
            continue
        miss = d["tourism_receipts_pct_exports"].isna()
        y = d["tourism_receipts_pct_exports"].fillna(MISSING_TOURISM_Y)
        fig.add_trace(go.Scatter(
            x=d["trade_pct_gdp"], y=y, mode="markers+text", name=grp,
            text=[f"{c} (tourism n/a)" if m else c for c, m in zip(d["country"], miss)],
            textposition="middle right",
            marker=dict(size=d["shortfall_2020"].abs(), sizemode="area", sizeref=sizeref, sizemin=6,
                        color=colour, opacity=0.75,
                        line=dict(color="black", width=1.2)),
            customdata=np.column_stack([d["shortfall_2020"], d["tourism_receipts_pct_exports"].fillna(np.nan)]),
            hovertemplate=("<b>%{text}</b><br>Trade: %{x:.1f}% of GDP<br>2020 shortfall: %{customdata[0]:+.1f} pp"
                           "<extra></extra>"),
        ))
    fig.add_hline(y=0, line_width=0.8, line_color="grey")
    fig.add_annotation(x=1, xref="paper", y=MISSING_TOURISM_Y, yanchor="top", xanchor="right", showarrow=False,
                       text="Tourism data missing: parked below the axis", font=dict(size=11, color="#666"))
    fig.update_xaxes(title_text="Trade openness, 2019 (% of GDP)", range=[15, 135])
    fig.update_yaxes(title_text="Tourism receipts, 2019 (% of exports)", range=[-4, 25], zeroline=False)
    fig.update_layout(template=TEMPLATE, height=560, font=dict(size=13), legend_title_text="Income group",
                      title="Two channels of exposure to the world (bubble size = size of the 2020 shock)")
    return fig


# --------------------------------------------------------------------------
# 4. Do vulnerabilities explain the shortfall? Scatter + Spearman
# --------------------------------------------------------------------------
def correlation_figure(v, var, target):
    s = v[["country", "income_group", var, target]].dropna()
    if len(s) < 3:
        return empty_figure("Not enough observations.")
    tab = spearman_table(v, target, [var]).iloc[0]
    fig = go.Figure()
    for grp, colour in INCOME_COLOURS.items():
        g = s[s["income_group"] == grp]
        if g.empty:
            continue
        fig.add_trace(go.Scatter(
            x=g[var], y=g[target], mode="markers+text", text=g["country"], textposition="top right",
            name=grp, marker=dict(color=colour, size=12, line=dict(color="black", width=1)),
            hovertemplate=f"<b>%{{text}}</b><br>{_short(VULN_VARS[var])}: %{{x:.1f}}<br>%{{y:+.1f}}<extra></extra>"))
    b = np.polyfit(s[var], s[target], 1)
    xx = np.linspace(s[var].min(), s[var].max(), 50)
    fig.add_trace(go.Scatter(x=xx, y=np.polyval(b, xx), mode="lines", showlegend=False,
                             line=dict(color="grey", dash="dash", width=1), hoverinfo="skip"))
    fig.add_hline(y=0, line_width=1, line_color="black")
    ytitle = "Shortfall 2020 (pp)" if target == "shortfall_2020" else "Output gap end-2022 (%)"
    fig.update_xaxes(title_text=VULN_VARS[var])
    fig.update_yaxes(title_text=ytitle)
    fig.update_layout(template=TEMPLATE, height=480, font=dict(size=13), legend_title_text="Income group",
                      title=f"{_short(VULN_VARS[var])}: Spearman rho = {tab['spearman_rho']:+.2f} "
                            f"(p = {tab['p_value']:.2f}, n = {int(tab['n'])})")
    return fig


def correlation_text(v, target) -> str:
    t = spearman_table(v, target)
    best = t["spearman_rho"].abs().idxmax()
    sig = int((t["p_value"] < 0.05).sum())
    return (f"{sig} of the {len(t)} correlations are statistically significant at 5%. The strongest is "
            f"{_short(VULN_VARS[best])} (rho = {t.loc[best, 'spearman_rho']:+.2f}, n = {int(t.loc[best, 'n'])}). "
            "With 11 countries these are descriptive patterns, not evidence of causation.")


# --------------------------------------------------------------------------
# 5. Robustness: leave-one-out heatmap
# --------------------------------------------------------------------------
def leave_one_out_figure(v, target="shortfall_2020"):
    lo = leave_one_out(v, target)
    cols = list(VULN_VARS)
    fig = go.Figure(go.Heatmap(
        z=lo[cols].T.values, x=list(lo.index), y=[_short(VULN_VARS[c]) for c in cols],
        colorscale="RdBu", zmid=0, zmin=-1, zmax=1, text=np.round(lo[cols].T.values, 2),
        texttemplate="%{text:+.2f}", colorbar=dict(title="rho without<br>this country"),
        hovertemplate="Without <b>%{x}</b><br>%{y}<br>rho = %{z:+.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Country removed", tickangle=-35)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(template=TEMPLATE, height=420, font=dict(size=13),
                      title="Spearman rho (vulnerability vs 2020 shock) after removing one country at a time")
    return fig


def leave_one_out_text(v, target="shortfall_2020") -> str:
    lo = leave_one_out(v, target)
    flips = [_short(VULN_VARS[c]) for c in lo if lo[c].min() < 0 < lo[c].max()]
    stable = [_short(VULN_VARS[c]) for c in lo if not (lo[c].min() < 0 < lo[c].max())]
    return (f"The sign of the relationship is stable for: {', '.join(stable) or 'none'}. "
            f"It flips depending on the country removed for: {', '.join(flips) or 'none'}.")


# --------------------------------------------------------------------------
# 6. Group comparison (strip plot)
# --------------------------------------------------------------------------
def group_figure(v, grouping="income_group", target="level_gap_2022"):
    g = add_groups(v)
    cats = sorted(g[grouping].unique())
    fig = go.Figure()
    for c in g["country"]:
        r = g[g["country"] == c].iloc[0]
        fig.add_trace(go.Scatter(
            x=[r[grouping]], y=[r[target]], mode="markers+text", text=[c], textposition="middle right",
            showlegend=False, marker=dict(size=13, color=COUNTRY_COLOURS[c], line=dict(color="black", width=1)),
            hovertemplate=f"<b>{c}</b><br>{GROUP_TARGETS[target]}: %{{y:+.1f}}<extra></extra>"))
    means = g.groupby(grouping)[target].mean()
    for i, cat in enumerate(cats):
        fig.add_shape(type="line", xref="x", yref="y", x0=i - 0.3, x1=i + 0.3, y0=means[cat], y1=means[cat],
                      line=dict(color="black", width=3))
    fig.add_hline(y=0, line_width=1, line_color="grey")
    fig.update_xaxes(categoryorder="array", categoryarray=cats, title_text="", range=[-0.6, len(cats) - 0.2])
    fig.update_yaxes(title_text=GROUP_TARGETS[target], zeroline=False)
    fig.update_layout(template=TEMPLATE, height=500, font=dict(size=13),
                      title="Who ended furthest from the expected path? (black bar = group mean)")
    return fig


# --------------------------------------------------------------------------
# 7. Structure or crisis management? stringency x shock, bubble = deaths, colour = trade
# --------------------------------------------------------------------------
def context_figure(v):
    sizes = np.sqrt(v["deaths_per_million_2020"].clip(lower=1))
    sizeref = 2.0 * sizes.max() / (46 ** 2)
    labels = [f"{c}<br>(tourism {t:.0f}%)" if pd.notna(t) else f"{c}<br>(tourism n/a)"
              for c, t in zip(v["country"], v["tourism_receipts_pct_exports"])]
    fig = go.Figure(go.Scatter(
        x=v["stringency_2020"], y=v["shortfall_2020"], mode="markers+text", text=labels,
        textposition="middle right",
        marker=dict(size=sizes, sizemode="area", sizeref=sizeref, sizemin=6, color=v["trade_pct_gdp"],
                    colorscale="Viridis", showscale=True, colorbar=dict(title="Trade openness<br>2019 (% GDP)"),
                    line=dict(color="black", width=1), opacity=0.85),
        customdata=np.column_stack([v["country"], v["deaths_per_million_2020"], v["trade_pct_gdp"]]),
        hovertemplate=("<b>%{customdata[0]}</b><br>Stringency 2020: %{x:.1f} (0-100)"
                       "<br>2020 shortfall: %{y:+.1f} pp<br>Deaths 2020: %{customdata[1]:,.0f} per million"
                       "<br>Trade: %{customdata[2]:.0f}% of GDP<extra></extra>")))
    fig.add_hline(y=0, line_width=1, line_color="grey")
    fig.update_xaxes(title_text="Average stringency index, 2020 (0-100)", range=[42, 80])
    fig.update_yaxes(title_text="Shortfall 2020 (pp)")
    fig.update_layout(template=TEMPLATE, height=600, font=dict(size=13),
                      title="Structural exposure x restrictions x health shock "
                            "(size = COVID deaths per million in 2020)")
    return fig


# --------------------------------------------------------------------------
# 8. Oil: a vulnerability that cuts both ways
# --------------------------------------------------------------------------
def oil_figure(v, countries):
    countries = [c for c in countries if c in COUNTRY_COLOURS]
    if not countries:
        return empty_figure("Select at least one country.")
    fig = go.Figure()
    for c in countries:
        r = v[v["country"] == c].iloc[0]
        fig.add_trace(go.Scatter(
            x=[2019, 2020, 2021, 2022], y=[r[k] for k in SHORTFALL_COLS], mode="lines+markers", name=c,
            line=dict(color=COUNTRY_COLOURS[c], width=3.5 if c == "Saudi Arabia" else 1.8),
            hovertemplate=f"<b>{c}</b><br>%{{x}}: %{{y:+.1f}} pp<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color="black")
    fig.update_xaxes(title_text="Year", tickvals=[2019, 2020, 2021, 2022])
    fig.update_yaxes(title_text="Actual minus IMF forecast growth (pp)")
    fig.update_layout(template=TEMPLATE, height=480, font=dict(size=13), legend_title_text="Country",
                      title="Saudi Arabia: below forecast in 2020, far above it in 2022")
    return fig


# --------------------------------------------------------------------------
# 9. A bias to keep in mind: forecast error before the pandemic (2019)
# --------------------------------------------------------------------------
def pre_covid_bias_figure(v):
    d = v.sort_values("shortfall_2019").reset_index(drop=True)
    fig = go.Figure(go.Bar(
        x=d["shortfall_2019"], y=d["country"], orientation="h",
        marker_color=[BELOW_COLOUR if x < -1 else "#999999" for x in d["shortfall_2019"]],
        text=[_sign(x) for x in d["shortfall_2019"]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>2019 error: %{x:+.1f} pp<extra></extra>"))
    fig.update_yaxes(categoryorder="array", categoryarray=list(d["country"]), autorange="reversed")
    fig.add_vline(x=0, line_width=1, line_color="black")
    fig.update_xaxes(title_text="Actual 2019 growth minus IMF 2019 forecast (percentage points)", range=[-3.5, 2.8])
    fig.update_layout(template=TEMPLATE, height=460, showlegend=False, font=dict(size=13),
                      title="Forecast error before the pandemic (2019); red = more than 1 pp below forecast")
    return fig
