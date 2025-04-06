import psycopg2
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using environment variables directly.")
    
# Database connection parameters from environment variables
DB_PARAMS = {
    "dbname": os.environ.get("PGDATABASE"),
    "user": os.environ.get("PGUSER"),
    "password": os.environ.get("PGPASSWORD"),
    "host": os.environ.get("PGHOST"),
    "port": os.environ.get("PGPORT")
}

# Check if environment variables are set
missing_vars = [k for k, v in DB_PARAMS.items() if v is None]
if missing_vars:
    print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
    print("Please set these variables in a .env file or in your environment.")
    print("Example .env file format:")
    print("PGDATABASE=your_database_name")
    print("PGUSER=your_database_user")
    print("PGPASSWORD=your_database_password")
    print("PGHOST=localhost")
    print("PGPORT=5432")
    sys.exit(1)

print("Connecting to PostgreSQL database...")
try:
    conn = psycopg2.connect(**DB_PARAMS)
    print("Connection successful!")
except Exception as e:
    print(f"Error connecting to database: {e}")
    print("Please check your PostgreSQL installation and environment variables.")
    sys.exit(1)

print("Creating tables...")
cur = conn.cursor()

# Create tables
cur.execute("""
CREATE TABLE IF NOT EXISTS nih_xray_metadata (
    image_index VARCHAR(255) PRIMARY KEY,
    finding_labels TEXT,
    follow_up_num INTEGER,
    patient_id VARCHAR(255),
    patient_age INTEGER,
    patient_gender VARCHAR(10),
    view_position VARCHAR(10),
    original_image_width INTEGER,
    original_image_height INTEGER,
    original_image_pixel_spacing_x FLOAT,
    original_image_pixel_spacing_y FLOAT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS nih_xray_bbox (
    id SERIAL PRIMARY KEY,
    image_index VARCHAR(255),
    finding_label VARCHAR(255),
    bbox_x INTEGER,
    bbox_y INTEGER,
    bbox_w INTEGER,
    bbox_h INTEGER,
    FOREIGN KEY (image_index) REFERENCES nih_xray_metadata(image_index) ON DELETE CASCADE
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS analysis_results (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255),
    image_path TEXT,
    prediction VARCHAR(255),
    confidence FLOAT,
    age INTEGER,
    gender VARCHAR(10),
    symptoms TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
cur.close()
conn.close()

print("Database tables created successfully!")
print("\nNext steps:")
print("1. Create the required directories with: mkdir -p models temp data")
print("2. Run the Streamlit app with: streamlit run app.py")
print("3. Import NIH dataset metadata from the External Data page (optional)")