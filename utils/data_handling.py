import streamlit as st
import pandas as pd
import json
import os
import datetime
import uuid

def initialize_session_state():
    """
    Initialize session state variables
    """
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = {
            'id': '',
            'name': '',
            'age': '',
            'gender': '',
            'symptoms': '',
            'medical_history': '',
            'temperature': '',
            'blood_pressure': '',
            'oxygen_saturation': '',
            'pulse_rate': '',
        }
    
    if 'current_image' not in st.session_state:
        st.session_state.current_image = None
    
    if 'current_image_array' not in st.session_state:
        st.session_state.current_image_array = None
    
    if 'current_prediction' not in st.session_state:
        st.session_state.current_prediction = None
        
    if 'analyses' not in st.session_state:
        st.session_state.analyses = []
    
    if 'display_heatmap' not in st.session_state:
        st.session_state.display_heatmap = False

def save_analysis_result(patient_data, image_path, prediction, confidence, timestamp=None):
    """
    Save analysis result to session state and database
    
    Args:
        patient_data: Dictionary of patient data
        image_path: Path to the saved image file
        prediction: Prediction label
        confidence: Confidence score
        timestamp: Timestamp of the analysis
    """
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    analysis_id = str(uuid.uuid4())
    
    result = {
        'id': analysis_id,
        'patient_id': patient_data.get('id', 'Unknown'),
        'patient_name': patient_data.get('name', 'Unknown'),
        'age': patient_data.get('age', 'Unknown'),
        'gender': patient_data.get('gender', 'Unknown'),
        'symptoms': patient_data.get('symptoms', 'Unknown'),
        'medical_history': patient_data.get('medical_history', 'Unknown'),
        'image_path': image_path,
        'prediction': prediction,
        'confidence': confidence,
        'timestamp': timestamp
    }
    
    # Add to session state
    st.session_state.analyses.append(result)
    
    # Save to database (if available)
    try:
        from utils.database import save_analysis_to_db
        
        db_id = save_analysis_to_db(
            patient_id=patient_data.get('id', 'Unknown'),
            image_path=image_path,
            prediction=prediction,
            confidence=confidence,
            age=patient_data.get('age', 'Unknown'),
            gender=patient_data.get('gender', 'Unknown'),
            symptoms=patient_data.get('symptoms', 'Unknown')
        )
        
        if db_id:
            # Add database ID to result
            result['db_id'] = db_id
    except Exception as e:
        # Continue even if database save fails
        st.warning(f"Note: Analysis saved locally but not to database. {str(e)}")
    
    return analysis_id

def get_analysis_by_id(analysis_id):
    """
    Get analysis result by ID
    
    Args:
        analysis_id: ID of the analysis
        
    Returns:
        Analysis result if found, None otherwise
    """
    if 'analyses' not in st.session_state:
        return None
    
    for analysis in st.session_state.analyses:
        if analysis['id'] == analysis_id:
            return analysis
    
    return None

def get_analyses_df():
    """
    Get a DataFrame of all analyses
    
    Returns:
        DataFrame of all analyses
    """
    if 'analyses' not in st.session_state or len(st.session_state.analyses) == 0:
        return pd.DataFrame()
    
    return pd.DataFrame(st.session_state.analyses)

def filter_analyses(df, filters):
    """
    Filter analyses based on provided filters
    
    Args:
        df: DataFrame of analyses
        filters: Dictionary of filter key-value pairs
        
    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    for key, value in filters.items():
        if value:
            if key == 'age_range':
                min_age, max_age = value
                filtered_df = filtered_df[(filtered_df['age'].astype(float) >= min_age) & 
                                          (filtered_df['age'].astype(float) <= max_age)]
            elif key == 'prediction':
                filtered_df = filtered_df[filtered_df['prediction'] == value]
            elif key == 'gender':
                filtered_df = filtered_df[filtered_df['gender'] == value]
            elif key == 'confidence_threshold':
                filtered_df = filtered_df[filtered_df['confidence'] >= value]
    
    return filtered_df

def clear_session_data():
    """
    Clear all session data
    """
    keys_to_clear = [
        'patient_data',
        'current_image',
        'current_image_array',
        'current_prediction',
        'display_heatmap'
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None

def get_similar_cases(prediction, age, gender, num_cases=5):
    """
    Get similar cases based on prediction, age, and gender
    
    Args:
        prediction: Prediction label
        age: Patient age
        gender: Patient gender
        num_cases: Number of cases to return
        
    Returns:
        DataFrame of similar cases
    """
    # Try to get similar cases from database first
    try:
        from utils.database import get_similar_cases_from_db
        db_cases = get_similar_cases_from_db(prediction, age, gender, limit=num_cases)
        
        if db_cases and len(db_cases) > 0:
            # Convert to DataFrame
            return pd.DataFrame(db_cases)
    except Exception as e:
        # Fallback to session state if database query fails
        st.warning(f"Note: Database query failed, using local data. {str(e)}")
    
    # Fallback to session state data
    if 'analyses' not in st.session_state or len(st.session_state.analyses) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(st.session_state.analyses)
    
    if df.empty:
        return df
    
    # Filter by prediction
    similar_cases = df[df['prediction'] == prediction]
    
    if similar_cases.empty:
        return similar_cases
    
    # Convert age to float for comparison
    try:
        age_float = float(age)
        similar_cases['age_float'] = similar_cases['age'].astype(float)
        
        # Calculate age difference
        similar_cases['age_diff'] = abs(similar_cases['age_float'] - age_float)
        
        # Sort by gender match and age difference
        similar_cases['gender_match'] = similar_cases['gender'] == gender
        similar_cases = similar_cases.sort_values(by=['gender_match', 'age_diff'], ascending=[False, True])
        
        # Drop helper columns
        similar_cases = similar_cases.drop(columns=['age_float', 'age_diff', 'gender_match'])
    except:
        # If age conversion fails, just sort by gender
        similar_cases = similar_cases[similar_cases['gender'] == gender]
    
    return similar_cases.head(num_cases)
