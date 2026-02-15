# 🔗 Panduan Setup Google Drive Integration

## Overview

Fitur ini akan otomatis menyimpan setiap gambar yang diupload ke folder Google Drive Anda, lengkap dengan hasil prediksi. Ini sangat berguna untuk:
- 📊 Mengumpulkan dataset training tambahan
- 📈 Meningkatkan akurasi model di masa depan
- 🔍 Analisis dan review hasil prediksi
- 📁 Organisasi data terstruktur

## 🚀 Langkah Setup (5-10 menit)

### Step 1: Buat Google Cloud Project

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Klik **Select a project** → **NEW PROJECT**
3. Nama project: `Oral Cancer Detection`
4. Klik **CREATE**
5. Tunggu beberapa detik hingga project dibuat

### Step 2: Enable Google Drive API

1. Di Cloud Console, pastikan project yang baru dibuat sudah dipilih
2. Klik menu ☰ → **APIs & Services** → **Library**
3. Search: `Google Drive API`
4. Klik **Google Drive API**
5. Klik **ENABLE**

### Step 3: Create API Key

1. Klik menu ☰ → **APIs & Services** → **Credentials**
2. Klik **+ CREATE CREDENTIALS** → **API key**
3. API key akan dibuat otomatis
4. **COPY** API key ini (contoh: `AIzaSyC...`)
5. Klik **RESTRICT KEY** (recommended untuk keamanan)
6. Di **API restrictions**:
   - Pilih **Restrict key**
   - Centang **Google Drive API**
   - Klik **Save**

### Step 4: Create OAuth 2.0 Client ID

1. Masih di **Credentials** page
2. Klik **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Jika muncul consent screen warning:
   - Klik **CONFIGURE CONSENT SCREEN**
   - Pilih **External** → **CREATE**
   - App name: `Oral Cancer Detection`
   - User support email: (email Anda)
   - Developer contact: (email Anda)
   - Klik **SAVE AND CONTINUE**
   - Skip Scopes → **SAVE AND CONTINUE**
   - Skip Test users → **SAVE AND CONTINUE**
   - Klik **BACK TO DASHBOARD**

4. Kembali ke **Credentials** → **+ CREATE CREDENTIALS** → **OAuth client ID**
5. Application type: **Web application**
6. Name: `Oral Cancer Web App`
7. **Authorized JavaScript origins**:
   - Klik **+ ADD URI**
   - Tambahkan: `https://USERNAME.github.io`
   - Jika testing lokal, tambahkan juga: `http://localhost:8000`
   
8. **Authorized redirect URIs**:
   - Klik **+ ADD URI**
   - Tambahkan: `https://USERNAME.github.io/oral-cancer-detection`
   - Jika testing lokal: `http://localhost:8000`

9. Klik **CREATE**
10. **COPY** Client ID (contoh: `123456789-abc...apps.googleusercontent.com`)

### Step 5: Update Code

Buka file `index-with-drive.html` dan ganti:

```javascript
// BARIS 350-351
const CLIENT_ID = 'YOUR_CLIENT_ID_HERE.apps.googleusercontent.com';
const API_KEY = 'YOUR_API_KEY_HERE';
```

Dengan:

```javascript
const CLIENT_ID = '123456789-abc...apps.googleusercontent.com';  // Client ID Anda
const API_KEY = 'AIzaSyC...';  // API Key Anda
```

### Step 6: Testing Lokal

```bash
# Jalankan local server
python -m http.server 8000
# Atau
python3 -m http.server 8000
# Atau gunakan Live Server extension di VS Code
```

Buka: `http://localhost:8000/index-with-drive.html`

### Step 7: Deploy ke GitHub Pages

```bash
# Rename file
mv index-with-drive.html index.html

# Commit and push
git add index.html
git commit -m "Add Google Drive integration"
git push origin main
```

Tunggu 1-2 menit, kemudian buka GitHub Pages URL Anda.

## 🔐 Keamanan & Privacy

### ⚠️ IMPORTANT: Jangan Commit Credentials!

**JANGAN** commit API key dan Client ID ke public repository jika sensitif. Sebagai gantinya:

#### Option 1: Environment Variables (Recommended untuk production)

```javascript
// Gunakan environment variables
const CLIENT_ID = process.env.GOOGLE_CLIENT_ID || 'fallback-dev-client-id';
const API_KEY = process.env.GOOGLE_API_KEY || 'fallback-dev-api-key';
```

Kemudian set di GitHub:
1. Settings → Secrets and variables → Actions
2. Add: `GOOGLE_CLIENT_ID` dan `GOOGLE_API_KEY`

#### Option 2: Restrict API Key

Di Google Cloud Console → Credentials → Edit API Key:

1. **Application restrictions**:
   - HTTP referrers
   - Add: `https://USERNAME.github.io/*`

2. **API restrictions**:
   - Restrict key
   - Select: Google Drive API only

### 🔒 OAuth Consent Screen Settings

Untuk production app:

1. Google Cloud Console → **OAuth consent screen**
2. **Publishing status**: Click **PUBLISH APP**
3. Verification may be required for full production use
4. For personal/testing use, "Testing" mode is sufficient (max 100 users)

## 📁 Struktur Folder di Google Drive

App akan otomatis membuat struktur folder:

```
Google Drive/
└── OralCancerDetection_TrainingData/
    ├── oral_cancer_2024-02-15T10-30-00_75pct.jpg
    ├── oral_cancer_2024-02-15T10-35-00_25pct.jpg
    ├── oral_cancer_2024-02-15T10-40-00_85pct.jpg
    └── ...
```

Setiap file berisi:
- **Filename**: timestamp + prediction percentage
- **Description**: Full prediction details (probability, classification)

## 🔧 Advanced Configuration

### Custom Folder Name

```javascript
// LINE ~410
const folderName = 'OralCancerDetection_TrainingData';

// Ganti dengan nama custom:
const folderName = 'MyCustomFolderName';
```

### Organize by Date

```javascript
async function createDriveFolder() {
    const date = new Date().toISOString().split('T')[0]; // 2024-02-15
    const folderName = `OralCancer_${date}`;
    
    // ... rest of code
}
```

### Add Metadata

```javascript
const metadata = {
    name: fileName,
    mimeType: file.type,
    parents: [driveFolderId],
    description: predictionResult ? 
        `Prediction: ${(predictionResult.probability * 100).toFixed(2)}%
         Classification: ${predictionResult.features.abnormality ? 'Abnormal' : 'Normal'}
         Confidence: ${(predictionResult.confidence * 100).toFixed(2)}%
         Timestamp: ${new Date().toISOString()}
         Severity: ${predictionResult.features.severity}` :
        'Oral cancer detection image',
    properties: {
        'app': 'OralCancerDetection',
        'version': '1.0',
        'prediction': predictionResult ? String(predictionResult.probability) : 'unknown'
    }
};
```

### Disable Auto-Save

Jika Anda ingin user memilih manual:

```html
<!-- LINE ~260 -->
<input type="checkbox" id="saveToDriveCheckbox" checked>

<!-- Ganti jadi unchecked by default: -->
<input type="checkbox" id="saveToDriveCheckbox">
```

## 📊 Menggunakan Data untuk Re-Training

### Download Data dari Drive

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

# Setup credentials
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service-account-key.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

service = build('drive', 'v3', credentials=credentials)

# Get folder ID
results = service.files().list(
    q="name='OralCancerDetection_TrainingData' and mimeType='application/vnd.google-apps.folder'",
    fields="files(id, name)").execute()

folder_id = results['files'][0]['id']

# List all images in folder
results = service.files().list(
    q=f"'{folder_id}' in parents and mimeType contains 'image/'",
    fields="files(id, name, description)").execute()

# Download images
for file in results['files']:
    request = service.files().get_media(fileId=file['id'])
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
    
    # Save file
    with open(f"dataset/{file['name']}", 'wb') as f:
        f.write(fh.getvalue())
    
    print(f"Downloaded: {file['name']}")
```

### Organize for Training

```python
import os
import shutil
import json

# Parse filename to extract prediction
def parse_filename(filename):
    # oral_cancer_2024-02-15T10-30-00_75pct.jpg
    parts = filename.split('_')
    if len(parts) >= 4 and 'pct' in parts[-1]:
        percentage = int(parts[-1].replace('pct.jpg', ''))
        return percentage
    return None

# Organize into folders
os.makedirs('dataset/normal', exist_ok=True)
os.makedirs('dataset/cancer', exist_ok=True)

for filename in os.listdir('dataset'):
    if filename.endswith('.jpg'):
        percentage = parse_filename(filename)
        
        if percentage is not None:
            if percentage > 50:
                # High probability = cancer
                shutil.move(f'dataset/{filename}', f'dataset/cancer/{filename}')
            else:
                # Low probability = normal
                shutil.move(f'dataset/{filename}', f'dataset/normal/{filename}')

print("Dataset organized!")
print(f"Normal images: {len(os.listdir('dataset/normal'))}")
print(f"Cancer images: {len(os.listdir('dataset/cancer'))}")
```

### Re-train Model

```python
# Use the organized dataset
train_generator = train_datagen.flow_from_directory(
    'dataset/',
    target_size=(224, 224),
    batch_size=32,
    class_mode='binary'
)

# Train with new data
model.fit(train_generator, epochs=10)
model.save('oral_cancer_model_v2.h5')
```

## 🐛 Troubleshooting

### Error: "popup_closed_by_user"
**Problem**: User menutup popup sebelum login
**Solution**: Normal behavior, user harus click "Connect" lagi

### Error: "invalid_grant"
**Problem**: Token expired atau invalid
**Solution**: 
```javascript
// Clear token and re-authenticate
gapi.client.setToken(null);
handleAuthClick();
```

### Error: "Not Found" saat upload
**Problem**: Folder ID tidak valid
**Solution**:
```javascript
// Reset folder ID
driveFolderId = null;
await createDriveFolder();
```

### Upload Success tapi File Tidak Muncul
**Problem**: Mungkin berada di folder lain
**Solution**:
1. Buka Google Drive
2. Search: `type:image source:app-name`
3. Check folder yang dibuat aplikasi

### CORS Error
**Problem**: Request blocked oleh browser
**Solution**: Pastikan origin sudah ditambahkan di OAuth credentials

### Rate Limit Error
**Problem**: Terlalu banyak request
**Solution**: 
- Google Drive API: 1000 requests per 100 seconds per user
- Implement retry logic:

```javascript
async function uploadWithRetry(file, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await uploadToDrive(file);
        } catch (error) {
            if (error.status === 429 && i < maxRetries - 1) {
                await new Promise(r => setTimeout(r, 2000 * (i + 1)));
                continue;
            }
            throw error;
        }
    }
}
```

## 📈 Monitoring Usage

### Check Quota

1. Google Cloud Console
2. APIs & Services → Dashboard
3. Click **Google Drive API**
4. View traffic and quota usage

### Set Alerts

1. Google Cloud Console → Monitoring
2. Create alert for API quota
3. Set threshold (e.g., 80% of quota)

## 🎯 Best Practices

1. **Always use HTTPS** in production
2. **Restrict API keys** to specific domains
3. **Implement error handling** for network failures
4. **Add user consent** before saving to Drive
5. **Compress images** before upload to save space
6. **Add metadata** for easier organization
7. **Implement batch upload** for multiple images
8. **Add progress indicators** for user feedback

## 💡 Tips

- Use Service Account untuk automated scripts
- Enable logging untuk debugging
- Implement offline queue untuk failed uploads
- Add retry mechanism untuk network issues
- Compress images sebelum upload (use canvas.toBlob with quality)
- Implement incremental backup strategy

## 📚 Resources

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth 2.0 for Web Apps](https://developers.google.com/identity/protocols/oauth2/javascript-implicit-flow)
- [API Key Best Practices](https://cloud.google.com/docs/authentication/api-keys)

---

**Setup selesai! 🎉 Data Anda sekarang otomatis tersimpan ke Google Drive untuk training model yang lebih baik!**
