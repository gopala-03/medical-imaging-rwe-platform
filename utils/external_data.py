import streamlit as st
import pandas as pd
import requests
import json
import os
from io import StringIO

def fetch_dataset_metadata():
    """
    Fetch metadata about available healthcare datasets
    
    Returns:
        Dictionary of dataset information
    """
    # In a real application, this would connect to an API
    # For demo purposes, we'll return static information
    
    return {
        "nih_chest_xray": {
            "name": "NIH Chest X-ray Dataset",
            "description": "Large dataset of chest X-ray images with various conditions",
            "source": "National Institutes of Health",
            "size": "112,120 images from 30,805 patients",
            "year": "2017",
            "conditions": ["Atelectasis", "Consolidation", "Infiltration", "Pneumothorax", 
                          "Edema", "Emphysema", "Fibrosis", "Effusion", "Pneumonia", 
                          "Pleural_Thickening", "Cardiomegaly", "Nodule", "Mass", "Hernia"],
            "url": "https://www.kaggle.com/datasets/nih-chest-xrays/data"
        },
        "covid_radiography": {
            "name": "COVID-19 Radiography Database",
            "description": "Chest X-ray images for COVID-19, normal, and viral pneumonia",
            "source": "IEEE Dataset",
            "size": "21,165 images",
            "year": "2020-2021",
            "conditions": ["COVID-19", "Normal", "Viral Pneumonia", "Lung Opacity"],
            "url": "https://www.kaggle.com/datasets/tawsifurrahman/covid19-radiography-database"
        },
        "nhs_chest_imaging": {
            "name": "NHS Chest Imaging Database",
            "description": "Collection of chest X-ray, CT and MRI from NHS hospitals",
            "source": "National Health Service (UK)",
            "size": "Varies by access agreement",
            "year": "2020-present",
            "conditions": ["COVID-19", "Various respiratory conditions"],
            "url": "https://nhsx.github.io/covid-chest-imaging-database/"
        }
    }

def fetch_sample_statistics(dataset_id="nih_chest_xray"):
    """
    Fetch sample statistics from a dataset
    
    Args:
        dataset_id: ID of the dataset to query
        
    Returns:
        DataFrame with statistics
    """
    # In a real application, this would connect to an API or database
    # For demo purposes, we'll generate sample statistics
    
    if dataset_id == "nih_chest_xray":
        # Sample age distribution
        age_data = {
            "age_group": ["0-20", "21-40", "41-60", "61-80", "80+"],
            "count": [1205, 5840, 12380, 8940, 2440]
        }
        
        # Sample condition prevalence
        condition_data = {
            "condition": ["Normal", "Pneumonia", "Effusion", "Infiltration", "Atelectasis", "Other"],
            "percentage": [53.8, 12.2, 10.9, 9.8, 8.5, 4.8]
        }
        
        return {
            "age_distribution": pd.DataFrame(age_data),
            "condition_prevalence": pd.DataFrame(condition_data)
        }
    
    elif dataset_id == "covid_radiography":
        # Sample distribution
        distribution_data = {
            "class": ["Normal", "COVID-19", "Viral Pneumonia", "Lung Opacity"],
            "count": [10192, 3616, 1345, 6012]
        }
        
        # Sample age distribution (fictional for demo)
        age_data = {
            "age_group": ["0-20", "21-40", "41-60", "61-80", "80+"],
            "count": [420, 2540, 7830, 6320, 4055]
        }
        
        return {
            "class_distribution": pd.DataFrame(distribution_data),
            "age_distribution": pd.DataFrame(age_data)
        }
    
    else:
        return None

def search_similar_cases(condition, age_range=None, gender=None, limit=5):
    """
    Search for similar cases in external datasets
    
    Args:
        condition: The condition to search for
        age_range: Optional tuple of (min_age, max_age)
        gender: Optional gender
        limit: Maximum number of results
        
    Returns:
        DataFrame with similar cases
    """
    # In a real application, this would perform an actual search
    # For demo purposes, we'll generate sample data
    
    # Map our conditions to dataset conditions
    condition_map = {
        "Normal": "Normal",
        "Pneumonia": "Pneumonia",
        "COVID-19": "COVID-19"
    }
    
    dataset_condition = condition_map.get(condition, condition)
    
    # Generate fictional sample data
    import numpy as np
    
    n_samples = min(limit, 10)  # At most 10 samples
    
    # Generate ages within range if specified
    if age_range:
        min_age, max_age = age_range
        ages = np.random.randint(min_age, max_age + 1, size=n_samples)
    else:
        ages = np.random.randint(20, 90, size=n_samples)
    
    # Generate genders
    if gender:
        genders = [gender] * n_samples
    else:
        genders = np.random.choice(["Male", "Female"], size=n_samples)
    
    # Generate confidence scores
    confidences = np.random.uniform(0.65, 0.99, size=n_samples)
    
    # Create sample data
    data = {
        "case_id": [f"EXT-{i:04d}" for i in range(1, n_samples + 1)],
        "age": ages,
        "gender": genders,
        "condition": [dataset_condition] * n_samples,
        "confidence": confidences,
        "source": np.random.choice(["NIH", "COVID-19-Rad", "NHS"], size=n_samples),
        "metadata": ["View details"] * n_samples
    }
    
    return pd.DataFrame(data)

def connect_to_dataset_api(api_key=None, dataset_id="nih_chest_xray"):
    """
    Connect to a dataset API
    
    Args:
        api_key: API key for authentication
        dataset_id: ID of the dataset to connect to
        
    Returns:
        Success status and connection information
    """
    # In a real application, this would establish a connection
    # For demo purposes, we'll simulate a connection
    
    if api_key:
        # Store the API key in session state
        st.session_state.dataset_api_key = api_key
        
        return {
            "status": "connected",
            "dataset": dataset_id,
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "access_level": "read-only",
            "message": f"Successfully connected to {dataset_id}"
        }
    else:
        return {
            "status": "error",
            "message": "API key is required for connection"
        }

def has_external_data_access():
    """
    Check if the user has external data access
    
    Returns:
        Boolean indicating whether user has access
    """
    return hasattr(st.session_state, 'dataset_api_key') and st.session_state.dataset_api_key is not None

def get_dataset_insights(dataset_id="nih_chest_xray", condition=None):
    """
    Get insights from dataset for a specific condition
    
    Args:
        dataset_id: ID of the dataset to query
        condition: Optional condition to filter by
        
    Returns:
        Dictionary of insights
    """
    # In a real application, this would analyze actual data
    # For demo purposes, we'll provide sample insights
    
    insights = {
        "Normal": {
            "age_distribution": {
                "mean": 42.3,
                "median": 44.0,
                "min": 18,
                "max": 90
            },
            "gender_distribution": {
                "Male": 48.2,
                "Female": 51.8
            },
            "common_comorbidities": [
                "None", "Hypertension", "Asthma", "Diabetes"
            ]
        },
        "Pneumonia": {
            "age_distribution": {
                "mean": 56.7,
                "median": 58.0,
                "min": 2,
                "max": 94
            },
            "gender_distribution": {
                "Male": 52.4,
                "Female": 47.6
            },
            "common_comorbidities": [
                "COPD", "Asthma", "Smoking", "Immunosuppression"
            ],
            "avg_hospital_stay": 5.3,
            "mortality_rate": 3.8
        },
        "COVID-19": {
            "age_distribution": {
                "mean": 61.2,
                "median": 63.0,
                "min": 12,
                "max": 97
            },
            "gender_distribution": {
                "Male": 55.8,
                "Female": 44.2
            },
            "common_comorbidities": [
                "Hypertension", "Diabetes", "Obesity", "Cardiovascular disease"
            ],
            "avg_hospital_stay": 9.6,
            "mortality_rate": 7.2,
            "common_treatments": [
                "Oxygen therapy", "Antivirals", "Corticosteroids"
            ]
        }
    }
    
    if condition and condition in insights:
        return {"condition": condition, "data": insights[condition]}
    elif condition:
        return {"condition": condition, "data": None, "message": "No insights available for this condition"}
    else:
        # Return general dataset insights
        return {
            "dataset": dataset_id,
            "conditions": list(insights.keys()),
            "total_cases": {"Normal": 10192, "Pneumonia": 1345, "COVID-19": 3616},
            "message": "Select a specific condition for detailed insights"
        }