# -*- coding: utf-8 -*-

import streamlit as st

from app.app_context import get_app_context


st.set_page_config(page_title="Enverus Well Production Analyzer", page_icon="🛢️", layout="wide")

st.markdown("# 🛢️ Enverus Well Production Analyzer")
st.caption(
    "Use the pages in the sidebar to navigate: Individual Wells, P10/P50/P90, P50 Type Curve, EUR Summary."
)

# Initialize shared context (data + fits + outlier exclusion)
ctx = get_app_context()
st.caption(f"Using bundled data file: `{ctx['data_file_name']}`")
