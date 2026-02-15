"""
Script untuk download dan organize gambar dari Google Drive
untuk keperluan re-training model

Install dependencies:
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pillow
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json
from datetime import datetime
import shutil
from PIL import Image

# Scopes untuk akses Drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

class DriveDataDownloader:
    def __init__(self, folder_name='OralCancerDetection_TrainingData'):
        self.folder_name = folder_name
        self.service = None
        self.folder_id = None
        
    def authenticate(self):
        """
        Authenticate dengan Google Drive API
        """
        creds = None
        
        # Token disimpan di file token.json setelah first run
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # Jika tidak ada valid credentials, login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials untuk next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        print("✓ Authentication successful!")
        
    def find_folder(self):
        """
        Cari folder training data di Drive
        """
        try:
            results = self.service.files().list(
                q=f"name='{self.folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)').execute()
            
            files = results.get('files', [])
            
            if not files:
                print(f"✗ Folder '{self.folder_name}' tidak ditemukan di Drive!")
                return False
            
            self.folder_id = files[0]['id']
            print(f"✓ Folder ditemukan: {files[0]['name']} (ID: {self.folder_id})")
            return True
            
        except Exception as error:
            print(f'✗ Error finding folder: {error}')
            return False
    
    def list_images(self):
        """
        List semua gambar dalam folder
        """
        try:
            results = self.service.files().list(
                q=f"'{self.folder_id}' in parents and mimeType contains 'image/' and trashed=false",
                spaces='drive',
                fields='files(id, name, description, createdTime, size)',
                pageSize=1000).execute()
            
            files = results.get('files', [])
            print(f"\n✓ Ditemukan {len(files)} gambar")
            return files
            
        except Exception as error:
            print(f'✗ Error listing files: {error}')
            return []
    
    def download_image(self, file_id, file_name, output_dir):
        """
        Download single image
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Save file
            filepath = os.path.join(output_dir, file_name)
            with open(filepath, 'wb') as f:
                f.write(fh.getvalue())
            
            return True
            
        except Exception as error:
            print(f'✗ Error downloading {file_name}: {error}')
            return False
    
    def parse_filename(self, filename):
        """
        Parse filename untuk extract prediction percentage
        Format: oral_cancer_2024-02-15T10-30-00_75pct.jpg
        """
        try:
            parts = filename.split('_')
            if len(parts) >= 4 and 'pct' in parts[-1]:
                percentage_str = parts[-1].replace('pct.jpg', '').replace('pct.png', '')
                percentage = int(percentage_str)
                return percentage
        except:
            pass
        return None
    
    def organize_dataset(self, source_dir, threshold=50):
        """
        Organize images ke folder normal/cancer berdasarkan prediction
        """
        print(f"\n📁 Organizing dataset (threshold: {threshold}%)...")
        
        normal_dir = os.path.join(source_dir, 'normal')
        cancer_dir = os.path.join(source_dir, 'cancer')
        uncertain_dir = os.path.join(source_dir, 'uncertain')
        
        os.makedirs(normal_dir, exist_ok=True)
        os.makedirs(cancer_dir, exist_ok=True)
        os.makedirs(uncertain_dir, exist_ok=True)
        
        stats = {'normal': 0, 'cancer': 0, 'uncertain': 0}
        
        for filename in os.listdir(source_dir):
            if not (filename.endswith('.jpg') or filename.endswith('.png')):
                continue
            
            filepath = os.path.join(source_dir, filename)
            
            # Parse prediction dari filename
            percentage = self.parse_filename(filename)
            
            if percentage is None:
                # Tidak bisa parse, masuk uncertain
                shutil.move(filepath, os.path.join(uncertain_dir, filename))
                stats['uncertain'] += 1
            elif percentage > threshold + 20:  # >70% = definitely cancer
                shutil.move(filepath, os.path.join(cancer_dir, filename))
                stats['cancer'] += 1
            elif percentage < threshold - 20:  # <30% = definitely normal
                shutil.move(filepath, os.path.join(normal_dir, filename))
                stats['normal'] += 1
            else:  # 30-70% = uncertain
                shutil.move(filepath, os.path.join(uncertain_dir, filename))
                stats['uncertain'] += 1
        
        print("\n" + "="*50)
        print("📊 Dataset Organization Complete!")
        print("="*50)
        print(f"Normal images:    {stats['normal']}")
        print(f"Cancer images:    {stats['cancer']}")
        print(f"Uncertain images: {stats['uncertain']}")
        print(f"Total:            {sum(stats.values())}")
        print("="*50)
        
        return stats
    
    def create_manifest(self, files, output_file='manifest.json'):
        """
        Create manifest file dengan metadata semua images
        """
        manifest = []
        
        for file in files:
            percentage = self.parse_filename(file['name'])
            
            manifest.append({
                'filename': file['name'],
                'file_id': file['id'],
                'created_time': file.get('createdTime'),
                'size_bytes': file.get('size'),
                'description': file.get('description', ''),
                'prediction_percentage': percentage,
                'classification': 'cancer' if percentage and percentage > 50 else 'normal' if percentage else 'unknown'
            })
        
        with open(output_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\n✓ Manifest created: {output_file}")
    
    def validate_images(self, directory):
        """
        Validate downloaded images (check corrupt files)
        """
        print(f"\n🔍 Validating images in {directory}...")
        
        corrupt_files = []
        valid_count = 0
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if not (filename.endswith('.jpg') or filename.endswith('.png')):
                    continue
                
                filepath = os.path.join(root, filename)
                
                try:
                    img = Image.open(filepath)
                    img.verify()  # Verify it's actually an image
                    valid_count += 1
                except Exception as e:
                    print(f"✗ Corrupt file: {filename}")
                    corrupt_files.append(filepath)
        
        print(f"✓ Valid images: {valid_count}")
        
        if corrupt_files:
            print(f"✗ Corrupt images: {len(corrupt_files)}")
            # Remove corrupt files
            for filepath in corrupt_files:
                os.remove(filepath)
                print(f"  Removed: {filepath}")
        
        return valid_count, len(corrupt_files)
    
    def download_all(self, output_dir='downloaded_dataset'):
        """
        Download semua gambar dari Drive
        """
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Authenticate
        print("🔐 Authenticating with Google Drive...")
        self.authenticate()
        
        # Find folder
        print(f"\n📁 Looking for folder '{self.folder_name}'...")
        if not self.find_folder():
            return
        
        # List images
        print("\n📋 Listing images...")
        files = self.list_images()
        
        if not files:
            print("No images found!")
            return
        
        # Create manifest
        self.create_manifest(files, os.path.join(output_dir, 'manifest.json'))
        
        # Download images
        print(f"\n⬇️  Downloading {len(files)} images...")
        print("="*50)
        
        success_count = 0
        for i, file in enumerate(files, 1):
            print(f"[{i}/{len(files)}] {file['name']}...", end=' ')
            
            if self.download_image(file['id'], file['name'], output_dir):
                print("✓")
                success_count += 1
            else:
                print("✗")
        
        print("="*50)
        print(f"✓ Downloaded: {success_count}/{len(files)} images")
        
        # Validate images
        self.validate_images(output_dir)
        
        # Organize dataset
        print("\n" + "="*50)
        organize = input("Organize dataset into normal/cancer folders? (y/n): ")
        if organize.lower() == 'y':
            self.organize_dataset(output_dir)
        
        print("\n" + "="*50)
        print("✨ Download Complete!")
        print("="*50)
        print(f"📁 Dataset location: {os.path.abspath(output_dir)}")
        print(f"📄 Manifest: {os.path.join(output_dir, 'manifest.json')}")
        print("="*50)


def main():
    """
    Main function
    """
    print("="*60)
    print("🦷 Oral Cancer Detection - Drive Data Downloader")
    print("="*60)
    
    # Configuration
    folder_name = input("\nFolder name (default: OralCancerDetection_TrainingData): ").strip()
    if not folder_name:
        folder_name = 'OralCancerDetection_TrainingData'
    
    output_dir = input("Output directory (default: downloaded_dataset): ").strip()
    if not output_dir:
        output_dir = 'downloaded_dataset'
    
    # Create downloader
    downloader = DriveDataDownloader(folder_name)
    
    # Download
    downloader.download_all(output_dir)


if __name__ == '__main__':
    # Check credentials file
    if not os.path.exists('credentials.json'):
        print("\n" + "="*60)
        print("⚠️  ERROR: credentials.json not found!")
        print("="*60)
        print("\nSteps to get credentials.json:")
        print("1. Go to Google Cloud Console")
        print("2. Create OAuth 2.0 Client ID (Desktop app)")
        print("3. Download JSON file")
        print("4. Rename to 'credentials.json'")
        print("5. Place in same directory as this script")
        print("\nSee GOOGLE_DRIVE_SETUP.md for detailed instructions")
        print("="*60)
    else:
        main()
