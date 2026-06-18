import streamlit as st

def header_home():
    
    logo_url = "https://img.freepik.com/free-vector/professional-business-woman-posing-with-documents_10045-816.jpg?semt=ais_hybrid&w=740&q=80"
    
    st.markdown(f"""
                <div
                    style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 30px; margin-top: 30px">
                        <img src = '{logo_url}' style = 'height: 170px'; />
                        <h1 style='text-align:center; color:#E0E3FF'>Snap-At</h1>
                </div>
                
                """, unsafe_allow_html=True)
    

def header_dashboard():
    logo_url = "https://img.freepik.com/free-vector/professional-business-woman-posing-with-documents_10045-816.jpg?semt=ais_hybrid&w=740&q=80"
    
    st.markdown(f"""
                <div
                    style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 30px; gap: 10px; margin-top: 30px">
                        <img src = '{logo_url}' style = 'height: 100px'; />
                        <h2 style='text-align:center; color:#5865F2'>Snap-At</h2>
                </div>
                
                
                """, unsafe_allow_html=True)