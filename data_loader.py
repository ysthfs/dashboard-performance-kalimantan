import pandas as pd
import os
import streamlit as st
from utils import minutes_to_hhmm

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    try: 
        base_path = os.path.dirname(__file__)
        file_path = os.path.join(base_path, "data", "data_tiket.xlsx")

        df = pd.read_excel(file_path, engine="openpyxl")

        required_cols = ["Status TT", "SLA Duration Closed", "Month"]
        for col in required_cols:
            if col not in df.columns:
                st.error(f"Kolom '{col}' tidak ditemukan di file Excel")
                return pd.DataFrame()

        # CLEANING
        df["Status TT"] = df["Status TT"].fillna("").astype(str).str.strip().str.lower()
        df["Month"] = df["Month"].astype(str).str.strip().str.title()

        df["SLA Duration Closed"] = pd.to_timedelta(
            df["SLA Duration Closed"], errors="coerce"
        )

        df["SLA Duration Closed"] = df["SLA Duration Closed"].dt.total_seconds() / 60
        df = df.dropna(subset=["SLA Duration Closed"])

        return df

    except Exception as e:
        st.error(f"Gagal load data: {e}")
        return pd.DataFrame()


# ==============================
# PROCESS DATA
# ==============================
@st.cache_data
def process_data(df):
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_closed = df[df["Status TT"] == "close"]

    if df_closed.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_group = df_closed.groupby("Month").agg({
        "Status TT": "count",
        "SLA Duration Closed": "mean"
    }).reset_index()

    df_group.columns = ["Month", "TT Closed", "Avg SLA (Minutes)"]

    month_order = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December"
    ]

    df_group["Month"] = pd.Categorical(
        df_group["Month"], categories=month_order, ordered=True
    )

    df_group = df_group.sort_values("Month")

    # FORMAT
    df_display = df_group.copy()

    df_display["Avg SLA (Minutes)"] = df_display["Avg SLA (Minutes)"].apply(
        lambda x: f"{int(x//60):02d}:{int(x%60):02d}" if pd.notnull(x) else "00:00"
    )

    df_group["Avg SLA (HH:MM)"] = df_group["Avg SLA (Minutes)"].apply(
        minutes_to_hhmm
    )

    return df_group, df_display
