import streamlit as st 

def apply_style():

    st.set_page_config(layout="wide")

    st.markdown("""
    <style>

    /* =========================
       HILANGIN HEADER STREAMLIT
    ========================= */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* =========================
       CONTAINER FULL & CENTER
    ========================= */
    .block-container {
        max-width: 100%; 
        margin: 0; 
        padding-top: 0.5rem;   /* 👈 kecilin biar ga kepotong */
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* =========================
       METRIC SIZE
    ========================= */
    [data-testid="stMetricValue"] {
        font-size: 36px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 16px;
    }

    /* =========================
       TITLE
    ========================= */
    h3 {
        font-size: 26px;
        margin-bottom: 0.5rem;
    }

    /* =========================
       SPACING ANTAR KOLOM
    ========================= */
    [data-testid="stHorizontalBlock"] {
        gap: 1.5rem;
    }

    </style>
    """, unsafe_allow_html=True)
