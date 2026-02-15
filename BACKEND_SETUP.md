# 🔧 Panduan Setup Backend untuk Auto-Save ke Google Drive Owner

## Overview

Sistem ini menggunakan **Service Account** sehingga semua gambar otomatis tersimpan ke **Google Drive Anda**, bukan Drive user. User tidak perlu login Google sama sekali!

## 📋 Arsitektur

```
User Browser (GitHub Pages)
    ↓ Upload gambar via API
Backend Server (Vercel/Railway/Render)
    ↓ Service Account Auth
Google Drive (Folder Anda)
```

---

## 🚀 Setup Step-by-Step

### Part 1: Google Cloud Setup (10 menit)

#### Step 1: Create Service Account

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Pilih atau buat project baru: `Oral Cancer Detection`
3. **Enable Google Drive API**:
   - Menu ☰ → APIs & Services → Library
   - Search: "Google Drive API"
   - Click **ENABLE**

4. **Create Service Account**:
   - Menu ☰ → IAM & Admin → Service Accounts
   - Click **+ CREATE SERVICE ACCOUNT**
   - Service account name: `oral-cancer-uploader`
   - Description: `Service account for uploading images to Drive`
   - Click **CREATE AND CONTINUE**
   - Role: Pilih **Basic → Editor** (atau skip, kita set manual di Drive)
   - Click **DONE**

5. **Generate Key**:
   - Click service account yang baru dibuat
   - Tab **KEYS** → **ADD KEY** → **Create new key**
   - Type: **JSON**
   - Click **CREATE**
   - File `service-account-key.json` akan terdownload
   - **SIMPAN FILE INI DENGAN AMAN!**

6. **Copy Service Account Email**:
   - Di halaman service account, copy emailnya
   - Format: `oral-cancer-uploader@project-id.iam.gserviceaccount.com`

#### Step 2: Setup Google Drive Folder

1. Buka [Google Drive](https://drive.google.com/)
2. Buat folder baru: `OralCancerDetection_TrainingData`
3. **Klik kanan folder → Share**
4. **Tambahkan service account email** yang tadi dicopy
5. Permission: **Editor**
6. **Uncheck** "Notify people"
7. Click **Share**

✅ Sekarang service account punya akses ke folder ini!

---

### Part 2: Deploy Backend

Pilih salah satu platform (Vercel paling mudah):

#### Option A: Deploy ke Vercel (Recommended - Gratis)

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Prepare files**:
```bash
cd backend/
# Copy service-account-key.json ke folder ini
cp ~/Downloads/service-account-key.json .
```

3. **Deploy**:
```bash
vercel
```

Follow prompts:
- Set up and deploy? **Y**
- Which scope? (pilih account Anda)
- Link to existing project? **N**
- Project name? `oral-cancer-api`
- In which directory is your code? **./backend**
- Want to override settings? **N**

4. **Set Environment Variable** (Important untuk security):
```bash
# Upload service account key as secret
vercel secrets add oral-cancer-service-account "$(cat service-account-key.json)"
```

5. **Create vercel.json** (sudah ada):
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "SERVICE_ACCOUNT_KEY": "@oral-cancer-service-account"
  }
}
```

6. **Deploy ulang**:
```bash
vercel --prod
```

7. **Copy URL** yang diberikan, contoh:
```
https://oral-cancer-api.vercel.app
```

#### Option B: Deploy ke Railway (Gratis)

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
```

2. **Login**:
```bash
railway login
```

3. **Init project**:
```bash
cd backend/
railway init
```

4. **Add service account as variable**:
```bash
railway variables set SERVICE_ACCOUNT_KEY="$(cat service-account-key.json)"
```

5. **Deploy**:
```bash
railway up
```

6. **Get URL**:
```bash
railway open
```

Copy URL dari browser, contoh: `https://oral-cancer-api.railway.app`

#### Option C: Deploy ke Render (Gratis)

1. Buka [render.com](https://render.com/)
2. Sign up/Login
3. **New → Web Service**
4. Connect GitHub repository atau upload folder
5. Settings:
   - Name: `oral-cancer-api`
   - Environment: **Python**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. **Environment Variables**:
   - Key: `SERVICE_ACCOUNT_KEY`
   - Value: (paste isi file service-account-key.json)
7. **Create Web Service**
8. Copy URL: `https://oral-cancer-api.onrender.com`

---

### Part 3: Update Frontend

1. **Edit `index-final.html`** line ~13:
```javascript
// BEFORE:
const BACKEND_API_URL = 'https://your-backend-api.vercel.app';

// AFTER:
const BACKEND_API_URL = 'https://oral-cancer-api.vercel.app';  // URL backend Anda
```

2. **Deploy ke GitHub Pages**:
```bash
# Rename file
mv index-final.html index.html

git add index.html
git commit -m "Add backend auto-save integration"
git push origin main
```

---

## ✅ Testing

### Test Backend

```bash
# Health check
curl https://oral-cancer-api.vercel.app/health

# Should return:
# {
#   "status": "healthy",
#   "service": "oral-cancer-drive-uploader",
#   "drive_connected": true
# }
```

### Test Upload

```bash
# Test upload (ganti IMAGE_BASE64 dengan base64 image)
curl -X POST https://oral-cancer-api.vercel.app/upload \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "prediction": {
      "probability": 0.75,
      "classification": "Abnormal",
      "confidence": 0.85,
      "severity": "Tinggi"
    }
  }'
```

### Test Frontend

1. Buka GitHub Pages URL
2. Upload gambar
3. Tunggu notifikasi "✓ Gambar tersimpan"
4. Check Google Drive folder - gambar harus ada!

---

## 📊 Monitoring & Maintenance

### View Stats

```bash
# Get statistics
curl https://oral-cancer-api.vercel.app/stats
```

Response:
```json
{
  "success": true,
  "total_images": 150,
  "cancer_predictions": 45,
  "normal_predictions": 105,
  "folder_id": "1abc..."
}
```

### Check Logs

**Vercel:**
```bash
vercel logs
```

**Railway:**
```bash
railway logs
```

**Render:**
- Dashboard → Logs tab

### Rate Limits

Google Drive API limits:
- **1,000 requests per 100 seconds per user**
- Untuk production, consider caching atau batching

---

## 🔒 Security Best Practices

### 1. Jangan Commit Service Account Key!

```bash
# Add to .gitignore
echo "service-account-key.json" >> .gitignore
echo "*.json" >> .gitignore  # Except package.json, vercel.json, etc
```

### 2. Use Environment Variables

Always store service account key as environment variable, never hardcode!

### 3. Enable CORS Properly

Di `app.py`, restrict origins:
```python
CORS(app, origins=[
    "https://username.github.io",
    "http://localhost:8000"  # for testing
])
```

### 4. Add Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/upload', methods=['POST'])
@limiter.limit("20 per minute")
def upload_image():
    # ...
```

### 5. Input Validation

```python
# Validate image size
MAX_SIZE = 5 * 1024 * 1024  # 5MB

# Validate image format
ALLOWED_FORMATS = ['image/jpeg', 'image/png']
```

---

## 🐛 Troubleshooting

### Error: "Service account key not found"

**Problem:** File tidak ada atau path salah

**Solution:**
```bash
# Vercel
vercel secrets add oral-cancer-service-account "$(cat service-account-key.json)"

# Railway
railway variables set SERVICE_ACCOUNT_KEY="$(cat service-account-key.json)"

# Render
# Copy-paste isi file ke environment variable di dashboard
```

### Error: "Permission denied"

**Problem:** Service account tidak punya akses ke folder

**Solution:**
1. Buka Google Drive folder
2. Share dengan service account email
3. Set permission ke "Editor"

### Error: "CORS blocked"

**Problem:** Frontend tidak bisa akses backend

**Solution:**
```python
# app.py
CORS(app, origins=["https://your-username.github.io"])
```

### Upload Slow

**Problem:** Gambar terlalu besar

**Solution:**
```javascript
// Compress image sebelum upload
function compressImage(base64, quality = 0.7) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            
            resolve(canvas.toDataURL('image/jpeg', quality));
        };
        img.src = base64;
    });
}
```

### Backend Timeout

**Problem:** Cold start lambuh

**Solution:**
- Vercel: Keep-alive ping every 5 minutes
- Railway: Upgrade plan (free tier sleeps)
- Render: Upgrade to paid plan (free tier sleeps after 15 min)

---

## 💰 Cost Estimate

### Free Tier Limits:

**Vercel:**
- ✅ 100GB bandwidth/month
- ✅ 100 deployments/day
- ✅ Unlimited requests

**Railway:**
- ✅ $5 free credit/month
- ✅ ~500 hours runtime/month

**Render:**
- ✅ 750 hours/month free
- ⚠️ Sleeps after 15 min inactivity

**Google Drive:**
- ✅ 15GB free storage
- ✅ 1,000 requests/100sec

**Estimate Usage:**
- 1,000 uploads/month = ~100MB storage
- Free tier cukup untuk ~10,000 images/month!

---

## 📈 Scaling

Jika traffic tinggi:

1. **Batch Uploads:**
```javascript
// Queue uploads
const uploadQueue = [];

async function queueUpload(image) {
    uploadQueue.push(image);
    
    if (uploadQueue.length >= 10) {
        await batchUpload(uploadQueue);
        uploadQueue.length = 0;
    }
}
```

2. **Use CDN:**
- Cloudflare for caching
- Edge functions for low latency

3. **Database Tracking:**
- Add PostgreSQL/MongoDB
- Track uploads, predictions, stats

4. **Monitoring:**
- Sentry for error tracking
- LogRocket for user sessions

---

## 🎯 Next Steps

1. ✅ Setup Service Account
2. ✅ Deploy Backend
3. ✅ Update Frontend
4. ✅ Test End-to-End
5. 📊 Monitor Usage
6. 🔄 Setup Auto-download Script (use `download_from_drive.py`)
7. 🤖 Re-train Model Periodic
8. 📈 Track Accuracy Improvements

---

## 📚 Resources

- [Google Drive API Docs](https://developers.google.com/drive/api/guides/about-sdk)
- [Service Account Auth](https://cloud.google.com/iam/docs/service-accounts)
- [Vercel Python Docs](https://vercel.com/docs/functions/runtimes/python)
- [Flask CORS](https://flask-cors.readthedocs.io/)

---

**Setup Complete! 🎉 Gambar sekarang otomatis tersimpan ke Drive Anda tanpa user perlu login!**
