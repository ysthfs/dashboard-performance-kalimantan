import pandas as pd
import streamlit as st
from data_loader import load_data, process_data
from chart import create_chart
from style import apply_style
from utils import minutes_to_hhmm, highlight_sla, add_icon, highlight_tt
import plotly.express as px

# ==============================
# CONSTANT
# ==============================
SLA_THRESHOLD = 240
SLA_WARNING = 360

# ==============================
# STYLE
# ==============================
apply_style()

st.markdown("""
<h1 style='text-align: center; margin-bottom: 5px;'>
    📊 DASHBOARD PERFORMANCE KALIMANTAN
</h1>
<p style='text-align: center; font-size: 14px; color: gray; margin-top: 0;'>
    Monitoring Ticket & SLA Performance
</p>
<hr style='margin-top: 10px; margin-bottom: 20px;'>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-baseweb="tag"] {
    display: none !important;
}

div[data-baseweb="select"] {
    max-width: 300px;
}

[data-baseweb="select"] > div {
    min-height: 32px !important;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# LOAD DATA
# ==============================
df = load_data()
if df.empty:
    st.error("Data tidak ditemukan atau kosong")
    st.stop()

if "Category" not in df.columns:
    st.error("Kolom 'Category' tidak ditemukan")
    st.stop()

# 🔥 ambil category (custom order biar rapi)
order = ["Fiberization", "Connectivity", "Prosky", "BB FTTH"]
categories = [c for c in order if c in df["Category"].dropna().unique()]

# ==============================
# 🔥 HEADER
# ==============================
st.markdown("## 📈 Trend by Category")
st.caption("Filter Category")

col_filter, _ = st.columns([1, 4])

with col_filter:
    selected_categories = st.multiselect(
        "",
        options=categories,
        default=categories,
        key="category_filter",
        placeholder="📊 Select Category"
    )

# ==============================
# APPLY FILTER
# ==============================
#df_trend = df[df["Category"].isin(selected_categories)] if selected_categories else df.copy()
if not selected_categories:
    st.warning("Pilih minimal 1 category")
    st.stop()

df_trend = df[df["Category"].isin(selected_categories)]

df_group_filter, _ = process_data(df_trend)

if df_group_filter.empty:
    st.warning("Data tidak tersedia untuk filter yang dipilih")
    st.stop()

# ==============================
# 🔥 METRICS
# ==============================
col_m1, col_m2 = st.columns(2)

total_ticket = df_group_filter["TT Closed"].sum()
avg_sla = df_group_filter["Avg SLA (Minutes)"].mean()
if pd.isna(avg_sla):
    avg_sla = 0
avg_sla_fmt = minutes_to_hhmm(avg_sla)
status = "❌ Out SLA" if avg_sla > SLA_THRESHOLD else "✅ Meet SLA"

col_m1.metric("🎫 Total Ticket", f"{total_ticket:,}")

delta_color = "inverse" if avg_sla > SLA_THRESHOLD else "normal"
col_m2.metric("⏱ Avg SLA", avg_sla_fmt, status,delta_color=delta_color)

# ==============================
# 🔥 MAIN CONTENT
# ==============================
col_left, col_right = st.columns([2.2, 1.8])

# ==============================
# LEFT
# ==============================
with col_left:

    df_table = df_group_filter[["Month", "TT Closed", "Avg SLA (HH:MM)"]].copy()

    df_table["Avg SLA (HH:MM)"] = df_table["Avg SLA (HH:MM)"].apply(
        lambda x: add_icon(x, SLA_THRESHOLD, SLA_WARNING)
    )

    st.dataframe(
        df_table.style
        .map(lambda x: highlight_sla(x, SLA_THRESHOLD, SLA_WARNING),
             subset=["Avg SLA (HH:MM)"])
        .map(highlight_tt, subset=["TT Closed"])
        .format({"TT Closed": "{:,}"}),
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"📊 {len(selected_categories)} category selected")

    fig_trend = create_chart(df_group_filter)
    st.plotly_chart(fig_trend, use_container_width=True)

# ==============================
# RIGHT
# ==============================
with col_right:

    st.markdown("### 📊 Insight")

    out_sla = df_group_filter[df_group_filter["Avg SLA (Minutes)"] > SLA_THRESHOLD]

    if not out_sla.empty:
        details = ", ".join(
            f"{row['Month']} ({row.get('Avg SLA (HH:MM)', '-')})"
            for _, row in out_sla.iterrows()
        )
        st.write(f"🚨 Over SLA 4 Hour: **{details}**")
    else:
        st.write("✅ Semua bulan masih dalam SLA 4 jam")

    st.markdown("---")

    tt_series = df_group_filter["TT Closed"].fillna(0)

    tt_valid = tt_series[tt_series > 0]

    if not tt_valid.empty:
        idx_max = tt_valid.idxmax()
        idx_min = tt_valid.idxmin()
    
        most_ticket = df_group_filter.loc[idx_max]
        least_ticket = df_group_filter.loc[idx_min]
    
        st.write(f"🔥 Most Ticket: **{most_ticket['Month']} ({most_ticket['TT Closed']})**")
        st.write(f"📉 Least Ticket: **{least_ticket['Month']} ({least_ticket['TT Closed']})**")

    else:
        st.write("Data ticket tidak cukup untuk analisis")
    # ==============================
    # CITY
    # ==============================
    st.markdown("---")
    st.markdown("### Top 10 Worst City")

    df_city_filter = df_trend.copy()
    
    if "Week" not in df_city_filter.columns:
        st.warning("Kolom 'Week' tidak ditemukan")
        st.stop()
    
    if "Kota" not in df_city_filter.columns:
        st.warning("Kolom 'Kota' tidak ditemukan")
        st.stop()
    
    df_city_filter["Week"] = pd.to_numeric(df_city_filter["Week"], errors="coerce")
    df_city_filter = df_city_filter.dropna(subset=["Week"])
    df_city_filter["Week"] = df_city_filter["Week"].astype(int)
    # Ambil week yang tersedia
    weeks_available = sorted(df_city_filter["Week"].dropna().unique())

    # Kalau kosong → stop
    if not weeks_available:
        st.warning("Data week tidak tersedia")
        st.stop()
    
    st.caption("Filter Week")
    
    selected_weeks_city = st.multiselect(
        "",
        options=weeks_available,
        default=[weeks_available[-1]],  # ambil week terakhir yg valid
        key="city_filter",
        placeholder="📅 Week"
    )

    if not selected_weeks_city:
        st.warning("Pilih minimal 1 week")
        st.stop()

    if len(selected_weeks_city) == 1:
        st.caption(f"📅 Week: {selected_weeks_city[0]}")
    else:
        st.caption(f"📅 Week: {min(selected_weeks_city)} - {max(selected_weeks_city)}")

    df_city_filter = df_city_filter[
        df_city_filter["Week"].isin(selected_weeks_city)
    ]

    df_city = df_city_filter[df_city_filter["Status TT"].fillna("").str.lower() == "close"] \
        .groupby("Kota")["Status TT"] \
        .count().reset_index()

    df_city.columns = ["Kota", "TT Closed"]

    df_worst = df_city.sort_values(by="TT Closed", ascending=False).head(10)

    if df_worst.empty:
        st.warning("Tidak ada data city")
    else:
        top_city = df_worst.iloc[0]
        st.write(f"🔥 Top Worst City: **{top_city['Kota']} ({top_city['TT Closed']} TT)**")
        st.caption("📌 Based on filtered data")

    fig_city = px.bar(
        df_worst,
        x="TT Closed",
        y="Kota",
        orientation="h",
        text="TT Closed",
        color="TT Closed",
        color_continuous_scale="Reds"
    )

    fig_city.update_traces(textposition="outside", cliponaxis=False)

    fig_city.update_layout(
        height=300,
        template="plotly_dark",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=0, r=0, t=30, b=10),
        coloraxis_showscale=False
    )

    if not df_worst.empty:
        st.plotly_chart(fig_city, use_container_width=True)
