#!/usr/bin/env python3
"""
Quick Upload Script for Single Folders
Simple script to upload a single folder without the full tracking system.
"""

import os
import json
import sys
import time
import subprocess
import tempfile
from datetime import datetime
from config import SUPABASE_CONNECTION_STRING, determine_test_status

def check_psql_available():
    """Check if psql command is available."""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def execute_sql(sql_query):
    """Execute SQL query using psql."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            temp_file.write(sql_query)
            temp_file_path = temp_file.name
        
        cmd = [
            'psql',
            SUPABASE_CONNECTION_STRING,
            '-f', temp_file_path,
            '-t',
            '-q'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        os.unlink(temp_file_path)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"SQL Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error executing SQL: {str(e)}")
        return None

def upload_single_folder(folder_path):
    """Upload a single folder to Supabase."""
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
        test_status = determine_test_status(stats_data)
        print(f"🏷️  Test status: {test_status}")
        
        # Create metadata
        metadata = {
            "upload_timestamp": test_date.isoformat(),
            "total_images": len(image_files),
            "files_processed": files,
            "upload_method": "quick_upload"
        }
        
        # Build SQL query
        images_array = "ARRAY[" + ",".join([f"'{img}'" for img in image_files]) + "]"
        stats_json = f"'{json.dumps(stats_data)}'::jsonb" if stats_data else "NULL"
        metadata_json = f"'{json.dumps(metadata)}'::jsonb"
        
        insert_query = f"""
        INSERT INTO device_test (
            folder_name, images, test_results, test_date, 
            test_status, upload_batch, metadata, data_type
        ) VALUES (
            '{folder_name}',
            {images_array},
            {stats_json},
            '{test_date.isoformat()}',
            '{test_status}',
            '{upload_batch}',
            {metadata_json},
            'image_analysis'
        ) ON CONFLICT (folder_name, device_id) 
        DO UPDATE SET 
            images = EXCLUDED.images,
            test_results = EXCLUDED.test_results,
            test_date = EXCLUDED.test_date,
            test_status = EXCLUDED.test_status,
            upload_batch = EXCLUDED.upload_batch,
            metadata = EXCLUDED.metadata,
            updated_at = NOW();
        """
        
        print("🚀 Executing database insert...")
        result = execute_sql(insert_query)
        
        if result is not None:
            print(f"✅ Successfully uploaded folder: {folder_name}")
            
            # Create success.json
            success_data = {
                "timestamp": test_date.isoformat(),
                "folder": folder_name,
                "status": "success",
                "uploaded_files": image_files + ([stats_file] if stats_file else []),
                "test_status": test_status,
                "upload_batch": upload_batch
            }
            
            success_file = os.path.join(folder_path, "success.json")
            with open(success_file, 'w') as f:
                json.dump(success_data, f, indent=2)
            
            print(f"📄 Created success.json in {folder_name}")
            return True
        else:
            print(f"❌ Failed to upload folder: {folder_name}")
            
            # Create failed.json
            failed_data = {
                "timestamp": test_date.isoformat(),
                "folder": folder_name,
                "status": "failed",
                "error": "Database upload failed",
                "upload_batch": upload_batch
            }
            
            failed_file = os.path.join(folder_path, "failed.json")
            with open(failed_file, 'w') as f:
                json.dump(failed_data, f, indent=2)
            
            print(f"📄 Created failed.json in {folder_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading folder {folder_name}: {str(e)}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python quick_upload.py <folder_path>")
        print("Example: python quick_upload.py data/Batch54")
        sys.exit(1)
    
    # Check if psql is available
    if not check_psql_available():
        print("❌ Error: psql command not found. Please install PostgreSQL client tools.")
        print("On Windows: Download from https://www.postgresql.org/download/windows/")
        print("On macOS: brew install postgresql")
        print("On Ubuntu: sudo apt-get install postgresql-client")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    print("🚀 Quick Upload Script")
    print("=" * 50)
    
    # Upload the folder
    success = upload_single_folder(folder_path)
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Upload completed successfully!")
    else:
        print("❌ Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 