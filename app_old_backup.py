"""
Backend Server untuk Upload ke Google Drive
Menggunakan Service Account agar gambar tersimpan ke Drive owner, bukan user

Deploy ke: Vercel, Railway, Render, atau Heroku

Install dependencies:
pip install flask flask-cors google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pillow
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import os
from datetime import datetime
import base64
import json

app = Flask(__name__)
CORS(app)  # Enable CORS untuk bisa dipanggil dari GitHub Pages

# Google Drive Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_NAME = 'OralCancerDetection_TrainingData'

# Global variables
drive_service = None
folder_id = None

def initialize_drive_service():
    """Initialize Google Drive service dengan service account"""
    global drive_service, folder_id
    
    try:
        # Get service account key from environment variable
        service_account_info = os.environ.get('SERVICE_ACCOUNT_KEY')
        
        if service_account_info:
            # Parse JSON from environment variable
            service_account_dict = json.loads(service_account_info)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_dict, scopes=SCOPES)
        else:
            # Fallback to file (for local development)
            credentials = service_account.Credentials.from_service_account_file(
                'service-account-key.json', scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✓ Google Drive service initialized")
        
        # Create or get folder
        folder_id = create_or_get_folder()
        print(f"✓ Folder ID: {folder_id}")
        
    except Exception as e:
        print(f"✗ Error initializing Drive service: {e}")
        raise

def create_or_get_folder():
    """Create folder jika belum ada, atau dapatkan ID jika sudah ada"""
    try:
        # Search for existing folder
        response = drive_service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{FOLDER_NAME}' and trashed=false",
            spaces='drive',
            fields='files(id, name)').execute()
        
        files = response.get('files', [])
        
        if files:
            return files[0]['id']
        
        # Create new folder
        file_metadata = {
            'name': FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = drive_service.files().create(
            body=file_metadata,
            fields='id').execute()
        
        print(f"✓ Created new folder: {FOLDER_NAME}")
        return folder.get('id')
        
    except Exception as e:
        print(f"✗ Error creating folder: {e}")
        return None

def upload_to_drive(image_data, filename, metadata_dict):
    """Upload image ke Google Drive"""
    try:
        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Create file metadata
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'description': metadata_dict.get('description', '')
        }
        
        # Add custom properties
        if 'properties' in metadata_dict:
            file_metadata['properties'] = metadata_dict['properties']
        
        # Upload file
        media = MediaIoBaseUpload(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            resumable=True
        )
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink').execute()
        
        print(f"✓ Uploaded: {filename} (ID: {file.get('id')})")
        
        return {
            'success': True,
            'file_id': file.get('id'),
            'file_name': file.get('name'),
            'web_link': file.get('webViewLink')
        }
        
    except Exception as e:
        print(f"✗ Error uploading to Drive: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'oral-cancer-drive-uploader',
        'drive_connected': drive_service is not None
    })

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Upload image endpoint
    
    Expected JSON payload:
    {
        "image": "data:image/jpeg;base64,...",
        "prediction": {
            "probability": 0.75,
            "classification": "Abnormal",
            "confidence": 0.85,
            "severity": "Tinggi"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        # Extract data
        image_data = data['image']
        prediction = data.get('prediction', {})
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        probability = prediction.get('probability', 0)
        percentage = int(probability * 100)
        filename = f"oral_cancer_{timestamp}_{percentage}pct.jpg"
        
        # Prepare metadata
        metadata = {
            'description': f"""
Oral Cancer Detection Upload
Timestamp: {datetime.now().isoformat()}
Prediction: {percentage}%
Classification: {prediction.get('classification', 'Unknown')}
Confidence: {prediction.get('confidence', 0) * 100:.1f}%
Severity: {prediction.get('severity', 'Unknown')}
            """.strip(),
            'properties': {
                'app': 'OralCancerDetection',
                'version': '1.0',
                'timestamp': timestamp,
                'prediction_percentage': str(percentage),
                'classification': prediction.get('classification', 'Unknown'),
                'severity': prediction.get('severity', 'Unknown')
            }
        }
        
        # Upload to Drive
        result = upload_to_drive(image_data, filename, metadata)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"✗ Error in upload endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics dari folder Drive"""
    try:
        # Count files in folder
        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='files(id, name, createdTime, properties)').execute()
        
        files = response.get('files', [])
        
        # Analyze data
        total = len(files)
        cancer_count = 0
        normal_count = 0
        
        for file in files:
            props = file.get('properties', {})
            percentage = int(props.get('prediction_percentage', 0))
            
            if percentage > 50:
                cancer_count += 1
            else:
                normal_count += 1
        
        return jsonify({
            'success': True,
            'total_images': total,
            'cancer_predictions': cancer_count,
            'normal_predictions': normal_count,
            'folder_id': folder_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Initialize Drive service saat startup
try:
    initialize_drive_service()
except Exception as e:
    print(f"Warning: Failed to initialize Drive service: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)