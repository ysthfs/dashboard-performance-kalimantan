import pandas as pd
import streamlit as st
from data_loader import load_data, process_data
from chart import create_chart
from style import apply_style
from utils import minutes_to_hhmm, highlight_sla, add_icon, highlight_tt
import plotly.express as px
#from streamlit_autorefresh import st_autorefresh

# ==============================
# CONSTANT
# ==============================
SLA_THRESHOLD = 240
SLA_WARNING = 360

# BEST PRACTICE
COL_PROJECT = "Type Project"

# ==============================
# STYLE
# ==============================
apply_style()
# SAFE AUTO REFRESH
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=30 * 60 * 1000, limit=100, key="refresh")
except Exception as e:
    st.warning(f"Auto refresh disabled: {e}")
    
st.markdown("""
<h1 style='text-align: center; margin-bottom: 5px;'>
    📊 DASHBOARD PERFORMANCE RPS KALIMANTAN
</h1>
<p style='text-align: center; font-size: 20px; color: white; margin-top: 0;'>
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
with st.spinner("Loading data..."):
    df = load_data()
    df.columns = df.columns.str.strip()
if df.empty:
    st.error("Data tidak ditemukan atau kosong")
    st.stop()

if COL_PROJECT not in df.columns:
    st.error("Kolom 'Type Project' tidak ditemukan")
    st.stop()

# 🔥 ambil Type Project (custom order biar rapi)
order = ["Fiberization", "Connectivity", "Prosky", "BB FTTH"]
unique_values = df[COL_PROJECT].dropna().unique()
categories = list(dict.fromkeys(order + list(unique_values)))

# fallback kalau kosong
if not categories:
    categories = sorted(unique_values)

# ==============================
# 🔥 HEADER
# ==============================

st.caption("Filter Type Project")

col_filter, _ = st.columns([1, 4])

with col_filter:
    selected_projects = st.multiselect(
        "",
        options=categories,
        default=categories,
        key="type_project_filter",
        placeholder="📊 Select Type Project"
    )

# ==============================
# APPLY FILTER
# ==============================
#df_trend = df[df[COL_PROJECT].isin(selected_categories)] if selected_categories else df.copy()
if not selected_projects:
    st.warning("Pilih minimal 1 Type Project")
    st.stop()

df_trend = df[df[COL_PROJECT].isin(selected_projects)]

df_group_filter, _ = process_data(df_trend)

if df_group_filter.empty:
    st.warning("Data tidak tersedia untuk filter yang dipilih")
    st.stop()

# ==============================
# 🔥 METRICS
# ==============================
col_m1, col_m2 = st.columns(2)

total_ticket = df_group_filter["TT Closed"].sum()
if df_group_filter["Avg SLA (Minutes)"].dropna().empty:
    avg_sla = 0
else:
    avg_sla = df_group_filter["Avg SLA (Minutes)"].mean()
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

    # pastikan kolom HH:MM selalu ada
    if "Avg SLA (HH:MM)" not in df_group_filter.columns:
        df_group_filter["Avg SLA (HH:MM)"] = df_group_filter["Avg SLA (Minutes)"].apply(minutes_to_hhmm)
    
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

    st.caption(f"📊 {len(selected_projects)} Type Project selected")

    fig_trend = create_chart(df_group_filter)
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # ==============================
    # 🔥 OWNER COMPARISON CHART
    # ==============================

    st.markdown("### Ticket by Owner")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "Owner" not in df_trend.columns:
        st.warning("Kolom 'Owner' tidak ditemukan")
    else:
        df_owner = df_trend.copy()

        # pastikan cuma ticket close
        df_owner = df_owner[
            df_owner["Status TT"].fillna("").str.lower() == "close"
        ]

        # grouping
        df_owner_group = (
            df_owner.groupby(["Month", "Owner"])
            .size()
            .reset_index(name="Total Ticket")
        )

        # urutan bulan biar ga acak
        month_order = ["January","February","March","April","May","June",
                    "July","August","September","October","November","December"]

        fig_owner = px.bar(
            df_owner_group,
            x="Month",
            y="Total Ticket",
            color="Owner",
            barmode="group",  # 👉 bisa ganti "stack"
            text="Total Ticket",
            category_orders={"Month": month_order}
        )
        
        fig_owner.update_traces(
            textposition="outside"
        )
        
        fig_owner.update_layout(
            uniformtext_minsize=8,
            uniformtext_mode='hide'
        )
        
        fig_owner.update_yaxes(
            range=[0, df_owner_group["Total Ticket"].max() * 1.2]
        )
        
        fig_owner.update_layout(
            template="plotly_dark",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Month",
            yaxis_title="Total Ticket",
            legend_title="Owner"
        )

        st.plotly_chart(fig_owner, use_container_width=True)

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

    # ==============================
    # 🔥 ROOT CAUSE PIE CHART
    # ==============================
    st.markdown("---")
    st.markdown("### 🧩 Root Cause Distribution")
    
    if "Root Cause" not in df_city_filter.columns:
        st.warning("Kolom 'Root Cause' tidak ditemukan")
    else:
        df_root = df_city_filter.copy()
    
        # hanya ticket close
        df_root = df_root[
            df_root["Status TT"].fillna("").str.lower() == "close"
        ]
    
        # grouping
        df_root_group = (
            df_root.groupby("Root Cause")
            .size()
            .reset_index(name="Total")
        )
    
        if df_root_group.empty:
            st.warning("Tidak ada data Root Cause")
        else:
    
            # ==============================
            # 🔥 TARUH DI SINI (TOP 6 + OTHERS)
            # ==============================
            top_n = 6
    
            df_sorted = df_root_group.sort_values(by="Total", ascending=False)
    
            df_top = df_sorted.head(top_n)
    
            df_others_total = df_sorted.iloc[top_n:]["Total"].sum()
    
            df_others = pd.DataFrame([{
                "Root Cause": "Others",
                "Total": df_others_total
            }])
    
            df_final = pd.concat([df_top, df_others], ignore_index=True)
            df_final = df_final[df_final["Total"] > 0]
            df_final = df_final.sort_values(by="Total", ascending=False)
            # ==============================
            # 🎨 COLOR PALETTE
            # ==============================
            colors = [
                "#636EFA", "#EF553B", "#00CC96",
                "#AB63FA", "#FFA15A", "#19D3F3",
                "#7f7f7f"  # Others (abu)
            ]
            
            # ==============================
            # 🧩 PIE CHART
            # ==============================
            fig_root = px.pie(
                df_final,
                names="Root Cause",
                values="Total",
                hole=0.5,
                color_discrete_sequence=colors
            )
            
            # 🔥 TEXT DI TENGAH (LEBIH BERGUNA)
            fig_root.update_layout(
                annotations=[dict(
                    text=f"{df_final['Total'].sum()} Issues",
                    x=0.5, y=0.5,
                    font_size=13,
                    showarrow=False
                )],
                template="plotly_dark",
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            # 🔥 LABEL DI PIE (CLEAN)
            fig_root.update_traces(
                textinfo="percent",
                textposition="inside"
            )
            
            st.plotly_chart(fig_root, use_container_width=True)
