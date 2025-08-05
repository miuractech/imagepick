#!/usr/bin/env python3
"""
Quick Upload Script for Single Folders using Supabase REST API
Simple script to upload a single folder without the full tracking system.
"""

import os
import json
import sys
import time
from datetime import datetime
from urllib import request, parse
import ssl
from config import DEVICE_ID, DEVICE_NAME, DEVICE_TYPE, SUPABASE_ANON_KEY

def upload_single_folder_rest(folder_path, supabase_url, supabase_key):
    """Upload a single folder to Supabase using REST API."""
    if not os.path.exists(folder_path):
        print(f"❌ Folder does not exist: {folder_path}")
        return False
    
    folder_name = os.path.basename(folder_path)
    print(f"📁 Uploading folder: {folder_name}")
    
    try:
        # Get all files in the folder
        files = os.listdir(folder_path)
        image_files = []
        stats_file = None
        
        for file in files:
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                    image_files.append(file)
                elif file.lower() == 'stats.json':
                    stats_file = file
        
        print(f"📸 Found {len(image_files)} image files")
        if stats_file:
            print(f"📊 Found stats.json file")
        
        # Upload images to Supabase Storage
        uploaded_image_urls = []
        for image_file in image_files:
            image_path = os.path.join(folder_path, image_file)
            # URL encode the filename for storage path
            encoded_filename = parse.quote(image_file)
            storage_path = f"images/{DEVICE_ID}/{folder_name}/{encoded_filename}"
            
            print(f"  📤 Uploading image: {image_file}")
            if upload_image_to_storage(image_path, storage_path, supabase_url, supabase_key):
                # Get public URL for the uploaded image (use encoded filename)
                image_url = f"{supabase_url.rstrip('/')}/storage/v1/object/public/images/{DEVICE_ID}/{folder_name}/{encoded_filename}"
                uploaded_image_urls.append(image_url)
                print(f"  ✅ Image uploaded: {image_url}")
            else:
                print(f"  ❌ Failed to upload image: {image_file}")
                # Still add the filename for reference
                uploaded_image_urls.append(image_file)
        
        # Read stats.json if exists
        stats_data = None
        if stats_file:
            try:
                with open(os.path.join(folder_path, stats_file), 'r') as f:
                    stats_data = json.load(f)
                print(f"✅ Loaded stats.json successfully")
            except Exception as e:
                print(f"❌ Error reading stats.json: {str(e)}")
                return False
        
        # Prepare data for database
        test_date = datetime.now()
        upload_batch = f"quick_batch_{int(time.time())}"
        
        # Determine test status
        test_status = "pending"
        if stats_data:
            if stats_data.get("result") and len(stats_data["result"]) > 0:
                test_status = "passed"
            else:
                test_status = "failed"
        
        print(f"🏷️  Test status: {test_status}")
        
        # Create metadata
        metadata = {
            "upload_timestamp": test_date.isoformat(),
            "total_images": len(image_files),
            "files_processed": files,
            "upload_method": "quick_upload_rest",
            "image_urls": uploaded_image_urls,
            "device_id": DEVICE_ID,
            "device_name": DEVICE_NAME,
            "device_type": DEVICE_TYPE
        }
        
        # Prepare data for insertion
        insert_data = {
            "folder_name": folder_name,
            "device_id": DEVICE_ID,
            "images": uploaded_image_urls,  # Use URLs instead of filenames
            "test_results": stats_data,
            "test_date": test_date.isoformat(),
            "test_status": test_status,
            "upload_batch": upload_batch,
            "metadata": metadata,
            "data_type": "image_analysis"
        }
        
        # Make REST API request
        url = f"{supabase_url.rstrip('/')}/rest/v1/device_test"
        
        headers = {
            'Content-Type': 'application/json',
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Prefer': 'return=minimal'
        }
        
        data_bytes = json.dumps(insert_data).encode('utf-8')
        
        req = request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method='POST'
        )
        
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        print("🚀 Executing REST API request...")
        
        with request.urlopen(req, context=context, timeout=30) as response:
            if response.status in [200, 201]:
                print(f"✅ Successfully uploaded folder: {folder_name}")
                
                # Create success.json
                success_data = {
                    "timestamp": test_date.isoformat(),
                    "folder": folder_name,
                    "status": "success",
                    "uploaded_files": image_files + ([stats_file] if stats_file else []),
                    "test_status": test_status,
                    "upload_batch": upload_batch,
                    "method": "rest_api",
                    "image_urls": uploaded_image_urls,
                    "device_id": DEVICE_ID,
                    "device_name": DEVICE_NAME,
                    "device_type": DEVICE_TYPE
                }
                
                success_file = os.path.join(folder_path, "success.json")
                with open(success_file, 'w') as f:
                    json.dump(success_data, f, indent=2)
                
                print(f"📄 Created success.json in {folder_name}")
                return True
            else:
                print(f"❌ HTTP Error {response.status}: {response.reason}")
                
                # Create failed.json
                failed_data = {
                    "timestamp": test_date.isoformat(),
                    "folder": folder_name,
                    "status": "failed",
                    "error": f"HTTP {response.status}: {response.reason}",
                    "upload_batch": upload_batch,
                    "method": "rest_api"
                }
                
                failed_file = os.path.join(folder_path, "failed.json")
                with open(failed_file, 'w') as f:
                    json.dump(failed_data, f, indent=2)
                
                print(f"📄 Created failed.json in {folder_name}")
                return False
                
    except Exception as e:
        print(f"❌ Error uploading folder {folder_name}: {str(e)}")
        
        # Create failed.json for exceptions
        failed_data = {
            "timestamp": datetime.now().isoformat(),
            "folder": folder_name,
            "status": "failed",
            "error": str(e),
            "method": "rest_api"
        }
        
        failed_file = os.path.join(folder_path, "failed.json")
        with open(failed_file, 'w') as f:
            json.dump(failed_data, f, indent=2)
        
        return False

def upload_image_to_storage(image_path: str, storage_path: str, supabase_url: str, supabase_key: str) -> bool:
    """Upload a single image file to Supabase Storage."""
    try:
        # Read the image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # Create storage bucket if it doesn't exist
        create_storage_bucket("images", supabase_url, supabase_key)
        
        # Upload to Supabase Storage
        url = f"{supabase_url.rstrip('/')}/storage/v1/object/{storage_path}"
        
        headers = {
            'Content-Type': 'application/octet-stream',
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        }
        
        req = request.Request(
            url,
            data=image_data,
            headers=headers,
            method='POST'
        )
        
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with request.urlopen(req, context=context, timeout=60) as response:
            if response.status in [200, 201]:
                return True
            else:
                print(f"Storage upload error: {response.status} - {response.reason}")
                return False
                
    except Exception as e:
        print(f"Error uploading image to storage: {str(e)}")
        return False

def create_storage_bucket(bucket_name: str, supabase_url: str, supabase_key: str) -> bool:
    """Create a storage bucket if it doesn't exist."""
    try:
        url = f"{supabase_url.rstrip('/')}/storage/v1/bucket"
        
        headers = {
            'Content-Type': 'application/json',
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        }
        
        data = {
            "id": bucket_name,
            "name": bucket_name,
            "public": True
        }
        
        data_bytes = json.dumps(data).encode('utf-8')
        
        req = request.Request(
            url,
            data=data_bytes,
            headers=headers,
            method='POST'
        )
        
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with request.urlopen(req, context=context, timeout=30) as response:
            # 200/201 means created, 409 means already exists
            if response.status in [200, 201, 409]:
                return True
            else:
                print(f"Bucket creation error: {response.status} - {response.reason}")
                return False
                
    except Exception as e:
        # If bucket already exists, that's fine
        if "already exists" in str(e) or "409" in str(e):
            return True
        print(f"Error creating storage bucket: {str(e)}")
        return False

def main():
    """Main function."""
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python quick_upload_rest.py <folder_path> [supabase_url] [supabase_key]")
        print("Example: python quick_upload_rest.py data/Batch54")
        print("Example: python quick_upload_rest.py data/Batch54 https://owcanqgrymdruzdrttfo.supabase.co")
        print("Example: python quick_upload_rest.py data/Batch54 https://owcanqgrymdruzdrttfo.supabase.co your_anon_key")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    supabase_url = sys.argv[2] if len(sys.argv) > 2 else "https://owcanqgrymdruzdrttfo.supabase.co"
    supabase_key = sys.argv[3] if len(sys.argv) > 3 else SUPABASE_ANON_KEY
    
    print("🚀 Quick Upload Script (REST API)")
    print("=" * 50)
    
    # Upload the folder
    success = upload_single_folder_rest(folder_path, supabase_url, supabase_key)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Upload completed successfully!")
    else:
        print("❌ Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 