import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

def overlay_heatmap_on_image(image, heatmap, alpha=0.4):
    """
    Overlay a heatmap on an image
    
    Args:
        image: The original image as a numpy array
        heatmap: The heatmap as a numpy array
        alpha: Transparency factor
        
    Returns:
        Image with overlayed heatmap
    """
    # Ensure image is RGB
    if len(image.shape) == 2:
        image_rgb = np.stack([image, image, image], axis=2)
    else:
        image_rgb = image
    
    # Resize image to match heatmap if needed
    if image_rgb.shape[:2] != heatmap.shape:
        image_rgb = np.array(Image.fromarray(image_rgb).resize((heatmap.shape[1], heatmap.shape[0])))
    
    # Create a colormap
    cmap = plt.cm.jet
    heatmap_colored = cmap(heatmap)[:, :, :3]  # Remove alpha channel
    
    # Convert to 0-255 range
    heatmap_colored = (heatmap_colored * 255).astype(np.uint8)
    
    # Overlay heatmap on image
    overlay = image_rgb.copy()
    mask = heatmap > 0.2  # Threshold to show only significant activations
    overlay[mask] = overlay[mask] * (1 - alpha) + heatmap_colored[mask] * alpha
    
    return overlay

def create_prediction_bar_chart(prediction_class, confidence):
    """
    Create a bar chart visualization for prediction confidence
    
    Args:
        prediction_class: The predicted class label
        confidence: The confidence score
        
    Returns:
        Plotly figure object
    """
    class_labels = ['Normal', 'Pneumonia', 'COVID-19']
    confidences = [0.0, 0.0, 0.0]
    
    # Set the confidence for the predicted class
    if prediction_class in class_labels:
        index = class_labels.index(prediction_class)
        confidences[index] = confidence
    
    # Create a bar chart
    fig = px.bar(
        x=class_labels,
        y=confidences,
        color=confidences,
        color_continuous_scale=['blue', 'green', 'red'],
        labels={'x': 'Diagnosis', 'y': 'Confidence'},
        title='Prediction Confidence'
    )
    
    # Set y-axis to range from 0 to 1
    fig.update_layout(yaxis_range=[0, 1])
    
    return fig

def create_patient_demographics_chart(df):
    """
    Create a pie chart of patient demographics
    
    Args:
        df: DataFrame containing patient data
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    # Gender distribution
    gender_counts = df['gender'].value_counts().reset_index()
    gender_counts.columns = ['Gender', 'Count']
    
    fig = px.pie(
        gender_counts, 
        values='Count', 
        names='Gender',
        title='Gender Distribution',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    return fig

def create_age_distribution_chart(df):
    """
    Create a histogram of age distribution
    
    Args:
        df: DataFrame containing patient data
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    # Try to convert age to numeric, ignoring errors
    df['age_numeric'] = pd.to_numeric(df['age'], errors='coerce')
    
    # Create age bins
    age_bins = [0, 18, 30, 45, 60, 75, 100]
    age_labels = ['0-18', '19-30', '31-45', '46-60', '61-75', '76+']
    
    df['age_group'] = pd.cut(df['age_numeric'], bins=age_bins, labels=age_labels, right=False)
    
    age_dist = df['age_group'].value_counts().sort_index().reset_index()
    age_dist.columns = ['Age Group', 'Count']
    
    fig = px.bar(
        age_dist,
        x='Age Group',
        y='Count',
        title='Age Distribution',
        color='Count',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    
    return fig

def create_diagnosis_distribution_chart(df):
    """
    Create a bar chart of diagnosis distribution
    
    Args:
        df: DataFrame containing patient data
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    # Diagnosis distribution
    diagnosis_counts = df['prediction'].value_counts().reset_index()
    diagnosis_counts.columns = ['Diagnosis', 'Count']
    
    fig = px.bar(
        diagnosis_counts,
        x='Diagnosis',
        y='Count',
        title='Diagnosis Distribution',
        color='Diagnosis',
        color_discrete_map={
            'Normal': 'green',
            'Pneumonia': 'orange',
            'COVID-19': 'red'
        }
    )
    
    return fig

def create_confidence_histogram(df):
    """
    Create a histogram of prediction confidence scores
    
    Args:
        df: DataFrame containing prediction data
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    fig = px.histogram(
        df,
        x='confidence',
        nbins=10,
        range_x=[0, 1],
        title='Prediction Confidence Distribution',
        labels={'confidence': 'Confidence Score'},
        color_discrete_sequence=['lightblue']
    )
    
    return fig

def create_age_vs_diagnosis_chart(df):
    """
    Create a box plot of age vs diagnosis
    
    Args:
        df: DataFrame containing patient and prediction data
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    df['age_numeric'] = pd.to_numeric(df['age'], errors='coerce')
    
    fig = px.box(
        df,
        x='prediction',
        y='age_numeric',
        color='prediction',
        title='Age Distribution by Diagnosis',
        labels={'prediction': 'Diagnosis', 'age_numeric': 'Age'},
        color_discrete_map={
            'Normal': 'green',
            'Pneumonia': 'orange',
            'COVID-19': 'red'
        }
    )
    
    return fig

def create_gender_vs_diagnosis_chart(df):
    """
    Create a grouped bar chart of gender vs diagnosis
    
    Args:
        df: DataFrame containing patient and prediction data
        
    Returns:
        Plotly figure object
    """
    if df.empty:
        return None
    
    gender_diagnosis = df.groupby(['gender', 'prediction']).size().reset_index(name='count')
    
    fig = px.bar(
        gender_diagnosis,
        x='gender',
        y='count',
        color='prediction',
        title='Diagnosis Distribution by Gender',
        labels={'gender': 'Gender', 'count': 'Count', 'prediction': 'Diagnosis'},
        barmode='group',
        color_discrete_map={
            'Normal': 'green',
            'Pneumonia': 'orange',
            'COVID-19': 'red'
        }
    )
    
    return fig
