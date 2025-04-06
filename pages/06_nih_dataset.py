import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import io
import requests
from utils.database import (
    get_nih_dataset_stats,
    get_nih_sample_records,
    import_nih_metadata,
    import_bbox_data,
    get_condition_insights
)
from utils.data_handling import initialize_session_state

def app():
    st.title("NIH Chest X-ray Dataset Integration")
    
    # Initialize session state
    initialize_session_state()
    
    # Introduction section
    st.markdown("""
    ## NIH Chest X-ray Dataset
    
    This page allows you to explore and integrate the NIH Chest X-ray Dataset, which contains 
    over 112,000 chest X-ray images from more than 30,000 unique patients with 15 different 
    disease classes.
    
    The dataset is available from:
    - [Kaggle NIH Chest X-rays Dataset](https://www.kaggle.com/datasets/nih-chest-xrays/data)
    - [NIH Clinical Center](https://nihcc.app.box.com/v/ChestXray-NIHCC)
    """)
    
    # Create tabs for different functionality
    tabs = st.tabs(["Dataset Overview", "Data Import", "Condition Analytics", "Sample Exploration"])
    
    # Tab 1: Dataset Overview
    with tabs[0]:
        st.markdown("### NIH Chest X-ray Dataset Overview")
        
        # Get dataset statistics from database
        stats = get_nih_dataset_stats()
        
        # Display summary metrics
        st.markdown("#### Dataset Summary")
        
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Total Records", f"{stats['total_records']:,}")
        
        with metric_cols[1]:
            male_count = stats['gender_distribution'].get('M', 0)
            st.metric("Male Patients", f"{male_count:,}")
        
        with metric_cols[2]:
            female_count = stats['gender_distribution'].get('F', 0)
            st.metric("Female Patients", f"{female_count:,}")
        
        with metric_cols[3]:
            class_count = len(stats['finding_distribution'])
            st.metric("Disease Classes", class_count)
        
        # Create visualizations of dataset statistics
        st.markdown("#### Dataset Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Age distribution chart
            if stats['age_distribution']:
                age_data = pd.DataFrame({
                    'Age Group': list(stats['age_distribution'].keys()),
                    'Count': list(stats['age_distribution'].values())
                })
                
                fig = px.bar(
                    age_data,
                    x='Age Group',
                    y='Count',
                    title='Age Distribution in NIH Dataset',
                    color='Count',
                    color_continuous_scale='Viridis'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gender distribution pie chart
            if stats['gender_distribution']:
                gender_data = pd.DataFrame({
                    'Gender': list(stats['gender_distribution'].keys()),
                    'Count': list(stats['gender_distribution'].values())
                })
                
                # Replace empty gender with 'Unknown'
                gender_data['Gender'] = gender_data['Gender'].replace('', 'Unknown')
                
                fig = px.pie(
                    gender_data,
                    values='Count',
                    names='Gender',
                    title='Gender Distribution',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Disease distribution chart
        if stats['finding_distribution']:
            finding_data = pd.DataFrame({
                'Finding': list(stats['finding_distribution'].keys()),
                'Count': list(stats['finding_distribution'].values())
            })
            
            # Sort by count descending
            finding_data = finding_data.sort_values('Count', ascending=False)
            
            fig = px.bar(
                finding_data,
                x='Finding',
                y='Count',
                title='Disease Distribution in NIH Dataset',
                color='Count',
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                xaxis_title='Disease',
                yaxis_title='Count',
                xaxis={'categoryorder':'total descending'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # View position distribution
        if stats['view_distribution']:
            view_data = pd.DataFrame({
                'View Position': list(stats['view_distribution'].keys()),
                'Count': list(stats['view_distribution'].values())
            })
            
            fig = px.pie(
                view_data,
                values='Count',
                names='View Position',
                title='X-ray View Positions',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Tab 2: Data Import
    with tabs[1]:
        st.markdown("### Import NIH Chest X-ray Dataset")
        
        st.markdown("""
        This section allows you to import metadata from the NIH Chest X-ray Dataset.
        
        You can either:
        1. Upload the CSV files directly
        2. Import a sample dataset for demonstration
        
        The complete dataset is available on [Kaggle](https://www.kaggle.com/datasets/nih-chest-xrays/data).
        """)
        
        # Tabs for different import methods
        import_tabs = st.tabs(["Upload CSV Files", "Load Sample Data"])
        
        # Tab 1: Upload CSV Files
        with import_tabs[0]:
            st.markdown("#### Upload Dataset CSV Files")
            
            # File upload for metadata
            st.markdown("##### 1. Upload Patient Metadata (Data_Entry_2017.csv)")
            metadata_file = st.file_uploader(
                "Choose the Data_Entry_2017.csv file",
                type="csv",
                help="This file contains patient information and findings for all images"
            )
            
            # File upload for bounding boxes
            st.markdown("##### 2. Upload Bounding Box Data (BBox_List_2017.csv)")
            bbox_file = st.file_uploader(
                "Choose the BBox_List_2017.csv file",
                type="csv",
                help="This file contains bounding box coordinates for some images"
            )
            
            if metadata_file:
                # Show a preview of the metadata
                st.markdown("##### Metadata Preview")
                
                preview_df = pd.read_csv(metadata_file, nrows=5)
                st.dataframe(preview_df, use_container_width=True)
                
                # Reset the file pointer
                metadata_file.seek(0)
            
            if bbox_file:
                # Show a preview of the bbox data
                st.markdown("##### Bounding Box Preview")
                
                preview_df = pd.read_csv(bbox_file, nrows=5)
                st.dataframe(preview_df, use_container_width=True)
                
                # Reset the file pointer
                bbox_file.seek(0)
            
            # Import button
            import_col1, import_col2 = st.columns([1, 3])
            
            with import_col1:
                import_button = st.button("Import Data", type="primary", disabled=not metadata_file)
            
            with import_col2:
                if import_button and metadata_file:
                    with st.spinner("Importing metadata..."):
                        # Import metadata
                        count = import_nih_metadata(metadata_file)
                        st.success(f"Successfully imported {count} records from metadata file.")
                    
                    if bbox_file:
                        with st.spinner("Importing bounding box data..."):
                            # Import bounding box data
                            bbox_count = import_bbox_data(bbox_file)
                            st.success(f"Successfully imported {bbox_count} bounding box records.")
        
        # Tab 2: Load Sample Data
        with import_tabs[1]:
            st.markdown("#### Load Sample Dataset")
            
            st.markdown("""
            You can load a sample of the NIH Chest X-ray dataset from Kaggle for demonstration purposes.
            
            This will download a subset of the metadata and import it into the database.
            """)
            
            # Import Kaggle integration
            from utils.kaggle_integration import check_kaggle_credentials, save_kaggle_credentials, import_nih_data_from_kaggle
            
            # Check if we already have Kaggle credentials
            if not check_kaggle_credentials():
                # Show form to input Kaggle credentials
                st.markdown("#### Kaggle API Credentials")
                st.markdown("""
                To download data from Kaggle, you need to provide your Kaggle API credentials.
                
                1. Go to your [Kaggle account settings](https://www.kaggle.com/account)
                2. Scroll down to the API section
                3. Click "Create New API Token" to download a kaggle.json file
                4. Enter the username and key from that file below
                """)
                
                with st.form("kaggle_credentials_form"):
                    kaggle_username = st.text_input("Kaggle Username")
                    kaggle_key = st.text_input("Kaggle API Key", type="password")
                    
                    submit = st.form_submit_button("Save Credentials")
                    
                    if submit and kaggle_username and kaggle_key:
                        save_kaggle_credentials(kaggle_username, kaggle_key)
                        st.success("Credentials saved successfully.")
                        st.rerun()
            
            # Sample size selection
            sample_size = st.slider("Sample Size", 100, 5000, 1000, 100,
                                  help="Number of records to download from the dataset")
            
            # Sample data download and import
            sample_col1, sample_col2 = st.columns([1, 3])
            
            with sample_col1:
                load_sample = st.button("Load From Kaggle", type="primary",
                                      disabled=not check_kaggle_credentials())
            
            with sample_col2:
                if load_sample:
                    with st.spinner("Downloading and importing data from Kaggle..."):
                        results = import_nih_data_from_kaggle(sample_size)
                        
                        # Report metadata results
                        if results["metadata"]["success"]:
                            st.success(results["metadata"]["message"])
                        else:
                            st.error(f"Metadata import: {results['metadata']['message']}")
                        
                        # Report bbox results
                        if results["bbox"]["success"]:
                            st.success(results["bbox"]["message"])
                        else:
                            st.warning(f"Bounding box import: {results['bbox']['message']}")
                        
                # If no Kaggle credentials, show alternative method
                if not check_kaggle_credentials():
                    st.info("Without Kaggle credentials, you can use the 'Upload CSV Files' tab to import the dataset manually.")
    
    # Tab 3: Condition Analytics
    with tabs[2]:
        st.markdown("### Condition Analytics in NIH Dataset")
        
        # Select condition to analyze
        condition_options = [
            "Atelectasis", "Consolidation", "Infiltration", "Pneumothorax", 
            "Edema", "Emphysema", "Fibrosis", "Effusion", "Pneumonia", 
            "Pleural_thickening", "Cardiomegaly", "Nodule", "Mass", "Hernia", "No Finding"
        ]
        
        selected_condition = st.selectbox(
            "Select a condition to analyze", 
            options=condition_options
        )
        
        # Get insights for the selected condition
        if selected_condition:
            with st.spinner(f"Analyzing {selected_condition}..."):
                insights = get_condition_insights(selected_condition)
                
                # Display insights
                st.markdown(f"#### Analysis of {selected_condition}")
                
                # Summary metrics
                metric_cols = st.columns(4)
                
                with metric_cols[0]:
                    st.metric("Total Cases", f"{insights['total_cases']:,}")
                
                with metric_cols[1]:
                    male_count = insights['gender_distribution'].get('M', 0)
                    female_count = insights['gender_distribution'].get('F', 0)
                    total_gender = max(1, male_count + female_count)  # Avoid division by zero
                    male_percent = (male_count / total_gender) * 100
                    
                    st.metric("Male Percentage", f"{male_percent:.1f}%")
                
                with metric_cols[2]:
                    female_percent = (female_count / total_gender) * 100
                    st.metric("Female Percentage", f"{female_percent:.1f}%")
                
                with metric_cols[3]:
                    pa_view = insights['view_distribution'].get('PA', 0)
                    ap_view = insights['view_distribution'].get('AP', 0)
                    total_views = max(1, sum(insights['view_distribution'].values()))
                    pa_percent = (pa_view / total_views) * 100
                    
                    st.metric("PA View Percentage", f"{pa_percent:.1f}%")
                
                # Visualizations
                st.markdown("#### Visualizations")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Age distribution chart
                    if insights['age_distribution']:
                        age_data = pd.DataFrame({
                            'Age Group': list(insights['age_distribution'].keys()),
                            'Count': list(insights['age_distribution'].values())
                        })
                        
                        fig = px.bar(
                            age_data,
                            x='Age Group',
                            y='Count',
                            title=f'Age Distribution for {selected_condition}',
                            color='Count',
                            color_continuous_scale='Viridis'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Gender distribution pie chart
                    if insights['gender_distribution']:
                        gender_data = pd.DataFrame({
                            'Gender': list(insights['gender_distribution'].keys()),
                            'Count': list(insights['gender_distribution'].values())
                        })
                        
                        # Replace empty gender with 'Unknown'
                        gender_data['Gender'] = gender_data['Gender'].replace('', 'Unknown')
                        
                        fig = px.pie(
                            gender_data,
                            values='Count',
                            names='Gender',
                            title=f'Gender Distribution for {selected_condition}',
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Co-occurring conditions
                if insights['cooccurring_conditions']:
                    st.markdown("#### Co-occurring Conditions")
                    
                    cooccurring_data = pd.DataFrame({
                        'Condition': list(insights['cooccurring_conditions'].keys()),
                        'Count': list(insights['cooccurring_conditions'].values())
                    })
                    
                    # Sort by count descending
                    cooccurring_data = cooccurring_data.sort_values('Count', ascending=False)
                    
                    fig = px.bar(
                        cooccurring_data,
                        x='Condition',
                        y='Count',
                        title=f'Conditions Co-occurring with {selected_condition}',
                        color='Count',
                        color_continuous_scale='Viridis'
                    )
                    
                    fig.update_layout(
                        xaxis_title='Condition',
                        yaxis_title='Count',
                        xaxis={'categoryorder':'total descending'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # View position distribution
                if insights['view_distribution']:
                    st.markdown("#### X-ray View Positions")
                    
                    view_data = pd.DataFrame({
                        'View Position': list(insights['view_distribution'].keys()),
                        'Count': list(insights['view_distribution'].values())
                    })
                    
                    fig = px.pie(
                        view_data,
                        values='Count',
                        names='View Position',
                        title=f'X-ray View Positions for {selected_condition}',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    # Tab 4: Sample Exploration
    with tabs[3]:
        st.markdown("### Explore Sample Records")
        
        # Get sample records
        sample_size = st.slider("Number of records to display", 5, 50, 10)
        
        with st.spinner("Loading sample records..."):
            sample_records = get_nih_sample_records(sample_size)
            
            if sample_records:
                # Convert to DataFrame for display
                sample_df = pd.DataFrame(sample_records)
                
                # Display sample records
                st.dataframe(sample_df, use_container_width=True)
                
                # Allow filtering by condition
                st.markdown("#### Filter by Condition")
                
                # Extract all conditions from sample
                all_conditions = []
                for record in sample_records:
                    if record['finding_labels']:
                        conditions = record['finding_labels'].split('|')
                        all_conditions.extend(conditions)
                
                unique_conditions = sorted(set(all_conditions))
                
                # Select condition to filter by
                filter_condition = st.selectbox(
                    "Select condition", 
                    options=["All"] + unique_conditions
                )
                
                if filter_condition != "All":
                    # Filter records by selected condition
                    filtered_records = [
                        record for record in sample_records
                        if record['finding_labels'] and filter_condition in record['finding_labels'].split('|')
                    ]
                    
                    if filtered_records:
                        st.markdown(f"##### Records with {filter_condition}")
                        filtered_df = pd.DataFrame(filtered_records)
                        st.dataframe(filtered_df, use_container_width=True)
                    else:
                        st.info(f"No records with {filter_condition} found in the sample.")
            else:
                st.info("No records found. Please import the dataset first.")

if __name__ == "__main__":
    app()