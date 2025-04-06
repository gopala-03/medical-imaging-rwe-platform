import streamlit as st
import numpy as np
import pydicom
import cv2
import os
import io
from PIL import Image
import tempfile
import torch
import torchvision.transforms as transforms

# Image preprocessing for model input
def preprocess_image_for_model(image_array):
    """
    Preprocess image for model input
    
    Args:
        image_array: Numpy array of the image
        
    Returns:
        Preprocessed tensor ready for model input
    """
    # Define preprocessing steps
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Convert to PIL Image
    if len(image_array.shape) == 2:  # If grayscale
        pil_image = Image.fromarray(image_array.astype('uint8'), 'L')
        # Convert to RGB for model compatibility
        pil_image = pil_image.convert('RGB')
    else:
        pil_image = Image.fromarray(image_array.astype('uint8'))
    
    # Apply preprocessing
    input_tensor = preprocess(pil_image)
    
    # Add batch dimension
    input_batch = input_tensor.unsqueeze(0)
    
    return input_batch

def read_dicom_file(file):
    """
    Read a DICOM file and return the pixel array
    
    Args:
        file: File-like object containing DICOM data
        
    Returns:
        Array of pixel data and metadata dict
    """
    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dcm') as tmp_file:
        tmp_file.write(file.getvalue())
        tmp_file_path = tmp_file.name
    
    # Read the DICOM file
    try:
        ds = pydicom.dcmread(tmp_file_path)
        
        # Extract metadata
        metadata = {
            'PatientID': getattr(ds, 'PatientID', 'Unknown'),
            'PatientName': str(getattr(ds, 'PatientName', 'Unknown')),
            'PatientAge': getattr(ds, 'PatientAge', 'Unknown'),
            'PatientSex': getattr(ds, 'PatientSex', 'Unknown'),
            'StudyDate': getattr(ds, 'StudyDate', 'Unknown'),
            'Modality': getattr(ds, 'Modality', 'Unknown'),
        }
        
        # Convert pixel data to numpy array
        img_array = ds.pixel_array
        
        # Normalize the image if needed
        if img_array.max() > 255:
            img_array = img_array / img_array.max() * 255
            
        img_array = img_array.astype(np.uint8)
        
        # Cleanup temporary file
        os.unlink(tmp_file_path)
        
        return img_array, metadata
    
    except Exception as e:
        # Cleanup temporary file
        os.unlink(tmp_file_path)
        raise e

def read_image_file(file):
    """
    Read a regular image file (PNG, JPG, etc.) and return the array
    
    Args:
        file: File-like object containing image data
        
    Returns:
        Array of pixel data
    """
    img = Image.open(io.BytesIO(file.getvalue()))
    return np.array(img), {}

def process_uploaded_file(uploaded_file):
    """
    Process an uploaded file based on its type
    
    Args:
        uploaded_file: The uploaded file from Streamlit
        
    Returns:
        Processed image array and metadata
    """
    if uploaded_file is None:
        return None, {}
    
    file_ext = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_ext == 'dcm':
            return read_dicom_file(uploaded_file)
        elif file_ext in ['png', 'jpg', 'jpeg']:
            return read_image_file(uploaded_file)
        else:
            st.error(f"Unsupported file format: {file_ext}")
            return None, {}
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None, {}

def setup_image_processors():
    """
    Set up any necessary components for image processing
    """
    # Create temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
