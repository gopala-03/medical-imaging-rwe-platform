import streamlit as st
import os
import requests
import pandas as pd
import json
import tempfile
import zipfile
import io
from utils.database import import_nih_metadata, import_bbox_data

def check_kaggle_credentials():
    """
    Check if Kaggle API credentials are available
    
    Returns:
        Boolean indicating if credentials are available
    """
    # Check if credentials are in session state
    if 'kaggle_username' in st.session_state and 'kaggle_key' in st.session_state:
        return True
    
    # Check if credentials are in environment variables
    if os.environ.get('KAGGLE_USERNAME') and os.environ.get('KAGGLE_KEY'):
        # Store in session state for later use
        st.session_state.kaggle_username = os.environ.get('KAGGLE_USERNAME')
        st.session_state.kaggle_key = os.environ.get('KAGGLE_KEY')
        return True
    
    return False

def save_kaggle_credentials(username, key):
    """
    Save Kaggle API credentials to session state
    
    Args:
        username: Kaggle username
        key: Kaggle API key
    """
    st.session_state.kaggle_username = username
    st.session_state.kaggle_key = key

def download_nih_metadata(sample_size=None):
    """
    Download metadata from the NIH Chest X-ray dataset from Kaggle
    
    Args:
        sample_size: Optional sample size to limit downloaded records
        
    Returns:
        Path to downloaded CSV file and success status
    """
    if not check_kaggle_credentials():
        return None, False, "Kaggle credentials not found. Please provide them."
    
    try:
        # Set up the API endpoint
        dataset_name = "nih-chest-xrays/data"
        file_name = "Data_Entry_2017.csv"
        
        # API endpoint for dataset file download
        kaggle_api_url = f"https://www.kaggle.com/api/v1/datasets/download/{dataset_name}/{file_name}"
        
        # Prepare authentication
        auth = (st.session_state.kaggle_username, st.session_state.kaggle_key)
        
        # Download the file
        with st.spinner(f"Downloading {file_name} from Kaggle..."):
            response = requests.get(kaggle_api_url, auth=auth)
            
            if response.status_code != 200:
                return None, False, f"Download failed with status code {response.status_code}: {response.text}"
            
            # Save the file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # If sample size is specified, load only a sample
            if sample_size:
                try:
                    df = pd.read_csv(temp_file_path, nrows=sample_size)
                    df.to_csv(temp_file_path, index=False)
                except Exception as e:
                    return None, False, f"Error sampling data: {str(e)}"
            
            return temp_file_path, True, "Download successful"
            
    except Exception as e:
        return None, False, f"Error downloading file: {str(e)}"

def download_nih_bbox_data():
    """
    Download bounding box data from the NIH Chest X-ray dataset from Kaggle
    
    Returns:
        Path to downloaded CSV file and success status
    """
    if not check_kaggle_credentials():
        return None, False, "Kaggle credentials not found. Please provide them."
    
    try:
        # Set up the API endpoint
        dataset_name = "nih-chest-xrays/data"
        file_name = "BBox_List_2017.csv"
        
        # API endpoint for dataset file download
        kaggle_api_url = f"https://www.kaggle.com/api/v1/datasets/download/{dataset_name}/{file_name}"
        
        # Prepare authentication
        auth = (st.session_state.kaggle_username, st.session_state.kaggle_key)
        
        # Download the file
        with st.spinner(f"Downloading {file_name} from Kaggle..."):
            response = requests.get(kaggle_api_url, auth=auth)
            
            if response.status_code != 200:
                return None, False, f"Download failed with status code {response.status_code}: {response.text}"
            
            # Save the file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            return temp_file_path, True, "Download successful"
            
    except Exception as e:
        return None, False, f"Error downloading file: {str(e)}"

def import_nih_data_from_kaggle(sample_size=1000):
    """
    Download and import NIH dataset from Kaggle
    
    Args:
        sample_size: Number of records to download as sample
        
    Returns:
        Dictionary of import results
    """
    results = {
        "metadata": {
            "success": False,
            "count": 0,
            "message": ""
        },
        "bbox": {
            "success": False,
            "count": 0,
            "message": ""
        }
    }
    
    # Download metadata
    metadata_path, success, message = download_nih_metadata(sample_size)
    
    if success:
        # Import metadata to database
        try:
            with open(metadata_path, 'r') as file:
                count = import_nih_metadata(file)
                results["metadata"] = {
                    "success": True,
                    "count": count,
                    "message": f"Successfully imported {count} metadata records"
                }
        except Exception as e:
            results["metadata"]["message"] = f"Error importing metadata: {str(e)}"
        
        # Clean up
        try:
            os.remove(metadata_path)
        except:
            pass
    else:
        results["metadata"]["message"] = message
    
    # Download bbox data
    bbox_path, success, message = download_nih_bbox_data()
    
    if success:
        # Import bbox data to database
        try:
            with open(bbox_path, 'r') as file:
                count = import_bbox_data(file)
                results["bbox"] = {
                    "success": True,
                    "count": count,
                    "message": f"Successfully imported {count} bounding box records"
                }
        except Exception as e:
            results["bbox"]["message"] = f"Error importing bounding box data: {str(e)}"
        
        # Clean up
        try:
            os.remove(bbox_path)
        except:
            pass
    else:
        results["bbox"]["message"] = message
    
    return results