import streamlit as st
import numpy as np
from PIL import Image
import tensorflow as tf
import io

# =====================================
# 🎨 PAGE CONFIGURATION
# =====================================
st.set_page_config(
    page_title="Oral Cancer Detection",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =====================================
# 🎯 CUSTOM CSS
# =====================================
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 10px;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
        border: none;
    }
    .upload-text {
        text-align: center;
        color: #666;
        padding: 2rem;
        border: 2px dashed #ddd;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .result-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
    }
    .result-normal {
        background-color: #d4edda;
        border: 2px solid #28a745;
        color: #155724;
    }
    .result-cancer {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        color: #721c24;
    }
    .confidence-bar {
        background-color: #e9ecef;
        border-radius: 10px;
        height: 30px;
        margin: 1rem 0;
        overflow: hidden;
    }
    .confidence-fill {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        transition: width 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================
# 🤖 LOAD MODEL
# =====================================
@st.cache_resource
def load_model():
    """Load TFLite model"""
    try:
        # Load TFLite model
        interpreter = tf.lite.Interpreter(model_path="model.tflite")
        interpreter.allocate_tensors()
        return interpreter
    except Exception as e:
        st.error(f"⚠️ Error loading model: {e}")
        st.info("💡 Make sure 'model.tflite' is in the same folder as this script!")
        return None

# =====================================
# 🔍 PREPROCESSING FUNCTION
# =====================================
def preprocess_image(image, target_size=(224, 224)):
    """
    Preprocess image for model prediction
    
    Args:
        image: PIL Image
        target_size: tuple (height, width)
    
    Returns:
        Preprocessed numpy array
    """
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize image
    image = image.resize(target_size)
    
    # Convert to numpy array
    img_array = np.array(image)
    
    # Normalize to [0, 1]
    img_array = img_array.astype('float32') / 255.0
    
    # Add batch dimension
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array

# =====================================
# 🎯 PREDICTION FUNCTION
# =====================================
def predict(interpreter, image):
    """
    Make prediction using TFLite model
    
    Args:
        interpreter: TFLite interpreter
        image: Preprocessed image array
    
    Returns:
        tuple: (prediction_class, confidence)
    """
    # Get input and output details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], image)
    
    # Run inference
    interpreter.invoke()
    
    # Get output tensor
    output = interpreter.get_tensor(output_details[0]['index'])
    
    # Get prediction
    # Assuming binary classification: [Normal, Cancer] or [Cancer, Normal]
    # Adjust based on your model's output
    confidence = float(output[0][0])
    
    # If confidence > 0.5, it's Cancer (class 1)
    # If confidence < 0.5, it's Normal (class 0)
    if confidence > 0.5:
        prediction = "Cancer"
        confidence_percent = confidence * 100
    else:
        prediction = "Normal"
        confidence_percent = (1 - confidence) * 100
    
    return prediction, confidence_percent

# =====================================
# 🎨 DISPLAY RESULT
# =====================================
def display_result(prediction, confidence):
    """Display prediction result with styling"""
    
    if prediction == "Normal":
        st.markdown(f"""
            <div class="result-box result-normal">
                <h2>✅ Hasil: NORMAL</h2>
                <p style="font-size: 1.2rem; margin: 1rem 0;">
                    Tidak terdeteksi tanda-tanda kanker mulut
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Confidence bar (green)
        st.markdown(f"""
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence}%; background-color: #28a745;">
                    {confidence:.1f}% Confidence
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.info("ℹ️ **Catatan:** Hasil ini adalah prediksi AI dan tidak menggantikan diagnosis medis profesional.")
        
    else:  # Cancer
        st.markdown(f"""
            <div class="result-box result-cancer">
                <h2>⚠️ Hasil: TERDETEKSI KANKER</h2>
                <p style="font-size: 1.2rem; margin: 1rem 0;">
                    Terdeteksi kemungkinan kanker mulut
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Confidence bar (red)
        st.markdown(f"""
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: {confidence}%; background-color: #dc3545;">
                    {confidence:.1f}% Confidence
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.warning("⚠️ **PENTING:** Segera konsultasikan dengan dokter atau ahli kesehatan untuk pemeriksaan lebih lanjut!")
        
        # Recommendations
        st.markdown("""
            ### 📋 Langkah Selanjutnya:
            1. 🏥 Konsultasi dengan dokter gigi atau spesialis
            2. 🔬 Lakukan pemeriksaan medis menyeluruh
            3. 📸 Bawa foto ini saat konsultasi
            4. ⏰ Jangan tunda pemeriksaan
        """)

# =====================================
# 🎯 MAIN APP
# =====================================
def main():
    # Header
    st.markdown("""
        <h1 style='text-align: center; color: #FF4B4B;'>
            🦷 Oral Cancer Detection
        </h1>
        <p style='text-align: center; font-size: 1.2rem; color: #666;'>
            Deteksi dini kanker mulut menggunakan AI
        </p>
        <hr style='margin: 2rem 0;'>
    """, unsafe_allow_html=True)
    
    # Load model
    interpreter = load_model()
    
    if interpreter is None:
        st.error("❌ Model tidak dapat dimuat. Aplikasi tidak dapat berjalan.")
        st.info("""
            ### 📦 Cara Menjalankan Aplikasi:
            
            1. Pastikan file `model.tflite` ada di folder yang sama
            2. Install dependencies: `pip install streamlit tensorflow pillow numpy`
            3. Jalankan: `streamlit run oral_cancer_webapp.py`
        """)
        return
    
    # Instructions
    with st.expander("📖 Cara Menggunakan", expanded=False):
        st.markdown("""
            ### Panduan Penggunaan:
            
            1. 📸 **Upload foto** area mulut yang ingin diperiksa
            2. 🖼️ **Format yang didukung:** JPG, JPEG, PNG
            3. 🎯 **Klik "Analisis Gambar"** untuk memulai deteksi
            4. ⏱️ **Tunggu beberapa detik** untuk hasil
            5. 📋 **Baca hasil** dan rekomendasi yang diberikan
            
            ⚠️ **Penting:** 
            - Gunakan foto yang jelas dan terang
            - Fokus pada area yang ingin diperiksa
            - Hasil ini adalah prediksi AI, bukan diagnosis medis
        """)
    
    # File uploader
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📤 Upload Foto Area Mulut",
        type=['jpg', 'jpeg', 'png'],
        help="Pilih foto area mulut yang ingin dianalisis"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            image = Image.open(uploaded_file)
            st.image(image, caption="📸 Gambar yang diupload", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Analyze button
        if st.button("🔍 Analisis Gambar"):
            with st.spinner("🔄 Sedang menganalisis gambar..."):
                try:
                    # Preprocess image
                    processed_image = preprocess_image(image)
                    
                    # Make prediction
                    prediction, confidence = predict(interpreter, processed_image)
                    
                    # Display result
                    st.markdown("<br>", unsafe_allow_html=True)
                    display_result(prediction, confidence)
                    
                    # Additional info
                    with st.expander("ℹ️ Informasi Tambahan"):
                        st.markdown(f"""
                            - **Model:** MobileNetV2 (Fine-tuned)
                            - **Akurasi Model:** ~87.77%
                            - **Input Size:** 224x224 pixels
                            - **Prediksi:** {prediction}
                            - **Confidence:** {confidence:.2f}%
                        """)
                    
                except Exception as e:
                    st.error(f"❌ Error saat analisis: {e}")
                    st.info("Coba upload gambar lain atau periksa format file.")
    
    else:
        # Placeholder when no image uploaded
        st.markdown("""
            <div class="upload-text">
                <h3>📤 Upload gambar untuk memulai analisis</h3>
                <p>Drag & drop atau klik untuk memilih file</p>
                <p style="font-size: 0.9rem; color: #999;">Format: JPG, JPEG, PNG</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        ---
        <p style='text-align: center; color: #999; font-size: 0.9rem;'>
            🤖 Powered by TensorFlow Lite & Streamlit<br>
            ⚕️ Untuk diagnosis medis yang akurat, konsultasikan dengan dokter profesional
        </p>
    """, unsafe_allow_html=True)

# =====================================
# 🚀 RUN APP
# =====================================
if __name__ == "__main__":
    main()
