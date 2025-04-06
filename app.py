import streamlit as st
import os
import torch
import pandas as pd
from utils.data_handling import initialize_session_state
from utils.image_processing import setup_image_processors
from utils.model import load_model, get_model_path

st.set_page_config(
    page_title="MedImaging RWE Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "# Medical Imaging & Real World Evidence Platform\n\nThis application provides AI-powered analysis of medical images with patient data integration and analytical reporting."
    }
)

def main():
    # Initialize session state
    initialize_session_state()
    
    # Set up necessary directories
    os.makedirs("temp", exist_ok=True)
    
    # Setup image processors
    setup_image_processors()
    
    # Load model if not in session state
    if 'model' not in st.session_state:
        with st.spinner("Loading AI model..."):
            try:
                model_path = get_model_path()
                st.session_state.model = load_model(model_path)
                st.session_state.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            except Exception as e:
                st.error(f"Error loading model: {str(e)}")
                st.info("Using a fallback model configuration.")
                # Create a simple model for demonstration
                from utils.model import ChestXRayClassifier
                model = ChestXRayClassifier(num_classes=3)
                model.eval()
                st.session_state.model = model
                st.session_state.device = torch.device("cpu")
    
    # Main page content
    st.title("Medical Imaging & Real World Evidence Platform")
    
    # More attractive welcome section with better user guidance
    st.markdown("""
    ## Welcome to the Medical Imaging RWE Platform
    
    This comprehensive platform empowers healthcare professionals with AI-powered image analysis and clinical insights.
    """)
    
    # Create columns for features
    feat_col1, feat_col2 = st.columns(2)
    
    with feat_col1:
        st.markdown("""
        ### 📊 Key Features
        
        - **Multi-format Support**: Upload DICOM, PNG, or JPG medical images
        - **AI Analysis**: Advanced neural network classification of conditions
        - **Visual Heatmaps**: See what the AI focuses on in each image
        - **Clinical Integration**: Link with patient data and symptoms
        """)
    
    with feat_col2:
        st.markdown("""
        ### 🚀 Getting Started
        
        1. Use the **Upload** page to add medical images
        2. Enter **Patient Data** including demographics and symptoms
        3. Run **AI Analysis** to get diagnostic suggestions  
        4. View the **Dashboard** for population trends and comparisons
        
        **Navigate through these pages using the sidebar menu →**
        """)
        
    # Create call-to-action button
    if st.button("Begin New Analysis", type="primary"):
        st.switch_page("pages/01_upload.py")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Analyses")
        if 'analyses' in st.session_state and len(st.session_state.analyses) > 0:
            recent_analyses = pd.DataFrame(st.session_state.analyses[-5:])
            if not recent_analyses.empty:
                st.dataframe(recent_analyses[['patient_id', 'age', 'gender', 'prediction', 'confidence']], use_container_width=True)
        else:
            st.info("No analyses have been performed yet. Start by uploading an image.")
    
    with col2:
        st.subheader("System Status")
        st.write(f"Model status: **{'Loaded' if 'model' in st.session_state else 'Not loaded'}**")
        st.write(f"Device: **{st.session_state.device if 'device' in st.session_state else 'CPU'}**")
        st.write(f"Total analyses: **{len(st.session_state.analyses) if 'analyses' in st.session_state else 0}**")
        
        # Display dataset info with links to the dataset integration pages
        st.markdown("### Connected Datasets")
        
        # Create a card-style layout for datasets
        dataset_col1, dataset_col2 = st.columns(2)
        
        with dataset_col1:
            with st.container(border=True):
                st.markdown("#### NIH Chest X-ray Dataset")
                st.markdown("112,120 chest X-rays with disease labels from 30,805 patients")
                st.markdown("**15 disease classes** including pneumonia, edema, and more")
                if st.button("Explore NIH Dataset", key="nih_dataset"):
                    st.switch_page("pages/06_nih_dataset.py")
        
        with dataset_col2:
            with st.container(border=True):
                st.markdown("#### External Healthcare Data")
                st.markdown("Connections to external healthcare databases")
                st.markdown("**Real-world evidence** to enhance diagnostic insights")
                if st.button("Explore External Data", key="external_data"):
                    st.switch_page("pages/05_external_data.py")

if __name__ == "__main__":
    main()
