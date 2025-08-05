#!/usr/bin/env python3
"""
Advanced Upload Manager for Supabase using REST API
Handles millions of folders efficiently by tracking upload status and processing only necessary folders.
Uses Supabase REST API instead of direct database connection.
"""

import os
import json
import sys
import time
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib import request, parse
import ssl
from typing import List, Dict, Set, Optional, Tuple
import argparse
from config import DEVICE_ID, DEVICE_NAME, DEVICE_TYPE, SUPABASE_ANON_KEY

class UploadTracker:
    """Tracks upload status in a local SQLite database."""
    
    def __init__(self, db_path: str = "upload_tracker.db"):
        """Initialize the upload tracker with SQLite database."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with necessary tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS folder_status (
                    folder_path TEXT PRIMARY KEY,
                    folder_name TEXT NOT NULL,
                    last_modified REAL NOT NULL,
                    file_count INTEGER NOT NULL,
                    file_hash TEXT NOT NULL,
                    upload_status TEXT NOT NULL,
                    upload_timestamp REAL,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS upload_batches (
                    batch_id TEXT PRIMARY KEY,
                    batch_name TEXT NOT NULL,
                    total_folders INTEGER NOT NULL,
                    successful_uploads INTEGER DEFAULT 0,
                    failed_uploads INTEGER DEFAULT 0,
                    start_time REAL NOT NULL,
                    end_time REAL,
                    status TEXT DEFAULT 'running',
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_folder_status_upload_status 
                ON folder_status(upload_status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_folder_status_last_modified 
                ON folder_status(last_modified)
            """)
            
            conn.commit()
    
    def calculate_folder_hash(self, folder_path: str) -> str:
        """Calculate a hash of the folder contents to detect changes."""
        try:
            files = []
            for file_path in Path(folder_path).rglob('*'):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append((str(file_path.relative_to(folder_path)), stat.st_mtime, stat.st_size))
            
            # Sort files for consistent hashing
            files.sort(key=lambda x: x[0])
            
            # Create hash from file names, modification times, and sizes
            content = json.dumps(files, sort_keys=True)
            return hashlib.md5(content.encode()).hexdigest()
            
        except Exception as e:
            print(f"Error calculating hash for {folder_path}: {e}")
            return ""
    
    def get_folder_info(self, folder_path: str) -> Optional[Dict]:
        """Get information about a folder from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT folder_path, folder_name, last_modified, file_count, 
                       file_hash, upload_status, upload_timestamp, error_message, retry_count
                FROM folder_status 
                WHERE folder_path = ?
            """, (folder_path,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'folder_path': row[0],
                    'folder_name': row[1],
                    'last_modified': row[2],
                    'file_count': row[3],
                    'file_hash': row[4],
                    'upload_status': row[5],
                    'upload_timestamp': row[6],
                    'error_message': row[7],
                    'retry_count': row[8]
                }
            return None
    
    def update_folder_status(self, folder_path: str, status: str, error_message: str = None):
        """Update the status of a folder in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE folder_status 
                SET upload_status = ?, upload_timestamp = ?, error_message = ?, 
                    retry_count = retry_count + 1, updated_at = (strftime('%s', 'now'))
                WHERE folder_path = ?
            """, (status, time.time(), error_message, folder_path))
            conn.commit()
    
    def record_folder(self, folder_path: str, folder_name: str, file_count: int, file_hash: str):
        """Record a new folder or update existing folder information."""
        last_modified = os.path.getmtime(folder_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO folder_status 
                (folder_path, folder_name, last_modified, file_count, file_hash, 
                 upload_status, updated_at)
                VALUES (?, ?, ?, ?, ?, 'pending', (strftime('%s', 'now')))
            """, (folder_path, folder_name, last_modified, file_count, file_hash))
            conn.commit()
    
    def get_folders_to_process(self, base_path: str, max_retries: int = 3) -> List[Dict]:
        """Get list of folders that need to be processed."""
        folders_to_process = []
        
        with sqlite3.connect(self.db_path) as conn:
            # Get folders that need processing
            cursor = conn.execute("""
                SELECT folder_path, folder_name, last_modified, file_count, 
                       file_hash, upload_status, retry_count
                FROM folder_status 
                WHERE folder_path LIKE ? AND 
                      (upload_status IN ('pending', 'failed') OR upload_status IS NULL) AND
                      retry_count < ?
                ORDER BY last_modified ASC
            """, (f"{base_path}%", max_retries))
            
            for row in cursor.fetchall():
                folder_info = {
                    'folder_path': row[0],
                    'folder_name': row[1],
                    'last_modified': row[2],
                    'file_count': row[3],
                    'file_hash': row[4],
                    'upload_status': row[5],
                    'retry_count': row[6]
                }
                
                # Check if folder still exists and has changed
                if os.path.exists(folder_info['folder_path']):
                    current_hash = self.calculate_folder_hash(folder_info['folder_path'])
                    current_modified = os.path.getmtime(folder_info['folder_path'])
                    
                    # Process if hash changed or status is pending/failed
                    if (current_hash != folder_info['file_hash'] or 
                        folder_info['upload_status'] in ['pending', 'failed']):
                        folder_info['current_hash'] = current_hash
                        folder_info['current_modified'] = current_modified
                        folders_to_process.append(folder_info)
        
        return folders_to_process
    
    def create_batch(self, batch_name: str, total_folders: int) -> str:
        """Create a new upload batch."""
        batch_id = f"batch_{int(time.time())}_{hash(batch_name) % 10000}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO upload_batches 
                (batch_id, batch_name, total_folders, start_time)
                VALUES (?, ?, ?, ?)
            """, (batch_id, batch_name, total_folders, time.time()))
            conn.commit()
        
        return batch_id
    
    def update_batch_status(self, batch_id: str, successful: int = 0, failed: int = 0, status: str = None):
        """Update batch status."""
        with sqlite3.connect(self.db_path) as conn:
            if status == 'completed':
                conn.execute("""
                    UPDATE upload_batches 
                    SET successful_uploads = ?, failed_uploads = ?, 
                        end_time = ?, status = ?
                    WHERE batch_id = ?
                """, (successful, failed, time.time(), status, batch_id))
            else:
                conn.execute("""
                    UPDATE upload_batches 
                    SET successful_uploads = successful_uploads + ?, 
                        failed_uploads = failed_uploads + ?
                    WHERE batch_id = ?
                """, (successful, failed, batch_id))
            conn.commit()

class SupabaseRestUploader:
    """Supabase uploader using REST API."""
    
    def __init__(self, supabase_url: str, supabase_key: str, tracker: UploadTracker):
        """Initialize the uploader with Supabase REST API credentials."""
        self.supabase_url = supabase_url.rstrip('/')
        self.supabase_key = supabase_key
        self.tracker = tracker
        self.upload_results = {
            "uploaded_files": [],
            "failed_files": [],
            "database_operations": [],
            "overall_status": "pending"
        }
    
    def make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to Supabase REST API."""
        try:
            url = f"{self.supabase_url}/rest/v1/{endpoint}"
            
            # Default headers
            headers = {
                'Content-Type': 'application/json',
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}',
                'Prefer': 'return=minimal'
            }
            
            # Prepare request
            if data:
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = None
            
            # Create request
            req = request.Request(
                url,
                data=data_bytes,
                headers=headers,
                method=method
            )
            
            # Create SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Make request
            with request.urlopen(req, context=context, timeout=30) as response:
                if response.status in [200, 201]:
                    response_data = response.read().decode('utf-8')
                    return json.loads(response_data) if response_data else {}
                else:
                    print(f"HTTP Error {response.status}: {response.reason}")
                    return None
                    
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    def upload_folder(self, folder_path: str, folder_info: Dict) -> bool:
        """Upload a single folder to Supabase using REST API."""
        folder_name = folder_info['folder_name']
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
            
            # Upload images to Supabase Storage
            uploaded_image_urls = []
            for image_file in image_files:
                image_path = os.path.join(folder_path, image_file)
                # URL encode the filename for storage path
                encoded_filename = parse.quote(image_file)
                storage_path = f"images/{DEVICE_ID}/{folder_name}/{encoded_filename}"
                
                print(f"  📤 Uploading image: {image_file}")
                if self.upload_image_to_storage(image_path, storage_path):
                    # Get public URL for the uploaded image (use encoded filename)
                    image_url = f"{self.supabase_url}/storage/v1/object/public/images/{DEVICE_ID}/{folder_name}/{encoded_filename}"
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
                "files_processed": files,
                "folder_hash": folder_info.get('current_hash', folder_info['file_hash']),
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
            
            # Insert into database using REST API
            result = self.make_request('device_test', method='POST', data=insert_data)
            
            if result is not None:
                print(f"✅ Successfully uploaded folder: {folder_name}")
                self.tracker.update_folder_status(folder_path, "success")
                return True
            else:
                print(f"❌ Failed to upload folder: {folder_name}")
                self.tracker.update_folder_status(folder_path, "failed", "REST API upload failed")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading folder {folder_name}: {str(e)}")
            self.tracker.update_folder_status(folder_path, "failed", str(e))
            return False

    def upload_image_to_storage(self, image_path: str, storage_path: str) -> bool:
        """Upload a single image file to Supabase Storage."""
        try:
            # Read the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Create storage bucket if it doesn't exist
            self.create_storage_bucket("images")
            
            # Upload to Supabase Storage
            url = f"{self.supabase_url}/storage/v1/object/{storage_path}"
            
            headers = {
                'Content-Type': 'application/octet-stream',
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}'
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

    def create_storage_bucket(self, bucket_name: str) -> bool:
        """Create a storage bucket if it doesn't exist."""
        try:
            url = f"{self.supabase_url}/storage/v1/bucket"
            
            headers = {
                'Content-Type': 'application/json',
                'apikey': self.supabase_key,
                'Authorization': f'Bearer {self.supabase_key}'
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

class UploadManager:
    """Main upload manager that coordinates the entire process."""
    
    def __init__(self, base_path: str, supabase_url: str, supabase_key: str, db_path: str = "upload_tracker.db"):
        """Initialize the upload manager."""
        self.base_path = base_path
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.tracker = UploadTracker(db_path)
        self.uploader = SupabaseRestUploader(supabase_url, supabase_key, self.tracker)
    
    def scan_and_record_folders(self) -> int:
        """Scan the base path and record all folders."""
        print(f"Scanning folders in: {self.base_path}")
        
        recorded_count = 0
        for root, dirs, files in os.walk(self.base_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            # Check if this directory contains image files or stats.json
            has_images = any(f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')) for f in files)
            has_stats = 'stats.json' in files
            
            if has_images or has_stats:
                folder_path = root
                folder_name = os.path.basename(root)
                file_count = len(files)
                file_hash = self.tracker.calculate_folder_hash(folder_path)
                
                self.tracker.record_folder(folder_path, folder_name, file_count, file_hash)
                recorded_count += 1
                
                if recorded_count % 100 == 0:
                    print(f"Recorded {recorded_count} folders...")
        
        print(f"Total folders recorded: {recorded_count}")
        return recorded_count
    
    def process_folders(self, batch_size: int = 50, max_retries: int = 3) -> Dict:
        """Process folders in batches."""
        print(f"Processing folders with batch size: {batch_size}")
        
        # Get folders to process
        folders_to_process = self.tracker.get_folders_to_process(self.base_path, max_retries)
        
        if not folders_to_process:
            print("No folders to process!")
            return {"successful": 0, "failed": 0, "total": 0}
        
        print(f"Found {len(folders_to_process)} folders to process")
        
        # Create batch
        batch_id = self.tracker.create_batch(
            f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
            len(folders_to_process)
        )
        
        successful = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(folders_to_process), batch_size):
            batch = folders_to_process[i:i + batch_size]
            print(f"\nProcessing batch {i//batch_size + 1}/{(len(folders_to_process) + batch_size - 1)//batch_size}")
            
            batch_successful = 0
            batch_failed = 0
            
            for folder_info in batch:
                try:
                    if self.uploader.upload_folder(folder_info['folder_path'], folder_info):
                        batch_successful += 1
                        successful += 1
                    else:
                        batch_failed += 1
                        failed += 1
                except Exception as e:
                    print(f"❌ Error processing {folder_info['folder_name']}: {e}")
                    batch_failed += 1
                    failed += 1
                    self.tracker.update_folder_status(
                        folder_info['folder_path'], "failed", str(e)
                    )
            
            # Update batch status
            self.tracker.update_batch_status(batch_id, batch_successful, batch_failed)
            
            print(f"Batch completed: {batch_successful} successful, {batch_failed} failed")
            
            # Small delay between batches to avoid overwhelming the API
            if i + batch_size < len(folders_to_process):
                time.sleep(1)
        
        # Mark batch as completed
        self.tracker.update_batch_status(batch_id, successful, failed, "completed")
        
        return {
            "successful": successful,
            "failed": failed,
            "total": len(folders_to_process),
            "batch_id": batch_id
        }
    
    def get_status_report(self) -> Dict:
        """Generate a status report."""
        with sqlite3.connect(self.tracker.db_path) as conn:
            # Get overall statistics
            cursor = conn.execute("""
                SELECT upload_status, COUNT(*) as count
                FROM folder_status
                GROUP BY upload_status
            """)
            
            status_counts = dict(cursor.fetchall())
            
            # Get recent batches
            cursor = conn.execute("""
                SELECT batch_id, batch_name, total_folders, successful_uploads, 
                       failed_uploads, start_time, end_time, status
                FROM upload_batches
                ORDER BY start_time DESC
                LIMIT 10
            """)
            
            recent_batches = []
            for row in cursor.fetchall():
                recent_batches.append({
                    'batch_id': row[0],
                    'batch_name': row[1],
                    'total_folders': row[2],
                    'successful_uploads': row[3],
                    'failed_uploads': row[4],
                    'start_time': datetime.fromtimestamp(row[5]),
                    'end_time': datetime.fromtimestamp(row[6]) if row[6] else None,
                    'status': row[7]
                })
            
            return {
                'status_counts': status_counts,
                'recent_batches': recent_batches,
                'total_folders': sum(status_counts.values())
            }

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description='Supabase Upload Manager (REST API)')
    parser.add_argument('base_path', help='Base path containing folders to upload')
    parser.add_argument('--scan-only', action='store_true', help='Only scan and record folders, don\'t upload')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of folders to process in each batch')
    parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retry attempts')
    parser.add_argument('--db-path', default='upload_tracker.db', help='Path to SQLite tracking database')
    parser.add_argument('--status', action='store_true', help='Show status report and exit')
    parser.add_argument('--supabase-url', default='https://owcanqgrymdruzdrttfo.supabase.co', help='Supabase URL')
    parser.add_argument('--supabase-key', default=SUPABASE_ANON_KEY, help='Supabase anon key')
    
    args = parser.parse_args()
    
    # Create upload manager
    manager = UploadManager(args.base_path, args.supabase_url, args.supabase_key, args.db_path)
    
    if args.status:
        # Show status report
        report = manager.get_status_report()
        print("\n" + "="*60)
        print("UPLOAD STATUS REPORT")
        print("="*60)
        print(f"Total folders tracked: {report['total_folders']}")
        print("\nStatus breakdown:")
        for status, count in report['status_counts'].items():
            print(f"  {status}: {count}")
        
        print("\nRecent batches:")
        for batch in report['recent_batches']:
            print(f"  {batch['batch_name']}: {batch['successful_uploads']}/{batch['total_folders']} successful")
        
        return
    
    # Scan and record folders
    recorded_count = manager.scan_and_record_folders()
    
    if args.scan_only:
        print("Scan completed. Use --status to view results.")
        return
    
    # Process folders
    if recorded_count > 0:
        print(f"\nStarting upload process for {recorded_count} folders...")
        result = manager.process_folders(args.batch_size, args.max_retries)
        
        print("\n" + "="*60)
        print("UPLOAD COMPLETED")
        print("="*60)
        print(f"Total processed: {result['total']}")
        print(f"Successful: {result['successful']}")
        print(f"Failed: {result['failed']}")
        print(f"Batch ID: {result['batch_id']}")
        
        if result['failed'] > 0:
            print(f"\n⚠️  {result['failed']} folders failed. Check the database for details.")
            print("Run with --status to see detailed report.")
    else:
        print("No folders found to process.")

if __name__ == "__main__":
    main() 