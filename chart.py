import plotly.graph_objects as go
from utils import minutes_to_hhmm
import numpy as np

def create_chart(df_group):
    threshold = 60

    # ==============================
    # COLOR BAR (TT Closed)
    # ==============================
    colors = [
        "rgba(255, 107, 107, 0.55)" if tt > threshold else "#4FC3F7"
        for tt in df_group["TT Closed"]
    ]

    fig = go.Figure()

    # ==============================
    # BAR CHART
    # ==============================
    fig.add_bar(
        x=df_group["Month"],
        y=df_group["TT Closed"],
        name="TT Closed",
        marker=dict(color=colors),

        text=df_group["TT Closed"],
        texttemplate="%{text:,}",
        textposition="outside",
        cliponaxis=False,

        textfont=dict(
            color="rgba(255, 200, 0, 0.8)",
            size=13,
            family="Arial Black"
        )
    )

    # ==============================
    # SLA DATA PREP (AUTO SCALE FIX)
    # ==============================
    sla_values = df_group["Avg SLA (Minutes)"].fillna(0)

    min_sla = sla_values.min()
    max_sla = sla_values.max()

    # ==============================
    # DYNAMIC PADDING
    # ==============================
    range_sla = max_sla - min_sla

    if range_sla == 0:
        padding = max(60, max_sla * 0.5 + 1)
    else:
        padding = range_sla * 0.25

    min_sla = max(0, min_sla - padding)
    max_sla = max_sla + padding
    max_sla = max(max_sla, sla_values.max() * 1.15)

    # ==============================
    # AUTO STEP (SMART TICKS)
    # ==============================
    range_final = max_sla - min_sla

    if range_final <= 120:
        step = 15
    elif range_final <= 300:
        step = 30
    elif range_final <= 600:
        step = 60
    else:
        step = 120

    # rounding biar clean
    tick_start = int(min_sla // step * step)
    tick_end = int((max_sla // step + 1) * step)

    tick_vals = np.arange(tick_start, tick_end + step, step).astype(int).tolist()
    # 🔥 PROTEKSI KOSONG / ERROR RANGE
    if len(tick_vals) == 0:
        tick_vals = [0, 60, 120, 180, 240]
    tick_text = [minutes_to_hhmm(int(x)) for x in tick_vals]

    # ==============================
    # GLOW LINE (BACKGROUND)
    # ==============================
    fig.add_scatter(
        x=df_group["Month"],
        y=sla_values,
        mode="lines",
        line=dict(
            shape="spline",
            smoothing=1.3,
            width=6,
            color="rgba(0,191,255,0.25)"
        ),
        hoverinfo="skip",
        showlegend=False,
        yaxis="y2"
    )

    # ==============================
    # MAIN SLA LINE
    # ==============================
    fig.add_scatter(
        x=df_group["Month"],
        y=sla_values,
        mode="lines+markers+text",
        name="Avg SLA",

        text=df_group["Avg SLA (HH:MM)"],
        customdata=df_group["TT Closed"],

        textposition="top center",
        yaxis="y2",

        hovertemplate=
        "<b>%{x}</b><br>" +
        "TT Closed: %{customdata}<br>" +
        "Avg SLA: %{text}<br>" +
        "<extra></extra>",

        line=dict(
            shape="spline",
            smoothing=1.3,
            width=3,
            color="#00EFFF"
        ),

        marker=dict(
            size=8,
            color=[
                "#FF3B3B" if v > 480 else "#00EFFF"
                for v in sla_values.fillna(0)
            ],
            line=dict(width=2, color="white")
        ),

        textfont=dict(
            color="white",
            size=14,
            family="Arial Black"
        )
    )

    # ==============================
    # SLA LINE (4 JAM)
    # ==============================
    fig.add_hline(
        y=240,
        line_dash="dash",
        line_color="#FC0404",
        line_width=2,
        annotation_text="<b>SLA 4:00</b>",
        annotation_position="top right",
        yref="y2",
        annotation_font=dict(color="#FC0404", size=12)
    )

    # ==============================
    # Y AXIS TT
    # ==============================
    max_tt = df_group["TT Closed"].max()

    # ==============================
    # FINAL LAYOUT
    # ==============================
    padding_top = max_tt * 0.25
    fig.update_layout(
        title=dict(
            text="Trends Ticket vs MTTR",
            font=dict(size=26)
        ),
                
        xaxis=dict(title="Month"),

        hovermode="x unified",

        hoverlabel=dict(
            bgcolor="black",
            font_size=12,
            font_family="Arial"
        ),

        yaxis=dict(
            title="TT Closed",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
            range=[0, max_tt + padding_top]
        ),

        yaxis2=dict(
            title="Avg SLA",
            overlaying="y",
            side="right",
            range=[min_sla, max_sla],
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            tickformat=None,
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=1,
            xanchor="right"
        ),

        margin=dict(l=40, r=40, t=90, b=80)
    )

    return fig
