import streamlit as st
from utils.data_handling import initialize_session_state

def app():
    st.title("Patient Information")
    
    # Initialize session state
    initialize_session_state()
    
    # Check if an image was uploaded
    if st.session_state.current_image is None:
        st.warning("Please upload an image first.")
        if st.button("Go to Upload Page"):
            st.switch_page("pages/01_upload.py")
        return
    
    # Display the uploaded image
    if st.session_state.current_image_array is not None:
        st.image(st.session_state.current_image_array, caption="Uploaded Image", width=300)
    
    # Patient information form
    st.markdown("## Patient Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.patient_data['id'] = st.text_input(
            "Patient ID", 
            value=st.session_state.patient_data.get('id', '')
        )
        
        st.session_state.patient_data['name'] = st.text_input(
            "Patient Name", 
            value=st.session_state.patient_data.get('name', '')
        )
        
        st.session_state.patient_data['age'] = st.text_input(
            "Age", 
            value=st.session_state.patient_data.get('age', '')
        )
        
        st.session_state.patient_data['gender'] = st.selectbox(
            "Gender", 
            options=["", "Male", "Female", "Other"],
            index=["", "Male", "Female", "Other"].index(st.session_state.patient_data.get('gender', '')) if st.session_state.patient_data.get('gender', '') in ["", "Male", "Female", "Other"] else 0
        )
        
    with col2:
        st.session_state.patient_data['symptoms'] = st.text_area(
            "Symptoms", 
            value=st.session_state.patient_data.get('symptoms', '')
        )
        
        st.session_state.patient_data['medical_history'] = st.text_area(
            "Medical History", 
            value=st.session_state.patient_data.get('medical_history', '')
        )
    
    # Vital signs
    st.markdown("## Vital Signs")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.session_state.patient_data['temperature'] = st.text_input(
            "Temperature (°C)", 
            value=st.session_state.patient_data.get('temperature', '')
        )
    
    with col2:
        st.session_state.patient_data['blood_pressure'] = st.text_input(
            "Blood Pressure (mmHg)", 
            value=st.session_state.patient_data.get('blood_pressure', '')
        )
    
    with col3:
        st.session_state.patient_data['oxygen_saturation'] = st.text_input(
            "Oxygen Saturation (%)", 
            value=st.session_state.patient_data.get('oxygen_saturation', '')
        )
    
    with col4:
        st.session_state.patient_data['pulse_rate'] = st.text_input(
            "Pulse Rate (bpm)", 
            value=st.session_state.patient_data.get('pulse_rate', '')
        )
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Back to Upload"):
            st.switch_page("pages/01_upload.py")
    
    with col2:
        proceed = st.button("Proceed to Analysis")
        
        if proceed:
            # Validate essential fields
            if not st.session_state.patient_data['id']:
                st.error("Patient ID is required.")
            elif not st.session_state.patient_data['age']:
                st.error("Patient age is required.")
            elif not st.session_state.patient_data['gender']:
                st.error("Patient gender is required.")
            else:
                st.switch_page("pages/03_analysis.py")

if __name__ == "__main__":
    app()
