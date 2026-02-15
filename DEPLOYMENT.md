# 🚀 Panduan Deploy ke GitHub Pages

## Langkah-langkah Lengkap

### 1️⃣ Persiapan Model dari Kaggle

#### Download Dataset
```bash
# Install Kaggle CLI
pip install kaggle

# Setup API token (download dari kaggle.com/account)
mkdir ~/.kaggle
mv kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download dataset (contoh)
kaggle datasets download -d ashenafifasilkebede/dataset
unzip dataset.zip -d data/
```

#### Training Model
```bash
# Install dependencies
pip install tensorflow tensorflowjs tf2onnx onnx

# Run training script
python train_model.py
```

Ini akan menghasilkan:
- `oral_cancer_model.tflite` (model ringan, ~5-10MB)
- `best_model.h5` (model keras original)

#### Optimize Model untuk Web
```bash
# PILIHAN 1: Quantize TFLite (paling ringan)
python -c "
import tensorflow as tf
converter = tf.lite.TFLiteConverter.from_keras_model(tf.keras.models.load_model('best_model.h5'))
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_types = [tf.float16]
tflite_quant_model = converter.convert()
with open('model_quantized.tflite', 'wb') as f:
    f.write(tflite_quant_model)
"

# PILIHAN 2: Convert ke ONNX (alternatif ringan)
python -c "
import tf2onnx
import onnx

spec = (tf.TensorSpec((None, 224, 224, 3), tf.float32, name='input'),)
model_proto, _ = tf2onnx.convert.from_keras(
    'best_model.h5',
    input_signature=spec,
    opset=13
)
onnx.save(model_proto, 'model.onnx')

# Quantize ONNX
from onnxruntime.quantization import quantize_dynamic, QuantType
quantize_dynamic('model.onnx', 'model_quantized.onnx', weight_type=QuantType.QUInt8)
"
```

### 2️⃣ Setup Repository GitHub

```bash
# Initialize git
git init

# Create repository di GitHub.com
# Kemudian:
git remote add origin https://github.com/USERNAME/oral-cancer-detection.git

# Add files
git add index.html README.md model_quantized.tflite
# ATAU gunakan model ONNX:
# git add index.html README.md model_quantized.onnx

git commit -m "Initial commit: Oral cancer detection app"
git branch -M main
git push -u origin main
```

### 3️⃣ Aktifkan GitHub Pages

1. Buka repository di GitHub
2. Klik **Settings** → **Pages**
3. Source: pilih **main** branch dan **/ (root)**
4. Klik **Save**
5. Tunggu 1-2 menit
6. Website akan tersedia di: `https://USERNAME.github.io/oral-cancer-detection/`

### 4️⃣ Verifikasi Deployment

Buka URL GitHub Pages Anda dan cek:
- ✅ Halaman loading dengan benar
- ✅ Model terload (cek console browser)
- ✅ Upload gambar berfungsi
- ✅ Analisis menghasilkan prediksi

## 📊 Perbandingan Format Model

| Format | Ukuran | Load Time | Browser Support | Rekomendasi |
|--------|--------|-----------|-----------------|-------------|
| TFLite (quantized) | 2-5 MB | Cepat | Chrome, Safari, Firefox | ⭐⭐⭐⭐⭐ Terbaik |
| ONNX (quantized) | 3-7 MB | Cepat | Semua browser modern | ⭐⭐⭐⭐⭐ Alternatif terbaik |
| TensorFlow.js | 10-30 MB | Lambat | Semua browser | ⭐⭐⭐ Kurang direkomendasikan |

## 🔧 Troubleshooting

### Model Tidak Loading

**Problem:** Console error "Failed to load model"

**Solution:**
```javascript
// Cek path model
// Jika file di root: 'model_quantized.tflite'
// Jika di folder: 'models/model_quantized.tflite'

// Pastikan file ter-commit ke GitHub
git add model_quantized.tflite
git commit -m "Add model file"
git push
```

### CORS Error

**Problem:** "CORS policy blocked"

**Solution:**
```html
<!-- Tambahkan meta tag di <head> -->
<meta http-equiv="Cross-Origin-Embedder-Policy" content="require-corp">
<meta http-equiv="Cross-Origin-Opener-Policy" content="same-origin">
```

Atau gunakan GitHub Pages settings → tambahkan custom headers

### Model Terlalu Besar

**Problem:** File >100MB tidak bisa di-push

**Solution:**
```bash
# Use Git LFS untuk file besar
git lfs install
git lfs track "*.tflite"
git add .gitattributes
git add model.tflite
git commit -m "Add model with LFS"
git push

# ATAU host model di tempat lain:
# - Hugging Face Hub (gratis)
# - Google Cloud Storage
# - AWS S3
# - Cloudflare R2
```

### Prediksi Tidak Akurat

**Problem:** Hasil prediksi aneh

**Solution:**
```javascript
// Cek preprocessing sesuai dengan training
// Pastikan normalisasi sama:

// Training pakai ImageNet normalization?
const mean = [0.485, 0.456, 0.406];
const std = [0.229, 0.224, 0.225];

// Training pakai simple /255?
const normalized = pixels / 255.0;

// Input size harus sama (224x224)
.resizeBilinear([224, 224])
```

## 🎯 Optimasi Performance

### 1. Lazy Loading Model
```javascript
// Load model hanya saat dibutuhkan
let modelPromise = null;

async function getModel() {
    if (!modelPromise) {
        modelPromise = detector.loadModel();
    }
    return modelPromise;
}

// Saat analyze
await getModel();
const result = await detector.predict(image);
```

### 2. Web Worker untuk Inferensi
```javascript
// Jalankan prediksi di background thread
const worker = new Worker('model-worker.js');

worker.postMessage({ image: imageData });
worker.onmessage = (e) => {
    const result = e.data;
    displayResults(result);
};
```

### 3. Progressive Loading
```javascript
// Load model secara bertahap
async function loadModelProgressive() {
    const response = await fetch('model.tflite');
    const reader = response.body.getReader();
    
    let receivedLength = 0;
    const chunks = [];
    
    while(true) {
        const {done, value} = await reader.read();
        if (done) break;
        
        chunks.push(value);
        receivedLength += value.length;
        
        // Update progress
        const progress = (receivedLength / response.headers.get('content-length')) * 100;
        updateLoadingBar(progress);
    }
    
    const blob = new Blob(chunks);
    return blob;
}
```

## 📱 Mobile Optimization

### Service Worker untuk Offline
```javascript
// sw.js
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('oral-cancer-v1').then((cache) => {
            return cache.addAll([
                '/',
                '/index.html',
                '/model_quantized.tflite'
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});
```

### Responsive Images
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">

<!-- Gunakan srcset untuk different screens -->
<img srcset="logo-1x.png 1x, logo-2x.png 2x" alt="Logo">
```

## 🔒 Security Best Practices

### 1. Input Validation
```javascript
function validateImage(file) {
    // Check file type
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
        throw new Error('Invalid file type');
    }
    
    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        throw new Error('File too large');
    }
    
    return true;
}
```

### 2. Content Security Policy
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; 
               style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
               font-src https://fonts.gstatic.com;">
```

## 📈 Analytics & Monitoring

### Google Analytics
```html
<!-- Add to <head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Error Tracking
```javascript
window.addEventListener('error', (event) => {
    // Log to analytics
    gtag('event', 'exception', {
        description: event.message,
        fatal: false
    });
});
```

## 🌐 Custom Domain (Optional)

### Setup Custom Domain
1. Beli domain (Namecheap, GoDaddy, dll)
2. GitHub Settings → Pages → Custom domain
3. Masukkan domain Anda (contoh: oralcancer.ai)
4. Di DNS provider, tambahkan records:

```
Type: A
Name: @
Value: 185.199.108.153

Type: A  
Name: @
Value: 185.199.109.153

Type: CNAME
Name: www
Value: USERNAME.github.io
```

5. Tunggu propagasi DNS (1-48 jam)
6. Enable HTTPS di GitHub Pages

## ✅ Checklist Deploy

- [ ] Model sudah di-train dan di-optimize
- [ ] File model <25MB (atau gunakan Git LFS)
- [ ] Testing lokal berhasil
- [ ] index.html sudah di-update dengan model path yang benar
- [ ] README.md lengkap dengan instruksi
- [ ] .gitignore sudah di-setup
- [ ] Repository di-push ke GitHub
- [ ] GitHub Pages sudah aktif
- [ ] Website bisa diakses
- [ ] Model berhasil loading di browser
- [ ] Upload gambar berfungsi
- [ ] Prediksi menghasilkan output yang benar
- [ ] Mobile responsive
- [ ] Disclaimer medical sudah ada

## 🎉 Next Steps

Setelah deploy berhasil:

1. **Testing dengan berbagai gambar**
   - Test dengan gambar normal
   - Test dengan gambar abnormal
   - Validasi akurasi

2. **Improve Model**
   - Kumpulkan feedback
   - Re-train dengan data baru
   - Update model di repository

3. **Add Features**
   - History prediksi
   - Export hasil PDF
   - Multi-language support
   - Batch processing

4. **Marketing**
   - Share di social media
   - Submit ke showcases
   - Tulis blog post

## 📞 Support

Jika ada masalah:
1. Check browser console untuk error
2. Verify model file ada di repository
3. Test di different browsers
4. Check GitHub Actions untuk build errors

---

**Happy Deploying! 🚀**
