import torch
import numpy as np
import cv2

class GradCAM:
    """
    Grad-CAM implementation for model interpretability
    """
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.register_hooks()
    
    def register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        # Register the hooks
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
    
    def generate(self, input_tensor, target_class=None):
        # Forward pass
        model_output = self.model(input_tensor)
        
        # If target_class is None, use the predicted class
        if target_class is None:
            target_class = torch.argmax(model_output).item()
        
        # Zero gradients
        self.model.zero_grad()
        
        # Backward pass
        output = model_output[0, target_class]
        output.backward()
        
        # Get weights
        gradients = self.gradients.mean(dim=(2, 3), keepdim=True)
        
        # Weight the activations
        cam = torch.sum(gradients * self.activations, dim=1, keepdim=True)
        
        # Apply ReLU
        cam = torch.nn.functional.relu(cam)
        
        # Normalize and convert to numpy
        if torch.max(cam) > 0:
            cam = cam / torch.max(cam)
        cam = cam.detach().cpu().numpy()[0, 0]
        
        return cam

def generate_gradcam(model, image_tensor, target_class=None, device='cpu'):
    """
    Generate Grad-CAM heatmap for the given image tensor
    
    Args:
        model: PyTorch model
        image_tensor: Preprocessed image tensor
        target_class: Target class index (None to use predicted class)
        device: Device to run on
        
    Returns:
        Grad-CAM heatmap as a numpy array
    """
    model.eval()
    
    # Move tensors to device
    image_tensor = image_tensor.to(device)
    
    # Get the model's layer to use for Grad-CAM
    target_layer = model.resnet.layer4[-1]
    
    # Create GradCAM instance
    grad_cam = GradCAM(model, target_layer)
    
    # Generate heatmap
    heatmap = grad_cam.generate(image_tensor, target_class)
    
    # Resize heatmap to match input size (224x224)
    heatmap = cv2.resize(heatmap, (224, 224))
    
    return heatmap
