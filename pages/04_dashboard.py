import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_handling import initialize_session_state, get_analyses_df, filter_analyses, get_similar_cases
from utils.visualization import (
    create_patient_demographics_chart, 
    create_age_distribution_chart, 
    create_diagnosis_distribution_chart,
    create_confidence_histogram,
    create_age_vs_diagnosis_chart,
    create_gender_vs_diagnosis_chart
)

def app():
    st.title("Analytics Dashboard")
    
    # Initialize session state
    initialize_session_state()
    
    # Try to get analyses from database first, then fallback to session state
    try:
        from utils.database import get_analysis_results, filter_analyses as db_filter_analyses
        db_analyses = get_analysis_results(limit=100)
        if db_analyses and len(db_analyses) > 0:
            st.success("Successfully loaded analysis data from database.")
            analyses_df = pd.DataFrame(db_analyses)
            # We'll use database filtering later
            use_db_filtering = True
        else:
            # Fallback to session state
            analyses_df = get_analyses_df()
            use_db_filtering = False
    except Exception as e:
        # Fallback to session state
        st.warning(f"Note: Using local data. Database connection: {str(e)}")
        analyses_df = get_analyses_df()
        use_db_filtering = False
    
    if analyses_df.empty:
        st.warning("No analyses have been performed yet. Start by uploading an image.")
        if st.button("Go to Upload Page"):
            st.switch_page("pages/01_upload.py")
        return
    
    # More descriptive dashboard introduction
    st.markdown("""
    This dashboard provides analytics and visualizations of all medical image analyses performed on the platform.
    Use the filters to explore trends, distributions, and clinical insights across patient populations.
    """)
    
    # Dashboard help/guide
    with st.expander("Dashboard Guide"):
        st.markdown("""
        ### Using the Analytics Dashboard
        
        **Main Features:**
        - **Filters**: Narrow down analyses by patient demographics and diagnostic criteria
        - **Summary Metrics**: View key statistics about the filtered dataset
        - **Visualizations**: Explore patterns and trends through interactive charts
        - **Case Comparison**: Compare current case with similar historical cases
        
        **Tips:**
        - Adjust multiple filters to find specific patient cohorts
        - Hover over charts for detailed information
        - Use the filters to identify demographic trends in diagnoses
        - Export specific analyses for reporting or follow-up
        """)
    
    # Create a more attractive filter sidebar with sections
    st.sidebar.markdown("## 🔍 Analysis Filters")
    
    # Patient filters section
    st.sidebar.markdown("### Patient Filters")
    
    # Gender filter with icons
    gender_options = ["All"] + sorted(analyses_df['gender'].unique().tolist())
    selected_gender = st.sidebar.selectbox("Gender", gender_options)
    
    # Age range filter with improved appearance
    age_min = int(pd.to_numeric(analyses_df['age'], errors='coerce').min() or 0)
    age_max = int(pd.to_numeric(analyses_df['age'], errors='coerce').max() or 100)
    selected_age_range = st.sidebar.slider("Age Range (years)", age_min, age_max, (age_min, age_max))
    
    # Diagnosis filters section
    st.sidebar.markdown("### Diagnostic Filters")
    
    # Diagnosis filter with color indicators
    diagnosis_options = ["All"] + sorted(analyses_df['prediction'].unique().tolist())
    selected_diagnosis = st.sidebar.selectbox("Diagnosis", diagnosis_options)
    
    # Confidence threshold filter with better description
    confidence_threshold = st.sidebar.slider("Minimum AI Confidence Score", 0.0, 1.0, 0.0, 0.05)
    
    # Initialize filters dictionary early
    filters = {}
    
    # Add date filter if we have timestamps
    if 'timestamp' in analyses_df.columns:
        st.sidebar.markdown("### Temporal Filters")
        # Convert timestamps to datetime if they're strings
        if analyses_df['timestamp'].dtype == 'object':
            try:
                analyses_df['timestamp'] = pd.to_datetime(analyses_df['timestamp'])
                min_date = analyses_df['timestamp'].min().date()
                max_date = analyses_df['timestamp'].max().date()
                selected_date_range = st.sidebar.date_input(
                    "Date Range",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                if len(selected_date_range) == 2:
                    filters['date_range'] = selected_date_range
            except:
                pass
    
    # Apply filters
    # (The filters dictionary was initialized earlier)
    if selected_gender != "All":
        filters['gender'] = selected_gender
    
    filters['age_range'] = selected_age_range
    
    if selected_diagnosis != "All":
        filters['prediction'] = selected_diagnosis
    
    if confidence_threshold > 0:
        filters['confidence_threshold'] = confidence_threshold
    
    # Use appropriate filtering method based on data source
    if 'use_db_filtering' in locals() and use_db_filtering:
        try:
            # Use database filtering when possible
            filtered_df = pd.DataFrame(db_filter_analyses(filters))
        except Exception as e:
            st.warning(f"Database filtering failed, using local filtering. Error: {str(e)}")
            filtered_df = filter_analyses(analyses_df, filters)
    else:
        # Use local filtering
        filtered_df = filter_analyses(analyses_df, filters)
    
    # Display summary metrics
    st.markdown("## Summary Metrics")
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Total Analyses", len(analyses_df))
    
    with metric_col2:
        st.metric("Filtered Analyses", len(filtered_df))
    
    with metric_col3:
        if not filtered_df.empty:
            normal_count = filtered_df[filtered_df['prediction'] == 'Normal'].shape[0]
            normal_percentage = normal_count / len(filtered_df) * 100
            st.metric("Normal Cases", f"{normal_count} ({normal_percentage:.1f}%)")
        else:
            st.metric("Normal Cases", "0 (0.0%)")
    
    with metric_col4:
        if not filtered_df.empty:
            abnormal_count = filtered_df[filtered_df['prediction'] != 'Normal'].shape[0]
            abnormal_percentage = abnormal_count / len(filtered_df) * 100
            st.metric("Abnormal Cases", f"{abnormal_count} ({abnormal_percentage:.1f}%)")
        else:
            st.metric("Abnormal Cases", "0 (0.0%)")
    
    # Display filtered data
    with st.expander("View Data", expanded=False):
        if not filtered_df.empty:
            display_columns = ['patient_id', 'age', 'gender', 'prediction', 'confidence', 'timestamp']
            st.dataframe(filtered_df[display_columns], use_container_width=True)
        else:
            st.info("No data matches the selected filters.")
    
    # Visualizations
    st.markdown("## Visualizations")
    
    if not filtered_df.empty:
        # First row of charts
        col1, col2 = st.columns(2)
        
        with col1:
            diagnosis_chart = create_diagnosis_distribution_chart(filtered_df)
            if diagnosis_chart:
                st.plotly_chart(diagnosis_chart, use_container_width=True)
        
        with col2:
            gender_chart = create_patient_demographics_chart(filtered_df)
            if gender_chart:
                st.plotly_chart(gender_chart, use_container_width=True)
        
        # Second row of charts
        col1, col2 = st.columns(2)
        
        with col1:
            age_chart = create_age_distribution_chart(filtered_df)
            if age_chart:
                st.plotly_chart(age_chart, use_container_width=True)
        
        with col2:
            confidence_chart = create_confidence_histogram(filtered_df)
            if confidence_chart:
                st.plotly_chart(confidence_chart, use_container_width=True)
        
        # Third row of charts - correlations
        col1, col2 = st.columns(2)
        
        with col1:
            age_vs_diagnosis = create_age_vs_diagnosis_chart(filtered_df)
            if age_vs_diagnosis:
                st.plotly_chart(age_vs_diagnosis, use_container_width=True)
        
        with col2:
            gender_vs_diagnosis = create_gender_vs_diagnosis_chart(filtered_df)
            if gender_vs_diagnosis:
                st.plotly_chart(gender_vs_diagnosis, use_container_width=True)
    else:
        st.info("No data available for visualization with the current filters.")
    
    # Case comparison feature
    st.markdown("## Case Comparison")
    
    if 'current_prediction' in st.session_state and st.session_state.current_prediction:
        current_prediction = st.session_state.current_prediction['class_label']
        current_age = st.session_state.patient_data.get('age', '')
        current_gender = st.session_state.patient_data.get('gender', '')
        
        st.markdown(f"Current case: **{current_prediction}** diagnosis for {current_gender}, {current_age} years old")
        
        similar_cases = get_similar_cases(current_prediction, current_age, current_gender)
        
        if not similar_cases.empty and len(similar_cases) > 1:  # More than just the current case
            st.markdown("### Similar Cases")
            
            display_columns = ['patient_id', 'age', 'gender', 'symptoms', 'prediction', 'confidence']
            st.dataframe(similar_cases[display_columns], use_container_width=True)
            
            # Demographics comparison
            st.markdown("#### Age Comparison")
            
            try:
                current_age_float = float(current_age)
                similar_cases['age_float'] = pd.to_numeric(similar_cases['age'], errors='coerce')
                
                age_fig = px.histogram(
                    similar_cases,
                    x='age_float',
                    nbins=10,
                    title=f'Age Distribution of Similar {current_prediction} Cases',
                    labels={'age_float': 'Age'},
                    color_discrete_sequence=['lightblue']
                )
                
                # Add vertical line for current patient
                age_fig.add_vline(
                    x=current_age_float,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Current Patient",
                    annotation_position="top right"
                )
                
                st.plotly_chart(age_fig, use_container_width=True)
            except:
                st.info("Age comparison not available")
        else:
            st.info("Not enough similar cases found for comparison.")
    else:
        st.info("Analyze a case first to see comparisons with similar cases.")
    
    # Navigation button
    if st.button("New Analysis"):
        st.switch_page("pages/01_upload.py")

if __name__ == "__main__":
    app()
