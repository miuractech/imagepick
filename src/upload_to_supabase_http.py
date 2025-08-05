#!/usr/bin/env python3
"""
Script to upload folder contents to Supabase using HTTP REST API.
This version uses built-in Python modules only.
"""

import os
import json
import sys
import time
import base64
import hashlib
import hmac
from datetime import datetime
from urllib import request, parse
import ssl

class SupabaseUploader:
    def __init__(self, supabase_url, supabase_key):
        """Initialize the uploader with Supabase credentials."""
        self.supabase_url = supabase_url.rstrip('/')
        self.supabase_key = supabase_key
        self.upload_results = {
            "uploaded_files": [],
            "failed_files": [],
            "database_operations": [],
            "overall_status": "pending"
        }
    
    def make_request(self, endpoint, method='GET', data=None, headers=None):
        """Make HTTP request to Supabase API."""
        try:
            url = f"{self.supabase_url}/rest/v1/{endpoint}"
            
            # Default headers
            default_headers = {
                'Content-Type': 'application/json',
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Prefer': 'return=minimal'
            }
            
            if headers:
                default_headers.update(headers)
            
            # Prepare request
            if data:
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = None
            
            # Create request
            req = request.Request(
                url,
                data=data_bytes,
                headers=default_headers,
                method=method
            )
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Make request
            with request.urlopen(req, context=context, timeout=30) as response:
                if response.status in [200, 201]:
                    return response.read().decode('utf-8')
                else:
                    print(f"HTTP Error {response.status}: {response.reason}")
                    return None
                    
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    def upload_folder(self, folder_path):
        """Upload contents of a folder to Supabase."""
        if not os.path.exists(folder_path):
            print(f"Folder does not exist: {folder_path}")
            self.upload_results["overall_status"] = "failed"
            return False
        
        folder_name = os.path.basename(folder_path)
        print(f"Uploading folder: {folder_name}")
        
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
            
            # Read stats.json if exists
            stats_data = None
            if stats_file:
                try:
                    with open(os.path.join(folder_path, stats_file), 'r') as f:
                        stats_data = json.load(f)
                    print(f"Loaded stats.json: {len(json.dumps(stats_data))} characters")
                except Exception as e:
                    print(f"Error reading stats.json: {str(e)}")
                    self.upload_results["failed_files"].append({
                        "file": stats_file,
                        "error": str(e)
                    })
            
            # Prepare data for database
            test_date = datetime.now()
            upload_batch = f"batch_{int(time.time())}"
            
            # Determine test status based on stats
            test_status = "pending"
            if stats_data:
                if stats_data.get("result") and len(stats_data["result"]) > 0:
                    test_status = "passed"
                else:
                    test_status = "failed"
            
            # Create metadata
            metadata = {
                "upload_timestamp": test_date.isoformat(),
                "total_images": len(image_files),
                "files_processed": files
            }
            
            # Prepare data for insertion
            insert_data = {
                "folder_name": folder_name,
                "images": image_files,
                "test_results": stats_data,
                "test_date": test_date.isoformat(),
                "test_status": test_status,
                "upload_batch": upload_batch,
                "metadata": metadata,
                "data_type": "image_analysis"
            }
            
            # Insert into database using REST API
            result = self.make_request(
                'device_test',
                method='POST',
                data=insert_data
            )
            
            if result is not None:
                print(f"Successfully uploaded folder: {folder_name}")
                self.upload_results["uploaded_files"].extend(image_files)
                if stats_file:
                    self.upload_results["uploaded_files"].append(stats_file)
                self.upload_results["database_operations"].append({
                    "operation": "insert",
                    "folder": folder_name,
                    "status": "success",
                    "timestamp": test_date.isoformat()
                })
                self.upload_results["overall_status"] = "success"
                return True
            else:
                print(f"Failed to upload folder: {folder_name}")
                self.upload_results["failed_files"].extend(image_files)
                if stats_file:
                    self.upload_results["failed_files"].append(stats_file)
                self.upload_results["overall_status"] = "failed"
                return False
                
        except Exception as e:
            print(f"Error uploading folder {folder_name}: {str(e)}")
            self.upload_results["overall_status"] = "failed"
            return False
    
    def create_status_file(self, folder_path):
        """Create success.json or failed.json based on upload results."""
        timestamp = datetime.now().isoformat()
        
        status_data = {
            "timestamp": timestamp,
            "folder": os.path.basename(folder_path),
            "overall_status": self.upload_results["overall_status"],
            "uploaded_files": self.upload_results["uploaded_files"],
            "failed_files": self.upload_results["failed_files"],
            "database_operations": self.upload_results["database_operations"],
            "summary": {
                "total_files_processed": len(self.upload_results["uploaded_files"]) + len(self.upload_results["failed_files"]),
                "successful_uploads": len(self.upload_results["uploaded_files"]),
                "failed_uploads": len(self.upload_results["failed_files"])
            }
        }
        
        # Determine filename based on overall status
        if self.upload_results["overall_status"] == "success":
            filename = "success.json"
        else:
            filename = "failed.json"
        
        filepath = os.path.join(folder_path, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(status_data, f, indent=2)
            print(f"Created status file: {filepath}")
            return True
        except Exception as e:
            print(f"Error creating status file: {str(e)}")
            return False

def main():
    """Main function to handle command line arguments and execute upload."""
    if len(sys.argv) != 2:
        print("Usage: python upload_to_supabase_http.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # Supabase configuration
    # You'll need to replace these with your actual Supabase URL and anon key
    supabase_url = "https://owcanqgrymdruzdrttfo.supabase.co"
    supabase_key = "your_supabase_anon_key_here"  # Replace with actual anon key
    
    print("⚠️  IMPORTANT: You need to set your Supabase anon key in the script!")
    print("1. Go to your Supabase project dashboard")
    print("2. Go to Settings > API")
    print("3. Copy the 'anon public' key")
    print("4. Replace 'your_supabase_anon_key_here' in the script")
    print()
    
    # Check if key is still placeholder
    if supabase_key == "your_supabase_anon_key_here":
        print("❌ Please set your Supabase anon key before running the script!")
        sys.exit(1)
    
    # Create uploader instance
    uploader = SupabaseUploader(supabase_url, supabase_key)
    
    # Upload folder
    success = uploader.upload_folder(folder_path)
    
    # Create status file
    uploader.create_status_file(folder_path)
    
    # Print summary
    print("\n" + "="*50)
    print("UPLOAD SUMMARY")
    print("="*50)
    print(f"Folder: {os.path.basename(folder_path)}")
    print(f"Overall Status: {uploader.upload_results['overall_status']}")
    print(f"Uploaded Files: {len(uploader.upload_results['uploaded_files'])}")
    print(f"Failed Files: {len(uploader.upload_results['failed_files'])}")
    
    if uploader.upload_results['failed_files']:
        print("\nFailed Files:")
        for file in uploader.upload_results['failed_files']:
            if isinstance(file, dict):
                print(f"  - {file['file']}: {file['error']}")
            else:
                print(f"  - {file}")
    
    if success:
        print("\n✅ Upload completed successfully!")
    else:
        print("\n❌ Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 