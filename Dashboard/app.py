"""Entry point: streamlit run app.py
 
Registers the chapters as pages of one multi-page dashboard.
"""
import streamlit as st
 
st.set_page_config(page_title="The World That Never Happened", layout="wide")
 
pages = [
    st.Page("chapter1.py", title="Ch. 1 - The future we expected", default=True),
    st.Page("chapter2.py", title="Ch. 2 - The shock hits"),
    st.Page("chapter3.py", title="Ch. 3 - Governments make their choices"),
    st.Page("chapter5.py", title="Ch. 5 - The recovery wasn't equal"),
]
st.navigation(pages).run()
 