import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import streamlit as st
import csv
import io

# Database connection parameters from environment variables
DB_PARAMS = {
    "dbname": os.environ.get("PGDATABASE"),
    "user": os.environ.get("PGUSER"),
    "password": os.environ.get("PGPASSWORD"),
    "host": os.environ.get("PGHOST"),
    "port": os.environ.get("PGPORT")
}

def get_db_connection():
    """
    Get a PostgreSQL database connection
    
    Returns:
        connection: PostgreSQL connection object
    """
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def execute_query(query, params=None, fetch=True):
    """
    Execute a SQL query and optionally fetch results
    
    Args:
        query: SQL query string
        params: Parameters for the query
        fetch: Whether to fetch results
        
    Returns:
        results: Query results if fetch is True, else None
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params or ())
                if fetch:
                    return cur.fetchall()
    except Exception as e:
        st.error(f"Query execution error: {str(e)}")
        return None
    finally:
        conn.close()

def import_nih_metadata(csv_file):
    """
    Import NIH Chest X-ray metadata from CSV file
    
    Args:
        csv_file: CSV file object
        
    Returns:
        count: Number of records imported
    """
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        df = pd.read_csv(csv_file)
        count = 0
        
        with conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    # Clean up data
                    patient_age = row.get('Patient Age', 0)
                    try:
                        patient_age = int(patient_age)
                    except:
                        patient_age = 0
                    
                    # Insert into database
                    cur.execute("""
                        INSERT INTO nih_xray_metadata 
                        (image_index, finding_labels, follow_up_num, patient_id, 
                        patient_age, patient_gender, view_position, 
                        original_image_width, original_image_height, 
                        original_image_pixel_spacing_x, original_image_pixel_spacing_y)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (image_index) DO NOTHING
                    """, (
                        row.get('Image Index', ''),
                        row.get('Finding Labels', ''),
                        row.get('Follow-up #', 0),
                        row.get('Patient ID', ''),
                        patient_age,
                        row.get('Patient Gender', ''),
                        row.get('View Position', ''),
                        row.get('OriginalImage Width', 0),
                        row.get('OriginalImage Height', 0),
                        row.get('OriginalImage PixelSpacing x', 0.0),
                        row.get('OriginalImage PixelSpacing y', 0.0)
                    ))
                    count += 1
        
        return count
    except Exception as e:
        st.error(f"Import error: {str(e)}")
        return 0
    finally:
        conn.close()

def import_bbox_data(csv_file):
    """
    Import bounding box data from CSV file
    
    Args:
        csv_file: CSV file object
        
    Returns:
        count: Number of records imported
    """
    conn = get_db_connection()
    if not conn:
        return 0
    
    try:
        df = pd.read_csv(csv_file)
        count = 0
        
        with conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute("""
                        INSERT INTO nih_xray_bbox 
                        (image_index, finding_label, bbox_x, bbox_y, bbox_w, bbox_h)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        row.get('Image Index', ''),
                        row.get('Finding Label', ''),
                        row.get('Bbox [x', 0),
                        row.get('y', 0),
                        row.get('w', 0),
                        row.get('h]', 0)
                    ))
                    count += 1
        
        return count
    except Exception as e:
        st.error(f"Import error: {str(e)}")
        return 0
    finally:
        conn.close()

def get_nih_dataset_stats():
    """
    Get statistics about the NIH dataset
    
    Returns:
        stats: Dictionary of dataset statistics
    """
    # Total records
    total_query = "SELECT COUNT(*) as total FROM nih_xray_metadata"
    total_result = execute_query(total_query)
    total = total_result[0]['total'] if total_result else 0
    
    # Gender distribution
    gender_query = """
        SELECT patient_gender, COUNT(*) as count 
        FROM nih_xray_metadata 
        GROUP BY patient_gender
    """
    gender_results = execute_query(gender_query)
    gender_distribution = {row['patient_gender']: row['count'] for row in gender_results} if gender_results else {}
    
    # Age distribution
    age_query = """
        SELECT 
            CASE 
                WHEN patient_age < 20 THEN '0-19'
                WHEN patient_age BETWEEN 20 AND 39 THEN '20-39'
                WHEN patient_age BETWEEN 40 AND 59 THEN '40-59'
                WHEN patient_age BETWEEN 60 AND 79 THEN '60-79'
                ELSE '80+'
            END as age_group,
            COUNT(*) as count
        FROM nih_xray_metadata
        GROUP BY age_group
        ORDER BY age_group
    """
    age_results = execute_query(age_query)
    age_distribution = {row['age_group']: row['count'] for row in age_results} if age_results else {}
    
    # Finding distribution
    finding_query = """
        WITH findings AS (
            SELECT unnest(string_to_array(finding_labels, '|')) as finding
            FROM nih_xray_metadata
        )
        SELECT finding, COUNT(*) as count
        FROM findings
        GROUP BY finding
        ORDER BY count DESC
    """
    finding_results = execute_query(finding_query)
    finding_distribution = {row['finding']: row['count'] for row in finding_results} if finding_results else {}
    
    # View position distribution
    view_query = """
        SELECT view_position, COUNT(*) as count
        FROM nih_xray_metadata
        GROUP BY view_position
        ORDER BY count DESC
    """
    view_results = execute_query(view_query)
    view_distribution = {row['view_position']: row['count'] for row in view_results} if view_results else {}
    
    return {
        "total_records": total,
        "gender_distribution": gender_distribution,
        "age_distribution": age_distribution,
        "finding_distribution": finding_distribution,
        "view_distribution": view_distribution
    }

def get_nih_sample_records(limit=10):
    """
    Get a sample of NIH dataset records
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        records: List of record dictionaries
    """
    query = f"""
        SELECT *
        FROM nih_xray_metadata
        ORDER BY RANDOM()
        LIMIT {limit}
    """
    return execute_query(query)

def save_analysis_to_db(patient_id, image_path, prediction, confidence, age, gender, symptoms):
    """
    Save analysis result to database
    
    Args:
        patient_id: Patient ID
        image_path: Path to the image
        prediction: Prediction label
        confidence: Confidence score
        age: Patient age
        gender: Patient gender
        symptoms: Patient symptoms
        
    Returns:
        success: Boolean indicating success
    """
    query = """
        INSERT INTO analysis_results
        (patient_id, image_path, prediction, confidence, age, gender, symptoms)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    params = (patient_id, image_path, prediction, confidence, age, gender, symptoms)
    
    try:
        result = execute_query(query, params)
        return result[0]['id'] if result else None
    except Exception as e:
        st.error(f"Error saving analysis: {str(e)}")
        return None

def get_analysis_results(limit=100):
    """
    Get analysis results from database
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        results: List of result dictionaries
    """
    query = f"""
        SELECT *
        FROM analysis_results
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    return execute_query(query)

def get_analysis_by_id(analysis_id):
    """
    Get analysis result by ID
    
    Args:
        analysis_id: ID of the analysis
        
    Returns:
        result: Analysis result dictionary
    """
    query = "SELECT * FROM analysis_results WHERE id = %s"
    results = execute_query(query, (analysis_id,))
    return results[0] if results else None

def filter_analyses(filters):
    """
    Filter analyses based on provided filters
    
    Args:
        filters: Dictionary of filter parameters
        
    Returns:
        results: Filtered analysis results
    """
    query = "SELECT * FROM analysis_results WHERE 1=1"
    params = []
    
    if 'patient_id' in filters and filters['patient_id']:
        query += " AND patient_id = %s"
        params.append(filters['patient_id'])
    
    if 'prediction' in filters and filters['prediction'] != 'All':
        query += " AND prediction = %s"
        params.append(filters['prediction'])
    
    if 'gender' in filters and filters['gender'] != 'All':
        query += " AND gender = %s"
        params.append(filters['gender'])
    
    if 'age_range' in filters:
        min_age, max_age = filters['age_range']
        query += " AND age BETWEEN %s AND %s"
        params.extend([min_age, max_age])
    
    if 'confidence_threshold' in filters:
        query += " AND confidence >= %s"
        params.append(filters['confidence_threshold'])
    
    if 'date_range' in filters:
        start_date, end_date = filters['date_range']
        query += " AND DATE(timestamp) BETWEEN %s AND %s"
        params.extend([start_date, end_date])
    
    query += " ORDER BY timestamp DESC"
    
    return execute_query(query, tuple(params))

def export_to_csv(data):
    """
    Export data to CSV
    
    Args:
        data: List of dictionaries to export
        
    Returns:
        csv_string: CSV data as a string
    """
    if not data:
        return ""
    
    output = io.StringIO()
    
    # Extract column names from first record
    fieldnames = data[0].keys()
    
    # Create CSV writer
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write data
    for row in data:
        writer.writerow(row)
    
    return output.getvalue()

def get_similar_cases_from_db(prediction, age, gender, limit=5):
    """
    Get similar cases from database
    
    Args:
        prediction: Prediction label
        age: Patient age
        gender: Patient gender
        limit: Maximum number of cases to return
        
    Returns:
        cases: List of similar cases
    """
    # Convert age to integer if it's not already
    try:
        age_val = int(age)
    except (ValueError, TypeError):
        age_val = 0
    
    # Define age range (±10 years)
    min_age = max(0, age_val - 10)
    max_age = age_val + 10
    
    query = """
        SELECT *
        FROM analysis_results
        WHERE prediction = %s
        AND age BETWEEN %s AND %s
    """
    params = [prediction, min_age, max_age]
    
    if gender and gender != 'All':
        query += " AND gender = %s"
        params.append(gender)
    
    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)
    
    return execute_query(query, tuple(params))

def get_condition_insights(condition):
    """
    Get insights about a specific condition from the NIH dataset
    
    Args:
        condition: Condition to get insights for
        
    Returns:
        insights: Dictionary of insights
    """
    # Normalize condition name
    normalized_condition = condition.strip().capitalize()
    
    # Age distribution for condition
    age_query = """
        WITH condition_patients AS (
            SELECT patient_id, patient_age, patient_gender
            FROM nih_xray_metadata
            WHERE finding_labels LIKE %s
        )
        SELECT 
            CASE 
                WHEN patient_age < 20 THEN '0-19'
                WHEN patient_age BETWEEN 20 AND 39 THEN '20-39'
                WHEN patient_age BETWEEN 40 AND 59 THEN '40-59'
                WHEN patient_age BETWEEN 60 AND 79 THEN '60-79'
                ELSE '80+'
            END as age_group,
            COUNT(*) as count
        FROM condition_patients
        GROUP BY age_group
        ORDER BY age_group
    """
    age_results = execute_query(age_query, (f'%{normalized_condition}%',))
    age_distribution = {row['age_group']: row['count'] for row in age_results} if age_results else {}
    
    # Gender distribution for condition
    gender_query = """
        SELECT patient_gender, COUNT(*) as count 
        FROM nih_xray_metadata 
        WHERE finding_labels LIKE %s
        GROUP BY patient_gender
    """
    gender_results = execute_query(gender_query, (f'%{normalized_condition}%',))
    gender_distribution = {row['patient_gender']: row['count'] for row in gender_results} if gender_results else {}
    
    # Co-occurring conditions
    cooccurring_query = """
        WITH condition_findings AS (
            SELECT 
                image_index,
                unnest(string_to_array(finding_labels, '|')) as finding
            FROM nih_xray_metadata
            WHERE finding_labels LIKE %s
        ),
        other_findings AS (
            SELECT finding
            FROM condition_findings
            WHERE finding != %s
        )
        SELECT finding, COUNT(*) as count
        FROM other_findings
        GROUP BY finding
        ORDER BY count DESC
        LIMIT 5
    """
    cooccurring_results = execute_query(cooccurring_query, (f'%{normalized_condition}%', normalized_condition))
    cooccurring_conditions = {row['finding']: row['count'] for row in cooccurring_results} if cooccurring_results else {}
    
    # Total cases with condition
    total_query = "SELECT COUNT(*) as total FROM nih_xray_metadata WHERE finding_labels LIKE %s"
    total_result = execute_query(total_query, (f'%{normalized_condition}%',))
    total = total_result[0]['total'] if total_result else 0
    
    # View position distribution for condition
    view_query = """
        SELECT view_position, COUNT(*) as count
        FROM nih_xray_metadata
        WHERE finding_labels LIKE %s
        GROUP BY view_position
        ORDER BY count DESC
    """
    view_results = execute_query(view_query, (f'%{normalized_condition}%',))
    view_distribution = {row['view_position']: row['count'] for row in view_results} if view_results else {}
    
    return {
        "total_cases": total,
        "age_distribution": age_distribution,
        "gender_distribution": gender_distribution,
        "cooccurring_conditions": cooccurring_conditions,
        "view_distribution": view_distribution
    }