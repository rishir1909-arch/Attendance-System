import streamlit as st
import time
import numpy as np

import pandas as pd 

from src.ui.base_layout import style_base_layout, style_background_dashboard
from src.components.header import header_dashboard
from src.database.config import supabase
from datetime import datetime
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card 
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog
from src.components.dialog_add_photos import add_photos_dialog
from src.components.dialog_attendance_results import attendance_result_dialog
from src.pipelines.face_pipelines import predict_attendance


from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login, get_teacher_subjects,get_attendance_for_teacher
)


def teacher_screen():
    style_background_dashboard()
    style_base_layout()

    if st.session_state.get("teacher_data"):
        teacher_dashboard()

    elif (
        "teacher_login_type" not in st.session_state
        or st.session_state.teacher_login_type == "login"
    ):
        teacher_screen_login()

    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


def teacher_dashboard():

    teacher_data = st.session_state.teacher_data

    c1, c2 = st.columns(2, vertical_alignment="center", gap="xxlarge")

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"Welcome, {teacher_data['name']}")

        if st.button(
            "Logout",
            type="secondary",
            key="logout_btn"
        ):
            st.session_state["is_logged_in"] = False
            st.session_state.pop("teacher_data", None)
            st.session_state.pop("user_role", None)
            st.rerun()

    st.divider()

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)

    with tab1:
        type1 = (
            "primary"
            if st.session_state.current_teacher_tab == "take_attendance"
            else "secondary"
        )

        if st.button(
            "Take Attendance",
            type=type1,
            width="stretch",
            key="attendance_tab"
        ):
            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()

    with tab2:
        type2 = (
            "primary"
            if st.session_state.current_teacher_tab == "manage_subjects"
            else "secondary"
        )

        if st.button(
            "Manage Subjects",
            type=type2,
            width="stretch",
            key="subjects_tab"
        ):
            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()

    with tab3:
        type3 = (
            "primary"
            if st.session_state.current_teacher_tab == "attendance_records"
            else "secondary"
        )

        if st.button(
            "Attendance Records",
            type=type3,
            width="stretch",
            key="records_tab"
        ):
            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()
            
    if st.session_state.current_teacher_tab == "take_attendance":
        teacher_tab_take_attendance()
    if st.session_state.current_teacher_tab == "manage_subjects":
        teacher_tab_manage_subjects()
    if st.session_state.current_teacher_tab == "attendance_records":
        teacher_tab_attendance_records()    
    

    st.divider()

    # Display selected tab content
    if st.session_state.current_teacher_tab == "take_attendance":
        st.header("Take Attendance")
        st.write("Attendance functionality goes here.")

    elif st.session_state.current_teacher_tab == "manage_subjects":
        st.header("Manage Subjects")
        st.write("Subject management functionality goes here.")

    elif st.session_state.current_teacher_tab == "attendance_records":
        st.header("Attendance Records")
        st.write("Attendance records functionality goes here.")

    footer_dashboard()

def teacher_tab_take_attendance():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')

    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:
        st.warning('You haven’t created any subjects yet! Please create one to begin!')
        return

    subject_options = {
        f"{s['name']} - {s['subject_code']}": s['subject_id']
        for s in subjects
    }

    col1, col2 = st.columns([3, 1])

    with col1:
        selected_subject_label = st.selectbox(
            'Select Subject',
            options=list(subject_options.keys())
        )

    with col2:
        if st.button(
            '📷 Add Photos',
            type='primary',
            use_container_width=True
        ):
            add_photos_dialog()

    selected_subject_id = subject_options[selected_subject_label]

    st.divider()

    # ---------------- ALWAYS SHOW ACTION BUTTONS ----------------
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            'Clear all photos 🗑️',
            use_container_width=True,
            type='secondary'
        ):
            st.session_state.attendance_images = []
            st.rerun()

    with c2:
        has_photos = bool(st.session_state.attendance_images)

        if st.button(
            'Run Face Analysis 📊',
            use_container_width=True,
            type='primary'
        ):
            if not has_photos:
                st.warning("Please add photos first!")
            with st.spinner('Deep scanning classroom photos...'):
                    all_detected_ids = {}

                    for idx, img in enumerate(st.session_state.attendance_images):
                        img_np = np.array(img.convert('RGB'))

                        detected, _, _ = predict_attendance(img_np)

                        if detected:
                            for sid in detected.keys():
                                student_id = int(sid)
                                all_detected_ids.setdefault(student_id, []).append(
                                    f"Photo {idx + 1}"
                                )

                    enrolled_res = (
                        supabase.table('subject_students')
                        .select("*, students(*)")
                        .eq('subject_id', selected_subject_id)
                        .execute()
                    )

                    enrolled_students = enrolled_res.data

                    if not enrolled_students:
                        st.warning('No students enrolled in this course')
                        return

                    results, attendance_to_log = [], []
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

                    for node in enrolled_students:
                        student = node['students']

                        sources = all_detected_ids.get(int(student['student_id']), [])
                        is_present = len(sources) > 0

                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })

                        attendance_to_log.append({
                            "student_id": student['student_id'],
                            "subject_id": selected_subject_id,
                            "timestamp": current_timestamp,
                            "is_present": is_present
                        })

            attendance_result_dialog(pd.DataFrame(results),attendance_to_log)

    with c3:
        if st.button(
            'Use Voice Attendance 🎙️',
            type='primary',
            use_container_width=True
        ):
            voice_attendance_dialog(selected_subject_id)

    # ---------------- IMAGE GALLERY ONLY ----------------
    if st.session_state.attendance_images:
        st.header('Added Photos')
        gallery_cols = st.columns(4)

        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, use_container_width=True, caption=f'Photo {idx + 1}')
    
def teacher_tab_manage_subjects():
    teacher_id = st.session_state.teacher_data['teacher_id']

    col1, col2 = st.columns(2)

    with col1:
        st.header("Manage Subjects")

    with col2:
        if st.button(
            "Create New Subject",
            width="stretch",
            key="create_subject_btn"
        ):
            create_subject_dialog(teacher_id)

    subjects = get_teacher_subjects(teacher_id)

    if subjects:

        for sub in subjects:

            stats = [
                ("👥", "Students", sub.get('total_students', 0)),
                ("⌚", "Classes", sub.get('total_classes', 0)),
            ]

            def share_btn(subject=sub):
                if st.button(
                    f"Share Code 🔗: {subject['subject_code']}",
                    key=f"share_{subject['subject_code']}"
                ):
                    share_subject_dialog(sub['name'],sub['subject_code'])
                st.space()

            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=stats,
                footer_callback=share_btn
            )

    else:
        st.info("No subjects found. Create one above.")
            
    
def teacher_tab_attendance_records():
    st.header("Attendance Records")

    teacher_id = st.session_state.teacher_data['teacher_id']

    records = get_attendance_for_teacher(teacher_id)

    if not records:
        st.info("No attendance records found.")
        return

    data = []

    for r in records:
        ts = r.get('timestamp')

        data.append({
            "ts_group": ts.split(".")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "N/A",
            "Subject": r['subjects']['name'],
            "Subject Code": r['subjects']['subject_code'],
            "is_present": bool(r.get('is_present', False))
        })

    df = pd.DataFrame(data)

    summary = (
        df.groupby(['ts_group', 'Time', 'Subject', 'Subject Code'])
        .agg(
            Present_Count=('is_present', 'sum'),
            Total_Count=('is_present', 'count')
        )
        .reset_index()
    )

    summary['Attendance Stats'] = (
        "✅ "
        + summary['Present_Count'].astype(str)
        + " / "
        + summary['Total_Count'].astype(str)
        + " Students"
    )

    display_df = (
        summary
        .sort_values(by='ts_group', ascending=False)
        [['Time', 'Subject', 'Subject Code', 'Attendance Stats']]
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    
def login_tea(teacher_username, teacher_password):

    if not teacher_username or not teacher_password:
        return False

    teacher = teacher_login(
        teacher_username,
        teacher_password
    )

    if teacher:
        st.session_state.user_role = "teacher"
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True

    return False


def register_teacher(
    teacher_username,
    teacher_name,
    teacher_pass,
    teacher_pass_confirm
):

    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All fields are required!"

    if check_teacher_exists(teacher_username):
        return False, "Username already taken!"

    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords do not match!"

    try:
        create_teacher(
            teacher_username,
            teacher_pass,
            teacher_name
        )

        return True, "Teacher account created successfully!"

    except Exception as e:
        return False, f"Error: {str(e)}"


def teacher_screen_login():

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge"
    )

    with c1:
        header_dashboard()

    with c2:
        if st.button(
            "Go back to home",
            type="secondary",
            key="teacher_home_btn"
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Login Using Password")

    teacher_username = st.text_input(
        "Enter Username",
        placeholder="nilima_singh"
    )

    teacher_password = st.text_input(
        "Enter Password",
        type="password"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button(
            "Login",
            width="stretch",
            key="teacher_login_btn"
        ):
            if login_tea(
                teacher_username,
                teacher_password
            ):
                st.toast("Welcome back!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(
                    "Invalid username/password combination"
                )

    with btnc2:
        if st.button(
            "Register",
            type="primary",
            width="stretch",
            key="goto_register_btn"
        ):
            st.session_state.teacher_login_type = "register"
            st.rerun()

    footer_dashboard()


def teacher_screen_register():

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge"
    )

    with c1:
        header_dashboard()

    with c2:
        if st.button(
            "Go back to home",
            type="secondary",
            key="register_home_btn"
        ):
            st.session_state["login_type"] = None
            st.rerun()

    st.header("Register Your Teacher Profile")

    teacher_username = st.text_input(
        "Enter Username",
        placeholder="nilima_singh"
    )

    teacher_name = st.text_input(
        "Enter Name",
        placeholder="Nilima Singh"
    )

    teacher_pass = st.text_input(
        "Enter Password",
        type="password"
    )

    teacher_pass_confirm = st.text_input(
        "Confirm Password",
        type="password"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:
        if st.button(
            "Register Now",
            width="stretch",
            key="register_teacher_btn"
        ):
            success, message = register_teacher(
                teacher_username,
                teacher_name,
                teacher_pass,
                teacher_pass_confirm
            )

            if success:
                st.success(message)
                time.sleep(2)

                st.session_state.teacher_login_type = "login"
                st.rerun()

            else:
                st.error(message)

    with btnc2:
        if st.button(
            "Login Instead",
            width="stretch",
            type="primary",
            key="login_instead_btn"
        ):
            st.session_state.teacher_login_type = "login"
            st.rerun()

    footer_dashboard() 
# 51hikNEosX4wEh9U
