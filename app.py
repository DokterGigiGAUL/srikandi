from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import base64
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MODEL_PATH = 'oral_cancer_model.tflite'
IMG_SIZE = 224

interpreter = None
input_details = None
output_details = None

def initialize_model():
    global interpreter, input_details, output_details
    try:
        if not os.path.exists(MODEL_PATH):
            print(f"Model not found: {MODEL_PATH}")
            return False
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        print("AI Model loaded successfully")
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

def predict_image(image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img = img.resize((IMG_SIZE, IMG_SIZE))
        img_array = np.array(img, dtype=np.float32) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        interpreter.set_tensor(input_details[0]['index'], img_array)
        interpreter.invoke()
        prediction = interpreter.get_tensor(output_details[0]['index'])[0][0]
        return float(prediction)
    except Exception as e:
        print(f"Prediction error: {e}")
        return None

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Oral Cancer Detection API',
        'status': 'running',
        'model_loaded': interpreter is not None
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': interpreter is not None
    })

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if interpreter is None:
            return jsonify({'success': False, 'error': 'Model not loaded'}), 500
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400
        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        prediction = predict_image(image_bytes)
        if prediction is None:
            return jsonify({'success': False, 'error': 'Prediction failed'}), 500
        prob_non_cancer = prediction
        prob_cancer = 1 - prediction
        
        # Zona threshold konservatif
        if prob_cancer >= 0.8:
            is_cancer = True
            confidence = prob_cancer
    
        if confidence >= 0.9:
            recommendation = "⚠️ Suspek kanker mulut dengan tingkat kepercayaan AI sangat tinggi. Konsultasi ke dokter gigi spesialis penyakit mulut, SEGERA!"
        else:
            recommendation = "⚠️ Terdeteksi kemungkinan lesi kanker mulut. Disarankan untuk konsultasi ke dokter gigi umum/ spesialis penyakit mulut."
    
        elif prob_cancer <= 0.4:
            is_cancer = False
            confidence = prob_non_cancer
    
        if confidence >= 0.8:
            recommendation = "✅ Kondisi mulut terlihat normal. Tetap jaga kesehatan mulut dengan rutin."
        else:
            recommendation = "✅ Kondisi mulut terlihat normal, namun tetap disarankan pemeriksaan untuk memastikan keamanan."
    
        else:
        # Zona abu-abu 40–80% → default tampil sebagai NON kanker
        is_cancer = False
        confidence = prob_non_cancer
        recommendation = "ℹ️ Hasil berada pada zona borderline. Disarankan evaluasi klinis langsung  untuk memastikan kondisi lesi."
        return jsonify({
            'success': True,
            'prediction_value': float(prediction),
            'diagnosis': 'Cancer Detected' if is_cancer else 'Normal (Non-Cancer)',
            'confidence': float(confidence * 100),
            'risk_level': 'High' if is_cancer else 'Low',
            'recommendation': recommendation,
            'model_info': {
                'accuracy': 99.40,
                'sensitivity': 67.32,
                'specificity': 99.67
            }
        }), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

print("Starting Oral Cancer Detection API...")
initialize_model()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
