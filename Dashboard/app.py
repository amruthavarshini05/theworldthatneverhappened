"""Entry point: streamlit run app.py
 
One multi-page dashboard: introduction, five chapters, conclusion.
"""
import streamlit as st
 
st.set_page_config(page_title="The World That Never Happened", layout="wide")
 
pages = [
    st.Page("intro.py", title="Introduction", default=True),
    st.Page("chapter1.py", title="Ch. 1 - The future we expected"),
    st.Page("chapter2.py", title="Ch. 2 - The shock hits"),
    st.Page("chapter3.py", title="Ch. 3 - Governments make their choices"),
    st.Page("chapter4.py", title="Ch. 4 - Not every country starts with the same cards"),
    st.Page("chapter5.py", title="Ch. 5 - The recovery wasn't equal"),
    st.Page("conclusion.py", title="Conclusion"),
]
st.navigation(pages).run()
 