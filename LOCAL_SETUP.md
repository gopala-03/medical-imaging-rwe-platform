# Local Setup Guide for Medical Imaging RWE Platform

This guide provides step-by-step instructions for setting up and running the Medical Imaging RWE Platform in a local environment.

## System Requirements

- Python 3.10 or newer
- PostgreSQL database server
- 4GB+ RAM recommended (for PyTorch)
- 500MB+ free disk space

## Installation Steps

### 1. Set Up Python Environment

First, create and activate a virtual environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

Install the required Python packages:

```bash
# Install required packages
pip install streamlit matplotlib numpy opencv-python pandas pillow plotly psycopg2-binary pydicom seaborn torch torchvision tqdm python-dotenv
```

### 3. Set Up PostgreSQL Database

1. Install PostgreSQL if not already installed
2. Create a new database for the application
3. Copy the `.env.example` file to `.env` and update with your database credentials

```bash
cp .env.example .env
# Edit .env with your database details
```

### 4. Create Database Tables

Run the included setup script:

```bash
python setup_db.py
```

### 5. Create Required Directories

```bash
mkdir -p models temp data
```

### 6. Start the Application

```bash
streamlit run app.py
```

The application should now be accessible at http://localhost:5000 in your web browser.

## Optional: Importing NIH Chest X-ray Dataset

For full functionality with the NIH dataset:

1. Register on Kaggle and get your API credentials
2. Add your Kaggle credentials to the `.env` file
3. Use the External Data page in the application to import the dataset metadata

## Folder Structure

```
.
├── app.py               # Main application entry point
├── assets/              # Assets including Grad-CAM implementation
├── data/                # Data storage directory
├── models/              # AI model storage
├── pages/               # Streamlit pages for different sections
│   ├── 01_upload.py
│   ├── 02_patient_data.py
│   ├── 03_analysis.py
│   ├── 04_dashboard.py
│   ├── 05_external_data.py
│   └── 06_nih_dataset.py
├── setup_db.py          # Database setup script
├── temp/                # Temporary file storage
└── utils/               # Utility modules
    ├── data_handling.py
    ├── database.py
    ├── external_data.py
    ├── image_processing.py
    ├── kaggle_integration.py
    ├── model.py
    └── visualization.py
```

## Common Issues

### Database Connection Problems

- Verify PostgreSQL is running
- Check the credentials in your `.env` file
- Ensure the database specified in PGDATABASE exists

### Model Loading Issues

- The application will create a basic model if the pre-trained one fails to load
- Check the `models` directory permissions

### Missing Dependencies

- If you encounter import errors, install the specific package:
  ```bash
  pip install <package_name>
  ```

### Permission Issues

- Ensure write permissions for the `models`, `temp`, and `data` directories

## Getting Help

For more advanced troubleshooting, refer to the README.md file or submit an issue to the repository.