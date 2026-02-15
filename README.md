# Oral Cancer Detection Web App

Aplikasi web untuk deteksi kanker mulut menggunakan AI/Machine Learning yang dapat di-deploy ke GitHub Pages.

## 🚀 Fitur

- ✅ Upload gambar rongga mulut
- ✅ Analisis AI real-time di browser
- ✅ Tampilan persentase probabilitas kanker
- ✅ Klasifikasi dan rekomendasi
- ✅ Interface modern dan responsive
- ✅ Tidak memerlukan backend server
- ✅ Privasi terjaga (analisis di browser)

## 📋 Cara Deploy ke GitHub Pages

### 1. Setup Repository

```bash
# Clone atau buat repository baru
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO-NAME.git
git push -u origin main
```

### 2. Aktifkan GitHub Pages

1. Buka repository di GitHub
2. Settings → Pages
3. Source: pilih branch `main` dan folder `/` (root)
4. Save
5. Website akan tersedia di `https://USERNAME.github.io/REPO-NAME/`

## 🤖 Integrasi Model dari Kaggle

### Pilihan 1: TensorFlow.js Lite (Direkomendasikan untuk GitHub Pages)

1. **Download dan Convert Model**

```bash
# Install TensorFlow
pip install tensorflow tensorflowjs

# Convert model Keras/SavedModel ke TFLite
python -c "
import tensorflow as tf
converter = tf.lite.TFLiteConverter.from_saved_model('model_path')
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()
with open('model.tflite', 'wb') as f:
    f.write(tflite_model)
"
```

2. **Gunakan TFLite di Web**

Tambahkan di `<head>`:
```html
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs-tflite@0.0.1-alpha.8/dist/tf-tflite.min.js"></script>
```

Update kode JavaScript:
```javascript
class OralCancerDetector {
    constructor() {
        this.model = null;
    }

    async loadModel() {
        // Load TFLite model
        this.model = await tflite.loadTFLiteModel('model.tflite');
        this.modelLoaded = true;
    }

    async predict(imageElement) {
        // Preprocess image
        const tensor = tf.browser.fromPixels(imageElement)
            .resizeBilinear([224, 224])  // Sesuaikan dengan input size model
            .toFloat()
            .div(255.0)
            .expandDims();

        // Run inference
        const predictions = await this.model.predict(tensor);
        const probability = predictions.dataSync()[0];

        tensor.dispose();
        predictions.dispose();

        return {
            probability: probability,
            confidence: 0.85,  // Bisa dihitung dari output model
            features: this.extractFeatures(probability)
        };
    }
}
```

### Pilihan 2: ONNX Runtime Web (Lebih Ringan)

1. **Convert ke ONNX**

```bash
pip install tf2onnx onnx

python -m tf2onnx.convert \
    --saved-model model_path \
    --output model.onnx \
    --opset 13
```

2. **Optimize untuk Web**

```bash
pip install onnxruntime

python -c "
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

model = onnx.load('model.onnx')
quantize_dynamic('model.onnx', 'model_quantized.onnx', weight_type=QuantType.QUInt8)
"
```

3. **Gunakan di Web**

```html
<script src="https://cdn.jsdelivr.net/npm/onnxruntime-web@1.16.0/dist/ort.min.js"></script>
```

```javascript
class OralCancerDetector {
    async loadModel() {
        this.session = await ort.InferenceSession.create('model_quantized.onnx');
        this.modelLoaded = true;
    }

    async predict(imageElement) {
        // Preprocess
        const canvas = document.createElement('canvas');
        canvas.width = 224;
        canvas.height = 224;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(imageElement, 0, 0, 224, 224);
        
        const imageData = ctx.getImageData(0, 0, 224, 224);
        const input = new Float32Array(224 * 224 * 3);
        
        for (let i = 0; i < imageData.data.length; i += 4) {
            const idx = i / 4;
            input[idx] = imageData.data[i] / 255.0;          // R
            input[idx + 224*224] = imageData.data[i+1] / 255.0;  // G
            input[idx + 224*224*2] = imageData.data[i+2] / 255.0; // B
        }

        const tensor = new ort.Tensor('float32', input, [1, 3, 224, 224]);
        const feeds = { input: tensor };  // Sesuaikan nama input
        
        const results = await this.session.run(feeds);
        const probability = results.output.data[0];  // Sesuaikan nama output

        return {
            probability: probability,
            confidence: 0.85,
            features: this.extractFeatures(probability)
        };
    }
}
```

### Pilihan 3: API Backend (Untuk Model Besar)

Jika model terlalu besar, gunakan API:

```javascript
async function predict(imageElement) {
    const canvas = document.createElement('canvas');
    canvas.width = 224;
    canvas.height = 224;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(imageElement, 0, 0, 224, 224);
    
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));
    
    const formData = new FormData();
    formData.append('image', blob);
    
    const response = await fetch('https://your-api.com/predict', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    return result;
}
```

Untuk backend, bisa gunakan:
- **Hugging Face Spaces** (gratis)
- **Google Cloud Run** (pay per use)
- **Railway.app** (gratis tier)
- **Render.com** (gratis tier)

## 📁 Struktur File

```
oral-cancer-detection/
├── index.html          # Main app
├── model.tflite        # Model AI (atau .onnx)
├── README.md          # Dokumentasi
└── LICENSE            # License file
```

## 🔧 Kustomisasi

### Ganti Threshold

```javascript
// Di function displayResults()
if (result.probability > 0.7) {  // Ubah nilai threshold
    status = 'Terdeteksi Kemungkinan Tinggi';
    // ...
}
```

### Sesuaikan Input Size Model

```javascript
// Ubah ukuran preprocessing
.resizeBilinear([224, 224])  // Ganti dengan input size model Anda
```

### Tambah Preprocessing

```javascript
async predict(imageElement) {
    const tensor = tf.browser.fromPixels(imageElement)
        .resizeBilinear([224, 224])
        .toFloat()
        .div(255.0)
        .sub([0.485, 0.456, 0.406])  // ImageNet mean
        .div([0.229, 0.224, 0.225])  // ImageNet std
        .expandDims();
    // ...
}
```

## 📊 Dataset dari Kaggle

Contoh dataset yang bisa digunakan:
- [Oral Cancer Dataset](https://www.kaggle.com/datasets/ashenafifasilkebede/dataset)
- [Oral Disease Dataset](https://www.kaggle.com/datasets/saiharsha03/oral-disease-dataset)

### Training Model Example

```python
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# Setup data
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    horizontal_flip=True,
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    'data/',
    target_size=(224, 224),
    batch_size=32,
    class_mode='binary',
    subset='training'
)

# Build model
model = tf.keras.Sequential([
    tf.keras.applications.MobileNetV2(
        include_top=False,
        input_shape=(224, 224, 3),
        weights='imagenet'
    ),
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Train
model.fit(train_generator, epochs=20)

# Save
model.save('oral_cancer_model')
```

## 🎨 Kustomisasi Tampilan

Ubah warna di CSS:

```css
:root {
    --primary: #0ea5e9;      /* Warna utama */
    --accent: #06b6d4;       /* Warna aksen */
    --success: #10b981;      /* Warna sukses */
    --danger: #ef4444;       /* Warna bahaya */
}
```

## ⚠️ Disclaimer

Aplikasi ini hanya untuk tujuan edukasi dan skrining awal. Hasil analisis BUKAN merupakan diagnosis medis resmi. Selalu konsultasikan dengan dokter atau profesional kesehatan untuk diagnosis yang akurat.

## 📝 License

MIT License - Silakan gunakan untuk tujuan edukasi dan pengembangan.

## 🤝 Kontribusi

Pull requests are welcome! Untuk perubahan besar, silakan buka issue terlebih dahulu.

## 📧 Kontak

Untuk pertanyaan atau saran, silakan buat issue di repository ini.

---

**Dibuat dengan ❤️ menggunakan TensorFlow.js / ONNX Runtime Web**
