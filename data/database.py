import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

def save_to_csv(data, filename="analyses.csv"):
    """
    Save analyses data to CSV file
    
    Args:
        data: List of analysis records
        filename: Name of the CSV file
    """
    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv(filepath, index=False)
    
    return filepath

def load_from_csv(filename="analyses.csv"):
    """
    Load analyses data from CSV file
    
    Args:
        filename: Name of the CSV file
        
    Returns:
        DataFrame of analyses data
    """
    filepath = os.path.join("data", filename)
    
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        return pd.DataFrame()

def export_analysis_report(analysis_id, format="csv"):
    """
    Export an analysis report in the specified format
    
    Args:
        analysis_id: ID of the analysis to export
        format: Format to export (csv or json)
        
    Returns:
        Bytes of the exported file
    """
    if 'analyses' not in st.session_state:
        return None
    
    # Find the analysis
    analysis = None
    for a in st.session_state.analyses:
        if a['id'] == analysis_id:
            analysis = a
            break
    
    if analysis is None:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame([analysis])
    
    if format == "csv":
        return df.to_csv(index=False).encode('utf-8')
    elif format == "json":
        return json.dumps(analysis, default=str).encode('utf-8')
    else:
        return None
