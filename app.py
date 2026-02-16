"""
Backend Server untuk Oral Cancer Detection + Upload ke Google Drive
- Endpoint /predict: Analisis gambar dengan AI model
- Endpoint /upload: Upload hasil ke Google Drive
Deploy ke: Railway, Render, atau Heroku
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import os
from datetime import datetime
import base64
import json

app = Flask(__name__)
CORS(app)  # Enable CORS untuk GitHub Pages

# ============================================
# CONFIGURATION
# ============================================
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_NAME = 'OralCancerDetection_TrainingData'
MODEL_PATH = 'oral_cancer_model.tflite'
IMG_SIZE = 224

# Global variables
drive_service = None
folder_id = None
interpreter = None
input_details = None
output_details = None

# ============================================
# AI MODEL INITIALIZATION
# ============================================
def initialize_model():
    """Load TFLite model"""
    global interpreter, input_details, output_details
    
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"⚠️ Model file not found: {MODEL_PATH}")
            return False
        
        # Load TFLite model
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        
        # Get input/output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print("✅ AI Model loaded successfully")
        print(f"   Input shape: {input_details[0]['shape']}")
        print(f"   Output shape: {output_details[0]['shape']}")
        return True
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def preprocess_image(image_bytes):
    """Preprocess image untuk model"""
    try:
        # Load image
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Resize
        img = img.resize((IMG_SIZE, IMG_SIZE))
        
        # Convert to array and normalize
        img_array = np.array(img, dtype=np.float32) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
        
    except Exception as e:
        print(f"❌ Error preprocessing image: {e}")
        return None

def predict_image(image_bytes):
    """Run inference dengan TFLite model"""
    try:
        # Preprocess
        img_array = preprocess_image(image_bytes)
        if img_array is None:
            return None
        
        # Set input tensor
        interpreter.set_tensor(input_details[0]['index'], img_array)
        
        # Run inference
        interpreter.invoke()
        
        # Get output
        prediction = interpreter.get_tensor(output_details[0]['index'])[0][0]
        
        return float(prediction)
        
    except Exception as e:
        print(f"❌ Error during prediction: {e}")
        return None

# ============================================
# GOOGLE DRIVE FUNCTIONS (EXISTING)
# ============================================
def initialize_drive_service():
    """Initialize Google Drive service dengan service account"""
    global drive_service, folder_id
    
    try:
        service_account_info = os.environ.get('SERVICE_ACCOUNT_KEY')
        
        if service_account_info:
            service_account_dict = json.loads(service_account_info)
            credentials = service_account.Credentials.from_service_account_info(
                service_account_dict, scopes=SCOPES)
        else:
            credentials = service_account.Credentials.from_service_account_file(
                'service-account-key.json', scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Google Drive service initialized")
        
        folder_id = create_or_get_folder()
        print(f"✅ Folder ID: {folder_id}")
        
    except Exception as e:
        print(f"⚠️ Drive service not initialized: {e}")

def create_or_get_folder():
    """Create folder jika belum ada"""
    try:
        response = drive_service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and name='{FOLDER_NAME}' and trashed=false",
            spaces='drive',
            fields='files(id, name)').execute()
        
        files = response.get('files', [])
        
        if files:
            return files[0]['id']
        
        file_metadata = {
            'name': FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = drive_service.files().create(
            body=file_metadata,
            fields='id').execute()
        
        print(f"✅ Created new folder: {FOLDER_NAME}")
        return folder.get('id')
        
    except Exception as e:
        print(f"❌ Error creating folder: {e}")
        return None

def upload_to_drive(image_data, filename, metadata_dict):
    """Upload image ke Google Drive"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id],
            'description': metadata_dict.get('description', '')
        }
        
        if 'properties' in metadata_dict:
            file_metadata['properties'] = metadata_dict['properties']
        
        media = MediaIoBaseUpload(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            resumable=True
        )
        
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink').execute()
        
        print(f"✅ Uploaded: {filename}")
        
        return {
            'success': True,
            'file_id': file.get('id'),
            'file_name': file.get('name'),
            'web_link': file.get('webViewLink')
        }
        
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return {
            'success': False,
            'error': str(e)
        }

# ============================================
# API ENDPOINTS
# ============================================
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'oral-cancer-detection',
        'model_loaded': interpreter is not None,
        'drive_connected': drive_service is not None
    })

@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint untuk prediksi AI
    
    Expected payload:
    {
        "image": "data:image/jpeg;base64,..."
    }
    
    Returns:
    {
        "success": true,
        "prediction_value": 0.234,
        "diagnosis": "Normal (Non-Cancer)",
        "confidence": 76.6,
        "risk_level": "Low",
        "recommendation": "..."
    }
    """
    try:
        # Check if model is loaded
        if interpreter is None:
            return jsonify({
                'success': False,
                'error': 'Model not loaded'
            }), 500
        
        # Get data
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        image_data = data['image']
        
        # Decode base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Predict
        prediction = predict_image(image_bytes)
        
        if prediction is None:
            return jsonify({
                'success': False,
                'error': 'Error during prediction'
            }), 500
        
        # Interpret hasil
        # Model output: 0 = Cancer, 1 = Non-Cancer
        is_cancer = prediction < 0.5
        confidence = (1 - prediction) if is_cancer else prediction
        
        # Get recommendation
        def get_recommendation(is_cancer, confidence):
            if is_cancer:
                if confidence > 0.8:
                    return "⚠️ Terdeteksi indikasi kanker mulut dengan tingkat kepercayaan tinggi. SEGERA konsultasi ke dokter spesialis!"
                else:
                    return "⚠️ Terdeteksi kemungkinan kanker mulut. Disarankan untuk segera konsultasi ke dokter untuk pemeriksaan lebih lanjut."
            else:
                if confidence > 0.8:
                    return "✅ Kondisi mulut terlihat normal. Tetap jaga kesehatan mulut dengan rutin."
                else:
                    return "✅ Kondisi mulut terlihat normal, namun tetap disarankan pemeriksaan rutin ke dokter gigi."
        
        result = {
            'success': True,
            'prediction_value': float(prediction),
            'diagnosis': 'Cancer Detected' if is_cancer else 'Normal (Non-Cancer)',
            'confidence': float(confidence * 100),
            'risk_level': 'High' if is_cancer else 'Low',
            'recommendation': get_recommendation(is_cancer, confidence),
            'model_info': {
                'accuracy': 85.71,
                'sensitivity': 84.35,
                'specificity': 86.92
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error in predict endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    """Upload image ke Google Drive (EXISTING ENDPOINT)"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        image_data = data['image']
        prediction = data.get('prediction', {})
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        probability = prediction.get('probability', 0)
        percentage = int(probability * 100)
        filename = f"oral_cancer_{timestamp}_{percentage}pct.jpg"
        
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
                'version': '2.0',
                'timestamp': timestamp,
                'prediction_percentage': str(percentage),
                'classification': prediction.get('classification', 'Unknown'),
                'severity': prediction.get('severity', 'Unknown')
            }
        }
        
        result = upload_to_drive(image_data, filename, metadata)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        print(f"❌ Error in upload endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics dari folder Drive (EXISTING ENDPOINT)"""
    try:
        if not drive_service or not folder_id:
            return jsonify({
                'success': False,
                'error': 'Drive service not initialized'
            }), 500
        
        response = drive_service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='files(id, name, createdTime, properties)').execute()
        
        files = response.get('files', [])
        
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

# ============================================
# STARTUP
# ============================================
# Initialize model saat startup
model_loaded = initialize_model()
if not model_loaded:
    print("⚠️ WARNING: Model not loaded! /predict endpoint will not work.")

# Initialize Drive service (optional, bisa skip jika tidak pakai)
try:
    initialize_drive_service()
except Exception as e:
    print(f"⚠️ Drive service not initialized: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)