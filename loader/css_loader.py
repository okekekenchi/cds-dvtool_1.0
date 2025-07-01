import streamlit as st

@st.cache_resource  # Cache to prevent reloading on reruns
def load_css(*filenames):
    # Always load main.css
    with open("assets/css/main.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    if filenames:
        try:
            for file in filenames:
                with open(file) as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
                st.warning(f"CSS file not found: {file}")