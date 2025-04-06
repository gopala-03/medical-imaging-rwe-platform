import streamlit as st
import torch
import torch.nn as nn
import torchvision.models as models
import os
import requests
from tqdm.auto import tqdm
import numpy as np

# Model class definitions
class ChestXRayClassifier(nn.Module):
    def __init__(self, num_classes=3):
        super(ChestXRayClassifier, self).__init__()
        # Load pre-trained ResNet18 model with weights (updated API)
        self.resnet = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
        
        # Replace the final fully connected layer for our specific classes
        in_features = self.resnet.fc.in_features
        self.resnet.fc = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
        
    def forward(self, x):
        return self.resnet(x)

def get_model_path():
    """
    Get the path to the model file, downloading if necessary
    
    Returns:
        Path to the model file
    """
    # Define model directory and path
    model_dir = os.path.join(os.getcwd(), "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "chest_xray_model.pth")
    
    # For now we'll use a dummy saved model since we can't really train one in this context
    # In a real-world scenario, you would download a pre-trained model or use one from your assets
    if not os.path.exists(model_path):
        try:
            # Create a model
            model = ChestXRayClassifier(num_classes=3)
            
            # In a real application, this is where we would download a pre-trained model
            # from a secure storage service or load from a local file
            
            # Save the model to disk
            torch.save(model.state_dict(), model_path)
            st.info("Model created and saved locally")
        except Exception as e:
            st.error(f"Error creating model: {str(e)}")
            # Create a basic fallback model and save it
            model = ChestXRayClassifier(num_classes=3)
            # Use a simpler save method that might be more compatible
            try:
                torch.save(model.state_dict(), model_path, _use_new_zipfile_serialization=False)
                st.info("Fallback model created and saved")
            except:
                # Last resort - create the model but don't save it
                return None
    
    return model_path

def load_model(model_path):
    """
    Load the model from the given path
    
    Args:
        model_path: Path to the model file
        
    Returns:
        Loaded model
    """
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = ChestXRayClassifier(num_classes=3)
    
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    
    return model

def predict(model, image_tensor, device):
    """
    Make prediction using the model
    
    Args:
        model: The neural network model
        image_tensor: Preprocessed image tensor
        device: Device to run inference on
        
    Returns:
        Class index, class label, and confidence score
    """
    model.eval()
    with torch.no_grad():
        image_tensor = image_tensor.to(device)
        outputs = model(image_tensor)
        probs = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probs, 1)
    
    class_idx = predicted.item()
    confidence_score = confidence.item()
    
    # Class labels
    class_labels = ['Normal', 'Pneumonia', 'COVID-19']
    class_label = class_labels[class_idx]
    
    return class_idx, class_label, confidence_score

def get_gradcam(model, image_tensor, device, target_layer_name='layer4'):
    """
    Generate Grad-CAM heatmap for the given image
    
    Args:
        model: The neural network model
        image_tensor: Preprocessed image tensor
        device: Device to run inference on
        target_layer_name: Name of the target layer for Grad-CAM
        
    Returns:
        Heatmap as numpy array
    """
    # This is a simplified implementation of Grad-CAM
    model.eval()
    
    # Register hooks to get activations and gradients
    activations = {}
    gradients = {}
    
    def get_activation(name):
        def hook(model, input, output):
            activations[name] = output.detach()
        return hook
    
    def get_gradient(name):
        def hook(grad):
            gradients[name] = grad.detach()
        return hook
    
    # Get the target layer
    if target_layer_name == 'layer4':
        target_layer = model.resnet.layer4
    
    # Register forward hook to get activations
    handle_activation = target_layer.register_forward_hook(get_activation(target_layer_name))
    
    # Register backward hook to get gradients
    handle_gradient = target_layer.register_full_backward_hook(
        lambda module, grad_in, grad_out: gradients.update({target_layer_name: grad_out[0]})
    )
    
    # Forward pass
    image_tensor = image_tensor.to(device)
    output = model(image_tensor)
    
    # Get the class with the highest score
    pred_class = torch.argmax(output).item()
    
    # Backward pass for the predicted class
    model.zero_grad()
    output[0, pred_class].backward()
    
    # Get the gradient and activation
    activations_value = activations[target_layer_name]
    gradient_value = gradients[target_layer_name]
    
    # Clean up hooks
    handle_activation.remove()
    handle_gradient.remove()
    
    # Compute weight for each channel
    weights = torch.mean(gradient_value, dim=(1, 2), keepdim=True)
    
    # Compute weighted combination of forward activation maps
    cam = torch.sum(weights * activations_value, dim=0).cpu().numpy()
    
    # ReLU on the CAM
    cam = np.maximum(cam, 0)
    
    # Resize CAM to the input image size
    cam = cv2.resize(cam, (224, 224))
    
    # Normalize the CAM
    if np.max(cam) > 0:
        cam = cam / np.max(cam)
    
    return cam

# For the Grad-CAM import
import cv2
