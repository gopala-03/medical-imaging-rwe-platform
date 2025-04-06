import streamlit as st
import os
import tempfile
import uuid
from datetime import datetime
from utils.image_processing import process_uploaded_file
from utils.data_handling import initialize_session_state

def app():
    st.title("Upload Medical Images")
    
    # Initialize session state
    initialize_session_state()
    
    # Instructions with improved user guidance
    st.markdown("""
    ## Image Upload
    
    Upload your medical images (DICOM, PNG, JPG) for analysis. The system supports:
    - Chest X-rays
    - CT scans
    - Other radiological images
    
    After uploading, you'll be able to add patient information and run AI analysis.
    """)
    
    # Add a helpful tutorial/guide
    with st.expander("How to use this tool"):
        st.markdown("""
        ### Quick Start Guide
        
        1. **Select an image file** using the upload button below
        2. **Review the image** to ensure it loaded correctly
        3. **Click 'Proceed to Patient Data'** to enter clinical information
        4. **Complete the analysis** on the next screens
        
        The AI will analyze the image for possible conditions including Normal findings, Pneumonia, and COVID-19.
        """)
        
    # User feedback section
    with st.expander("Having trouble uploading?"):
        st.markdown("""
        ### Troubleshooting
        
        - Ensure your image is in DICOM (.dcm), PNG (.png), or JPG (.jpg/.jpeg) format
        - DICOM files will automatically extract patient metadata if available
        - Maximum file size: 200MB
        - If your upload fails, try converting your image to PNG format
        
        Need more help? Contact technical support.
        """)
    
    # File uploader
    uploaded_file = st.file_uploader("Choose an image file", type=["dcm", "png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        # Process the uploaded file
        image_array, metadata = process_uploaded_file(uploaded_file)
        
        if image_array is not None:
            # Save the image to session state
            st.session_state.current_image = uploaded_file
            st.session_state.current_image_array = image_array
            
            # Pre-fill patient data if available from DICOM metadata
            if metadata:
                if 'PatientID' in metadata and metadata['PatientID'] != 'Unknown':
                    st.session_state.patient_data['id'] = metadata['PatientID']
                
                if 'PatientName' in metadata and metadata['PatientName'] != 'Unknown':
                    st.session_state.patient_data['name'] = metadata['PatientName']
                
                if 'PatientAge' in metadata and metadata['PatientAge'] != 'Unknown':
                    # Extract numeric age if in format like '045Y'
                    age_str = metadata['PatientAge']
                    if age_str.endswith('Y'):
                        try:
                            st.session_state.patient_data['age'] = int(age_str[:-1])
                        except:
                            pass
                
                if 'PatientSex' in metadata and metadata['PatientSex'] != 'Unknown':
                    gender_map = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
                    st.session_state.patient_data['gender'] = gender_map.get(metadata['PatientSex'], metadata['PatientSex'])
            
            # Display the image
            st.image(image_array, caption=f"Uploaded image: {uploaded_file.name}", use_column_width=True)
            
            # Save the image to a temporary file
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate a unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            file_ext = uploaded_file.name.split('.')[-1].lower()
            temp_filename = f"{timestamp}_{unique_id}.{file_ext}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            # Save the file
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            st.session_state.current_image_path = temp_path
            
            # Proceed to patient data page button
            if st.button("Proceed to Patient Data"):
                st.session_state.current_page = "patient_data"
                st.rerun()
        else:
            st.error("Failed to process the uploaded image. Please try another file.")
    
    # Information about supported formats
    with st.expander("Supported Image Formats"):
        st.markdown("""
        ### DICOM (.dcm)
        - Standard format for medical imaging
        - Contains image data and patient metadata
        
        ### PNG, JPG/JPEG
        - Common image formats
        - Use for digitized X-rays or screenshots
        
        For best results, use DICOM format whenever available as it preserves important medical metadata.
        """)

if __name__ == "__main__":
    app()
