"""
Script untuk melatih model deteksi kanker mulut dan mengkonversinya ke format web
Menggunakan dataset dari Kaggle
"""

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
import tensorflowjs as tfjs
import numpy as np
import os

# Konfigurasi
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 20
DATA_DIR = 'path/to/kaggle/dataset'  # Ganti dengan path dataset Anda

def create_model():
    """
    Membuat model menggunakan MobileNetV2 (lightweight untuk web)
    """
    # Base model (pretrained)
    base_model = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Build model
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(1, activation='sigmoid')  # Binary classification
    ])
    
    return model

def prepare_data():
    """
    Mempersiapkan data training dan validation
    """
    # Data augmentation untuk training
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=30,
        width_shift_range=0.3,
        height_shift_range=0.3,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        validation_split=0.2
    )
    
    # Training generator
    train_generator = train_datagen.flow_from_directory(
        DATA_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='binary',
        subset='training',
        shuffle=True
    )
    
    # Validation generator
    val_generator = train_datagen.flow_from_directory(
        DATA_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='binary',
        subset='validation',
        shuffle=False
    )
    
    return train_generator, val_generator

def train_model():
    """
    Melatih model
    """
    print("🔧 Membuat model...")
    model = create_model()
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy', 
                 tf.keras.metrics.Precision(),
                 tf.keras.metrics.Recall()]
    )
    
    print("📊 Mempersiapkan data...")
    train_gen, val_gen = prepare_data()
    
    # Callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7
        ),
        tf.keras.callbacks.ModelCheckpoint(
            'best_model.h5',
            monitor='val_accuracy',
            save_best_only=True,
            mode='max'
        )
    ]
    
    print("🚀 Memulai training...")
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Fine-tuning (optional)
    print("\n🔬 Fine-tuning model...")
    base_model = model.layers[0]
    base_model.trainable = True
    
    # Freeze early layers
    for layer in base_model.layers[:-30]:
        layer.trainable = False
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    history_fine = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=10,
        callbacks=callbacks,
        verbose=1
    )
    
    return model, history

def convert_to_tflite(model):
    """
    Konversi model ke TFLite (untuk web yang lebih ringan)
    """
    print("\n📦 Mengkonversi ke TFLite...")
    
    # Convert
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    # Save
    with open('oral_cancer_model.tflite', 'wb') as f:
        f.write(tflite_model)
    
    print("✅ Model TFLite disimpan: oral_cancer_model.tflite")
    
    # Cek ukuran
    size_mb = len(tflite_model) / (1024 * 1024)
    print(f"📊 Ukuran model: {size_mb:.2f} MB")

def convert_to_tfjs(model):
    """
    Konversi model ke TensorFlow.js format
    """
    print("\n📦 Mengkonversi ke TensorFlow.js...")
    
    tfjs.converters.save_keras_model(model, 'tfjs_model')
    print("✅ Model TFJS disimpan di folder: tfjs_model/")

def convert_to_onnx():
    """
    Konversi model ke ONNX (alternatif yang lebih ringan)
    Memerlukan: pip install tf2onnx
    """
    print("\n📦 Mengkonversi ke ONNX...")
    
    import tf2onnx
    
    spec = (tf.TensorSpec((None, IMG_SIZE, IMG_SIZE, 3), tf.float32, name="input"),)
    
    model_proto, _ = tf2onnx.convert.from_keras(
        'best_model.h5',
        input_signature=spec,
        opset=13,
        output_path='oral_cancer_model.onnx'
    )
    
    print("✅ Model ONNX disimpan: oral_cancer_model.onnx")

def evaluate_model(model):
    """
    Evaluasi performa model
    """
    print("\n📈 Evaluasi model...")
    
    _, val_gen = prepare_data()
    
    results = model.evaluate(val_gen)
    
    print(f"\n{'='*50}")
    print(f"Validation Loss: {results[0]:.4f}")
    print(f"Validation Accuracy: {results[1]:.4f}")
    if len(results) > 2:
        print(f"Validation Precision: {results[2]:.4f}")
        print(f"Validation Recall: {results[3]:.4f}")
    print(f"{'='*50}")

def create_test_inference():
    """
    Membuat file test untuk inferensi
    """
    code = """
import tensorflow as tf
import numpy as np
from PIL import Image

# Load model
model = tf.lite.Interpreter(model_path='oral_cancer_model.tflite')
model.allocate_tensors()

# Get input and output details
input_details = model.get_input_details()
output_details = model.get_output_details()

# Load and preprocess image
img = Image.open('test_image.jpg')
img = img.resize((224, 224))
img_array = np.array(img) / 255.0
img_array = np.expand_dims(img_array, axis=0).astype(np.float32)

# Run inference
model.set_tensor(input_details[0]['index'], img_array)
model.invoke()

# Get prediction
prediction = model.get_tensor(output_details[0]['index'])[0][0]

print(f"Cancer probability: {prediction * 100:.2f}%")
if prediction > 0.7:
    print("Status: HIGH RISK - Konsultasi dokter segera")
elif prediction > 0.4:
    print("Status: MEDIUM RISK - Pemeriksaan lanjutan disarankan")
else:
    print("Status: LOW RISK - Tetap monitor")
"""
    
    with open('test_inference.py', 'w') as f:
        f.write(code)
    
    print("✅ Test inference script created: test_inference.py")

if __name__ == "__main__":
    print("🦷 Oral Cancer Detection - Model Training & Conversion")
    print("="*60)
    
    # Training
    model, history = train_model()
    
    # Evaluasi
    evaluate_model(model)
    
    # Save model keras
    model.save('oral_cancer_model.h5')
    print("\n✅ Model Keras disimpan: oral_cancer_model.h5")
    
    # Konversi ke berbagai format
    print("\n🔄 Konversi model ke format web...")
    
    # Pilih salah satu atau semua:
    convert_to_tflite(model)      # Paling ringan, direkomendasikan
    # convert_to_tfjs(model)      # TensorFlow.js (lebih besar)
    # convert_to_onnx()           # ONNX (alternatif ringan)
    
    # Create test file
    create_test_inference()
    
    print("\n" + "="*60)
    print("✨ Selesai! Upload file .tflite ke GitHub Pages repository")
    print("📝 Update index.html dengan kode loading model yang sesuai")
    print("="*60)
