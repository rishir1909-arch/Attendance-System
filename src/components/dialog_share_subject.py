import streamlit as st
import segno
import io

from src.database.db import create_subject

@st.dialog("Create New Subject")
def share_subject_dialog(subject_name, subject_code):
    
    app_domain = "snapAt-main.streamlit.app"
    join_url = f"{app_domain}/join_code={subject_code}"
    st.header("Scan to Join")
    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=10, border=1)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('### Copy Link')
        st.code(join_url, language="text")
        st.markdown(f'{subject_code} - {subject_name}')
        st.info('Copy this link to share on Whatapp or Email')
        
    with col2:
        st.markdown('### Scan to Join')
        st.image(out.getvalue(),  caption='QR-Code for class joining')
        
        
    