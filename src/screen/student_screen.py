import streamlit as st
import numpy as np
import time

from PIL import Image

from src.ui.base_layout import style_base_layout, style_background_dashboard
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.enroll_dialog import enroll_dialog
from src.components.subject_card import subject_card
from src.database.db import get_all_students, create_student, get_student_subjects, get_student_attendance, unenroll_student_to_subject, enroll_student_to_subject
from src.pipelines.face_pipelines import (
    predict_attendance,
    get_face_embeddings,   
    train_classifier
)
from src.pipelines.voice_pipelines import get_voice_embedding


def student_dashboard():

    student_data = st.session_state.student_data

    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"Welcome, {student_data['name']}")

        if st.button(
            "Logout",
            type="secondary",
            key="logout_btn"
        ):
            st.session_state["is_logged_in"] = False
            del st.session_state.student_data
            st.rerun()

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.header("Your Enrolled Subjects")

    with c2:
        if st.button(
            "Enroll in Subject",
            type="primary",
            use_container_width=True,
            key="enroll_subject_btn"
        ):
            enroll_dialog()

    st.divider()

    student_id = student_data["student_id"]

    with st.spinner("Loading your enrolled subjects..."):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log["subject_id"]

        if sid not in stats_map:
            stats_map[sid] = {
                "total": 0,
                "attended": 0
            }

        stats_map[sid]["total"] += 1

        if log.get("is_present"):
            stats_map[sid]["attended"] += 1

    cols = st.columns(2)

    for i, sub_node in enumerate(subjects):

        sub = sub_node["subjects"]
        sid = sub["subject_id"]

        stats = stats_map.get(
            sid,
            {
                "total": 0,
                "attended": 0
            }
        )

        with cols[i % 2]:

            subject_card(
                name=sub["name"],
                code=sub["subject_code"],
                section=sub["section"],
                stats=[
                    ("📚", "Total", stats["total"]),
                    ("✅", "Attended", stats["attended"]),
                ]
            )

            if st.button(
                "Unenroll from Course",
                key=f"unenroll_{sid}",
                type="tertiary",
                use_container_width=True
            ):
                unenroll_student_to_subject(
                    student_id,
                    sid
                )

                st.toast(
                    f"Unenrolled from {sub['name']} successfully!"
                )

                st.rerun()

    footer_dashboard()


def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')

    with c1:
        header_dashboard()

    with c2:
        if st.button(
            "Go back to Home",
            type='secondary',
            key='loginbackbtn'
        ):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using FaceID')

    photo_source = st.camera_input("Position your face in the center")

    show_registration = False

    if photo_source:

        img = np.array(Image.open(photo_source))

        with st.spinner('AI is scanning...'):

            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning('Face not found!')
                show_registration = True

            elif num_faces > 1:
                st.warning('Multiple faces found')
                show_registration = False

            elif detected:

                student_id = list(detected.keys())[0]

                all_students = get_all_students()

                student = next(
                    (
                        s for s in all_students
                        if str(s.get('student_id')) == str(student_id)
                    ),
                    None
                )

                if student:

                    st.session_state.is_logged_in = True
                    st.session_state.user_role = 'student'
                    st.session_state.student_data = student

                    st.toast(f"Welcome Back {student['name']}")

                    time.sleep(1)
                    st.rerun()

                else:
                    st.info('Face not recognised! Register below.')
                    show_registration = True

            else:
                st.info('Face not recognised! Register below.')
                show_registration = True

    if photo_source and show_registration:

        with st.container(border=True):

            st.header('Register New Profile')

            new_name = st.text_input(
                "Enter your name",
                placeholder="E.g. Rehan Rizvi"
            )

            st.subheader("Optional: Voice Enrollment")

            st.info(
                "Record a short phrase such as "
                "'I am present' or 'My name is Akash'."
            )

            audio_data = None

            try:
                audio_data = st.audio_input(
                    "Record your voice"
                )

            except Exception:
                st.error("Audio recording failed.")

            if st.button(
                "Create Account",
                type="primary"
            ):

                if not new_name:
                    st.warning("Please enter your name!")
                else:

                    with st.spinner("Creating profile..."):

                        img = np.array(Image.open(photo_source))

                        encodings = get_face_embeddings(img)

                        if encodings:

                            face_emb = encodings[0].tolist()

                            voice_emb = None

                            if audio_data:
                                voice_emb = get_voice_embedding(
                                    audio_data.read()
                                )

                            response_data = create_student(
                                new_name,
                                face_embedding=face_emb,
                                voice_embedding=voice_emb
                            )

                            if response_data:

                                train_classifier()

                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]

                                st.toast(
                                    f"Profile Created! Hi {new_name}"
                                )

                                time.sleep(1)
                                st.rerun()

                            else:
                                st.error(
                                    "Failed to create profile."
                                )

                        else:
                            st.error(
                                "Couldn't capture your facial features for registration."
                            )

    footer_dashboard()
