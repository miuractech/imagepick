#!/usr/bin/env python3
"""
Script to upload folder contents to Supabase database.
Uses subprocess to call psql for database operations.
"""

import os
import json
import sys
import subprocess
import time
from datetime import datetime
import tempfile

class SupabaseUploader:
    def __init__(self, connection_string):
        """Initialize the uploader with connection string."""
        self.connection_string = connection_string
        self.upload_results = {
            "uploaded_files": [],
            "failed_files": [],
            "database_operations": [],
            "overall_status": "pending"
        }
    
    def execute_sql(self, sql_query, params=None):
        """Execute SQL query using psql command line tool."""
        try:
            # Create a temporary file for the SQL query
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(sql_query)
                temp_file_path = temp_file.name
            
            # Build psql command
            cmd = [
                'psql',
                self.connection_string,
                '-f', temp_file_path,
                '-t',  # tuples only
                '-q'   # quiet mode
            ]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"SQL Error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("SQL query timed out")
            return None
        except Exception as e:
            print(f"Error executing SQL: {str(e)}")
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
            
            # Build SQL query with proper escaping
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
            
            result = self.execute_sql(insert_query)
            
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

def check_psql_available():
    """Check if psql command is available."""
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    """Main function to handle command line arguments and execute upload."""
    if len(sys.argv) != 2:
        print("Usage: python upload_to_supabase_simple.py <folder_path>")
        sys.exit(1)
    
    # Check if psql is available
    if not check_psql_available():
        print("Error: psql command not found. Please install PostgreSQL client tools.")
        print("On Windows: Download from https://www.postgresql.org/download/windows/")
        print("On macOS: brew install postgresql")
        print("On Ubuntu: sudo apt-get install postgresql-client")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    connection_string = "postgresql://postgres.owcanqgrymdruzdrttfo:dG.-pDR@fF$KZ4#@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
    
    # Create uploader instance
    uploader = SupabaseUploader(connection_string)
    
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