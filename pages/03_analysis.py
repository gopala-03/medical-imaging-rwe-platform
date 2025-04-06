import streamlit as st
import torch
import numpy as np
import os
import cv2
from PIL import Image
from utils.image_processing import preprocess_image_for_model
from utils.model import predict
from utils.data_handling import initialize_session_state, save_analysis_result
from utils.visualization import overlay_heatmap_on_image, create_prediction_bar_chart
from assets.grad_cam import generate_gradcam

def app():
    st.title("Image Analysis")
    
    # Initialize session state
    initialize_session_state()
    
    # Check prerequisites
    if st.session_state.current_image is None:
        st.warning("Please upload an image first.")
        if st.button("Go to Upload Page"):
            st.switch_page("pages/01_upload.py")
        return
    
    if not st.session_state.patient_data.get('id'):
        st.warning("Please provide patient information.")
        if st.button("Go to Patient Data"):
            st.switch_page("pages/02_patient_data.py")
        return
    
    # Display basic information
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(st.session_state.current_image_array, caption="Uploaded Image", use_column_width=True)
    
    with col2:
        st.markdown("### Patient Information")
        st.write(f"**ID:** {st.session_state.patient_data.get('id', 'N/A')}")
        st.write(f"**Name:** {st.session_state.patient_data.get('name', 'N/A')}")
        st.write(f"**Age:** {st.session_state.patient_data.get('age', 'N/A')}")
        st.write(f"**Gender:** {st.session_state.patient_data.get('gender', 'N/A')}")
        
        if st.session_state.patient_data.get('symptoms'):
            st.markdown(f"**Symptoms:** {st.session_state.patient_data.get('symptoms', 'N/A')}")
    
    # Analysis section with clear user guidance
    st.markdown("## AI-Powered Analysis")
    
    # Help information
    with st.expander("Understanding the AI Analysis"):
        st.markdown("""
        ### How our AI works
        
        Our system uses deep learning to analyze medical images:
        
        1. **Image Processing**: Your image is preprocessed to match our model's requirements
        2. **Neural Network Analysis**: A trained model evaluates the image for patterns
        3. **Results Interpretation**: The AI highlights areas of concern with a heatmap
        4. **Diagnostic Suggestion**: Based on patterns recognized in thousands of images
        
        The AI model is trained to recognize patterns associated with:
        - **Normal** lung appearance
        - **Pneumonia** (bacterial/viral)
        - **COVID-19** related findings
        
        *Note: This analysis is meant to assist healthcare professionals, not replace clinical judgment.*
        """)
    
    # Check if we already have a prediction
    if 'current_prediction' not in st.session_state or st.session_state.current_prediction is None:
        # More visible and attractive analysis button
        start_col1, start_col2, start_col3 = st.columns([1, 2, 1])
        with start_col2:
            start_analysis = st.button("🔍 Start AI Analysis", use_container_width=True, type="primary")
        
        if start_analysis:
            with st.spinner("Running AI analysis... Please wait while our model examines the image."):
                try:
                    # Preprocess the image
                    image_tensor = preprocess_image_for_model(st.session_state.current_image_array)
                    
                    # Make prediction
                    class_idx, class_label, confidence = predict(
                        st.session_state.model,
                        image_tensor,
                        st.session_state.device
                    )
                    
                    # Generate Grad-CAM
                    gradcam = generate_gradcam(
                        st.session_state.model,
                        image_tensor,
                        class_idx,
                        st.session_state.device
                    )
                    
                    # Overlay Grad-CAM on image
                    overlay = overlay_heatmap_on_image(
                        st.session_state.current_image_array,
                        gradcam
                    )
                    
                    # Save results
                    st.session_state.current_prediction = {
                        'class_idx': class_idx,
                        'class_label': class_label,
                        'confidence': confidence,
                        'gradcam': gradcam,
                        'overlay': overlay
                    }
                    
                    # Save analysis to session state
                    analysis_id = save_analysis_result(
                        st.session_state.patient_data,
                        st.session_state.current_image_path,
                        class_label,
                        confidence
                    )
                    
                    st.session_state.current_analysis_id = analysis_id
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")
    else:
        # Display prediction results
        prediction = st.session_state.current_prediction
        
        # Create columns for results and visualization
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Prediction Results")
            st.markdown(f"**Diagnosis:** {prediction['class_label']}")
            st.markdown(f"**Confidence:** {prediction['confidence']:.2f}")
            
            # Display prediction confidence as a bar chart
            fig = create_prediction_bar_chart(prediction['class_label'], prediction['confidence'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Visualization")
            
            # Toggle for heatmap
            show_heatmap = st.checkbox("Show AI Attention Map", value=True)
            
            if show_heatmap:
                st.image(prediction['overlay'], caption="AI Attention Map", use_container_width=True)
                st.info("The colored overlay shows areas that the AI focused on to make its diagnosis.")
            else:
                st.image(st.session_state.current_image_array, caption="Original Image", use_container_width=True)
        
        # Analysis findings with enhanced UI and recommendations
        st.markdown("### Analysis Findings")
        
        # Create an attractive findings box
        findings_container = st.container()
        
        with findings_container:
            if prediction['class_label'] == 'Normal':
                st.success("No significant abnormalities detected in the chest X-ray.")
                st.markdown("""
                **Recommendations:**
                - Routine follow-up as clinically indicated
                - Continue preventive care measures
                - Document as normal baseline for future comparisons
                """)
            elif prediction['class_label'] == 'Pneumonia':
                st.warning("""
                **Findings suggestive of Pneumonia:**
                - The AI model has detected patterns consistent with pneumonia
                - Areas of consolidation may be present in the lungs
                - Clinical correlation is recommended
                """)
                st.markdown("""
                **Recommendations:**
                - Consider laboratory tests (CBC, CRP) to confirm infection
                - Assess oxygen saturation and respiratory status
                - Consider antibiotic therapy if bacterial pneumonia is suspected
                - Follow-up imaging in 4-6 weeks to confirm resolution
                """)
            elif prediction['class_label'] == 'COVID-19':
                st.error("""
                **Findings suggestive of COVID-19:**
                - The AI model has detected patterns consistent with COVID-19 pneumonia
                - Typical findings include ground-glass opacities and peripheral consolidations
                - These findings have a characteristic distribution pattern
                """)
                st.markdown("""
                **Recommendations:**
                - Perform COVID-19 PCR or antigen testing for confirmation
                - Implement appropriate isolation precautions
                - Monitor oxygen saturation closely
                - Consider treatment options based on current clinical guidelines
                - Follow-up imaging as appropriate based on clinical course
                """)
            
            # Add interactive notes section for the clinician
            st.markdown("### Clinical Notes")
            clinical_notes = st.text_area("Add your clinical observations and plan:", height=100,
                                         placeholder="Enter your clinical impression and treatment plan here...")
            
            if clinical_notes:
                st.session_state.clinical_notes = clinical_notes
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("New Analysis"):
                # Clear current image and prediction
                st.session_state.current_image = None
                st.session_state.current_image_array = None
                st.session_state.current_prediction = None
                st.switch_page("pages/01_upload.py")
        
        with col2:
            if st.button("View Dashboard"):
                st.switch_page("pages/04_dashboard.py")

if __name__ == "__main__":
    app()
