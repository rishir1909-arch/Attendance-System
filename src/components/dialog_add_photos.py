import streamlit as st
from PIL import Image


@st.dialog("Capture or Upload Photos")
def add_photos_dialog():

    st.write(
        "Add classroom photos to scan for attendance."
    )

    if "photo_tab" not in st.session_state:
        st.session_state.photo_tab = "camera"

    t1, t2 = st.columns(2)

    type_camera = (
        "primary"
        if st.session_state.photo_tab == "camera"
        else "tertiary"
    )

    type_upload = (
        "primary"
        if st.session_state.photo_tab == "upload"
        else "tertiary"
    )

    with t1:
        if st.button(
            "📷 Camera",
            type=type_camera,
            width="stretch"
        ):
            st.session_state.photo_tab = "camera"
            st.rerun()

    with t2:
        if st.button(
            "📁 Upload",
            type=type_upload,
            width="stretch"
        ):
            st.session_state.photo_tab = "upload"
            st.rerun()

    st.divider()

    if st.session_state.photo_tab == "camera":

        cam_photo = st.camera_input(
            "Take Snapshot",
            key="dialog_cam"
        )

        if cam_photo:

            st.session_state.attendance_images.append(
                Image.open(cam_photo)
            )

            st.toast("Photo captured!")
            st.rerun()

    elif st.session_state.photo_tab == "upload":

        uploaded_files = st.file_uploader(
            "Choose image files",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="dialog_upload"
        )

        if uploaded_files:

            for file in uploaded_files:
                st.session_state.attendance_images.append(
                    Image.open(file)
                )

            st.toast(
                f"{len(uploaded_files)} photo(s) uploaded!"
            )

            st.rerun()

    st.divider()

    if st.button(
        "Done",
        type="primary",
        width="stretch"
    ):
        st.rerun()