import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.data_handling import initialize_session_state
from utils.external_data import (
    fetch_dataset_metadata, 
    fetch_sample_statistics,
    connect_to_dataset_api,
    has_external_data_access,
    search_similar_cases,
    get_dataset_insights
)

def app():
    st.title("Real-World Healthcare Data Integration")
    
    # Initialize session state
    initialize_session_state()
    
    # Introduction
    st.markdown("""
    ## Connect to External Healthcare Datasets
    
    Enhance your diagnostic capabilities by connecting to real-world healthcare datasets.
    These datasets provide valuable context, comparison, and insights for your analyses.
    """)
    
    # Create section for available datasets
    st.markdown("### Available Datasets")
    
    # Fetch metadata about available datasets
    datasets = fetch_dataset_metadata()
    
    # Display datasets as cards
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown(f"#### {datasets['nih_chest_xray']['name']}")
            st.markdown(f"**Source:** {datasets['nih_chest_xray']['source']}")
            st.markdown(f"**Size:** {datasets['nih_chest_xray']['size']}")
            st.markdown(f"**Description:** {datasets['nih_chest_xray']['description']}")
            st.markdown(f"**Conditions:** {', '.join(datasets['nih_chest_xray']['conditions'][:5])}...")
            
            if st.button("Connect to NIH Dataset", key="connect_nih"):
                st.session_state.selected_dataset = "nih_chest_xray"
    
    with col2:
        with st.container(border=True):
            st.markdown(f"#### {datasets['covid_radiography']['name']}")
            st.markdown(f"**Source:** {datasets['covid_radiography']['source']}")
            st.markdown(f"**Size:** {datasets['covid_radiography']['size']}")
            st.markdown(f"**Description:** {datasets['covid_radiography']['description']}")
            st.markdown(f"**Conditions:** {', '.join(datasets['covid_radiography']['conditions'])}")
            
            if st.button("Connect to COVID Dataset", key="connect_covid"):
                st.session_state.selected_dataset = "covid_radiography"
    
    # Third dataset in a separate row
    with st.container(border=True):
        st.markdown(f"#### {datasets['nhs_chest_imaging']['name']}")
        st.markdown(f"**Source:** {datasets['nhs_chest_imaging']['source']}")
        st.markdown(f"**Size:** {datasets['nhs_chest_imaging']['size']}")
        st.markdown(f"**Description:** {datasets['nhs_chest_imaging']['description']}")
        st.markdown(f"**Conditions:** {', '.join(datasets['nhs_chest_imaging']['conditions'])}")
        
        if st.button("Connect to NHS Dataset", key="connect_nhs"):
            st.session_state.selected_dataset = "nhs_chest_imaging"
    
    # Check if a dataset has been selected
    if 'selected_dataset' in st.session_state:
        selected_id = st.session_state.selected_dataset
        selected_dataset = datasets[selected_id]
        
        st.markdown(f"## Connecting to {selected_dataset['name']}")
        
        # Show connection form
        with st.form("dataset_connection_form"):
            st.markdown(f"""
            To connect to the {selected_dataset['name']}, you'll need an API key.
            For real integration, you would need to request access from the data provider.
            """)
            
            api_key = st.text_input("API Key", type="password", 
                                   placeholder="Enter your API key", 
                                   help="For demo purposes, you can enter any value")
            
            submitted = st.form_submit_button("Connect")
            
            if submitted and api_key:
                # Connect to the API
                connection_result = connect_to_dataset_api(api_key, selected_id)
                
                if connection_result["status"] == "connected":
                    st.success(connection_result["message"])
                    st.session_state.external_data_connected = True
                    st.rerun()
                else:
                    st.error(connection_result["message"])
    
    # If connected to external data, show data exploration options
    if has_external_data_access():
        st.markdown("## Data Exploration")
        
        # Determine which dataset we're connected to
        dataset_id = st.session_state.get('selected_dataset', 'nih_chest_xray')
        dataset_info = datasets[dataset_id]
        
        st.markdown(f"""
        You are now connected to the **{dataset_info['name']}**.
        Explore patterns, trends, and insights from this dataset to enhance your understanding.
        """)
        
        # Tab-based data exploration
        tab1, tab2, tab3 = st.tabs(["Dataset Statistics", "Similar Cases", "Condition Insights"])
        
        with tab1:
            st.markdown("### Dataset Statistics")
            
            # Fetch sample statistics for the selected dataset
            stats = fetch_sample_statistics(dataset_id)
            
            if stats:
                col1, col2 = st.columns(2)
                
                with col1:
                    if "age_distribution" in stats:
                        st.markdown("#### Age Distribution")
                        age_data = stats["age_distribution"]
                        
                        # Create bar chart
                        fig = px.bar(
                            age_data, 
                            x="age_group", 
                            y="count", 
                            title=f"Age Distribution in {dataset_info['name']}",
                            labels={"age_group": "Age Group", "count": "Count"},
                            color_discrete_sequence=['#3366CC']
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if "condition_prevalence" in stats:
                        st.markdown("#### Condition Prevalence")
                        condition_data = stats["condition_prevalence"]
                        
                        # Create pie chart
                        fig = px.pie(
                            condition_data,
                            values="percentage",
                            names="condition",
                            title=f"Condition Prevalence in {dataset_info['name']}",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif "class_distribution" in stats:
                        st.markdown("#### Class Distribution")
                        class_data = stats["class_distribution"]
                        
                        # Create pie chart
                        fig = px.pie(
                            class_data,
                            values="count",
                            names="class",
                            title=f"Class Distribution in {dataset_info['name']}",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No statistics available for this dataset.")
        
        with tab2:
            st.markdown("### Search for Similar Cases")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                condition = st.selectbox(
                    "Condition", 
                    options=["Normal", "Pneumonia", "COVID-19"]
                )
            
            with col2:
                min_age, max_age = st.slider(
                    "Age Range",
                    min_value=0,
                    max_value=100,
                    value=(30, 70)
                )
            
            with col3:
                gender = st.selectbox(
                    "Gender",
                    options=["Any", "Male", "Female"]
                )
            
            # Set up age range and gender for query
            age_range = (min_age, max_age)
            gender_query = None if gender == "Any" else gender
            
            # Search button
            if st.button("Search External Cases"):
                with st.spinner("Searching for similar cases..."):
                    similar_cases = search_similar_cases(
                        condition, 
                        age_range=age_range, 
                        gender=gender_query
                    )
                    
                    if not similar_cases.empty:
                        st.markdown(f"#### Found {len(similar_cases)} similar cases")
                        st.dataframe(similar_cases, use_container_width=True)
                        
                        # Provide option to view details
                        st.markdown("Click on a row to view detailed case information")
                    else:
                        st.info("No similar cases found matching your criteria.")
            
            # Show tips for search
            with st.expander("Search Tips"):
                st.markdown("""
                - Broader age ranges will return more results
                - Use 'Any' for gender to see all matching cases
                - Results shown are from external datasets and are anonymized
                - In a real implementation, you would see actual cases from these datasets
                """)
        
        with tab3:
            st.markdown("### Condition Insights")
            
            # Get condition insights
            selected_condition = st.selectbox(
                "Select Condition",
                options=["Normal", "Pneumonia", "COVID-19"]
            )
            
            insights = get_dataset_insights(dataset_id, selected_condition)
            
            if insights and "data" in insights and insights["data"]:
                condition_data = insights["data"]
                
                # Create columns for insights
                insight_col1, insight_col2 = st.columns([1, 1])
                
                with insight_col1:
                    st.markdown("#### Age Distribution")
                    
                    age_dist = condition_data["age_distribution"]
                    st.metric("Mean Age", f"{age_dist['mean']:.1f}")
                    
                    # Create age gauge
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number+delta",
                        value=age_dist["mean"],
                        domain={"x": [0, 1], "y": [0, 1]},
                        title={"text": f"{selected_condition} Mean Age"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "royalblue"},
                            "steps": [
                                {"range": [0, 20], "color": "lightgray"},
                                {"range": [20, 40], "color": "lightblue"},
                                {"range": [40, 60], "color": "lightcyan"},
                                {"range": [60, 80], "color": "lightsalmon"},
                                {"range": [80, 100], "color": "lightcoral"}
                            ],
                            "threshold": {
                                "line": {"color": "red", "width": 4},
                                "thickness": 0.75,
                                "value": age_dist["median"]
                            }
                        }
                    ))
                    
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                
                with insight_col2:
                    st.markdown("#### Gender Distribution")
                    
                    gender_dist = condition_data["gender_distribution"]
                    
                    # Create gender pie chart
                    fig = px.pie(
                        values=list(gender_dist.values()),
                        names=list(gender_dist.keys()),
                        title=f"Gender Distribution for {selected_condition}",
                        color_discrete_sequence=["#3366CC", "#FF6699"]
                    )
                    
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Common comorbidities
                st.markdown("#### Common Comorbidities")
                
                comorbidities = condition_data["common_comorbidities"]
                
                # Create horizontal bar chart
                comorbidity_data = pd.DataFrame({
                    "Comorbidity": comorbidities,
                    "Count": [85, 60, 45, 30] if len(comorbidities) >= 4 else [85, 60, 45]
                })
                
                fig = px.bar(
                    comorbidity_data,
                    x="Count",
                    y="Comorbidity",
                    orientation="h",
                    title=f"Common Comorbidities for {selected_condition}",
                    labels={"Count": "Prevalence (%)", "Comorbidity": ""},
                    color="Count",
                    color_continuous_scale="Viridis"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Additional metrics if available
                st.markdown("#### Additional Metrics")
                
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    if "avg_hospital_stay" in condition_data:
                        st.metric("Avg. Hospital Stay (days)", condition_data["avg_hospital_stay"])
                    else:
                        st.metric("Avg. Hospital Stay (days)", "N/A")
                
                with metric_col2:
                    if "mortality_rate" in condition_data:
                        st.metric("Mortality Rate (%)", condition_data["mortality_rate"])
                    else:
                        st.metric("Mortality Rate (%)", "N/A")
                
                with metric_col3:
                    sample_size = {"Normal": 10192, "Pneumonia": 1345, "COVID-19": 3616}
                    st.metric("Sample Size", sample_size.get(selected_condition, "N/A"))
                
                # Common treatments if available
                if "common_treatments" in condition_data:
                    st.markdown("#### Common Treatments")
                    
                    for treatment in condition_data["common_treatments"]:
                        st.markdown(f"- {treatment}")
            else:
                st.info(f"No detailed insights available for {selected_condition}.")
                
            # Show comparison with current case
            if 'current_prediction' in st.session_state and st.session_state.current_prediction:
                with st.expander("Compare with Current Case"):
                    current_prediction = st.session_state.current_prediction['class_label']
                    current_age = st.session_state.patient_data.get('age', '')
                    current_gender = st.session_state.patient_data.get('gender', '')
                    
                    st.markdown(f"""
                    #### Current Case:
                    - **Diagnosis:** {current_prediction}
                    - **Age:** {current_age}
                    - **Gender:** {current_gender}
                    
                    This case can be compared with the population statistics shown above.
                    """)

if __name__ == "__main__":
    app()