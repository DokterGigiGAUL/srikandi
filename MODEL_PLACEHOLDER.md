# 📦 MODEL FILE PLACEHOLDER

## ⚠️ PENTING: Anda perlu menambahkan file model!

File `model.tflite` belum ada di folder ini. Aplikasi tidak akan berjalan tanpa file model.

## 📥 Cara Mendapatkan model.tflite:

### Opsi 1: Dari Google Colab
```python
# Di notebook Colab Anda, jalankan:
from google.colab import files
files.download('oral_cancer_model.tflite')
```

### Opsi 2: Dari Google Drive
1. Buka https://drive.google.com
2. Cari folder `oral-cancer-detection-bot`
3. Download file `oral_cancer_model.tflite` atau `model.tflite`

### Opsi 3: Dari Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Download file
railway run cat model.tflite > model.tflite
```

## 📍 Letakkan Model di Sini:

Setelah download, letakkan file di folder ini:

```
oral-cancer-webapp/
├── oral_cancer_webapp.py
├── requirements.txt
├── README.md
└── model.tflite          ← LETAKKAN DI SINI!
```

## ✅ Nama File Harus:
- `model.tflite` (ATAU)
- Edit line 53 di `oral_cancer_webapp.py` jika nama file berbeda:

```python
# Line 53
interpreter = tf.lite.Interpreter(model_path="NAMA_FILE_ANDA.tflite")
```

## 🔍 Cara Cek Apakah Model Sudah Benar:

```bash
# Cek ukuran file (seharusnya 2-3 MB)
ls -lh model.tflite

# Test load model
python -c "import tensorflow as tf; interpreter = tf.lite.Interpreter(model_path='model.tflite'); print('✅ Model OK!')"
```

## 🚀 Setelah Model Ada:

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run oral_cancer_webapp.py
```

---

💡 **Tips:** Simpan backup model di Google Drive untuk akses mudah di masa depan!
