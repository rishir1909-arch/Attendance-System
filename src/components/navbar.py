import streamlit as st


def navbar():
    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.page = "home"

    with col2:
        if st.button("📚 Subjects", use_container_width=True):
            st.session_state.page = "subjects"

    with col3:
        if st.button("📸 Attendance", use_container_width=True):
            st.session_state.page = "attendance"

    with col4:
        if st.button("📊 Reports", use_container_width=True):
            st.session_state.page = "reports"

    st.divider()


# Initialize page
if "page" not in st.session_state:
    st.session_state.page = "home"

navbar()

# Page Routing
if st.session_state.page == "home":
    st.title("🏠 Home")

elif st.session_state.page == "subjects":
    st.title("📚 Subjects")

elif st.session_state.page == "attendance":
    st.title("📸 Attendance")

elif st.session_state.page == "reports":
    st.title("📊 Reports")