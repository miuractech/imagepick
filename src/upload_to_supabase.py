#!/usr/bin/env python3
"""
Script to upload folder contents to Supabase database.
Handles multiple images, stats.json files, and creates status reports.
"""

import os
import json
import sys
import socket
import ssl
import base64
import hashlib
import time
from datetime import datetime
from urllib.parse import urlparse, quote_plus
import re

class SupabaseUploader:
    def __init__(self, connection_string):
        """Initialize the uploader with connection string."""
        self.connection_string = connection_string
        self.connection = None
        self.upload_results = {
            "uploaded_files": [],
            "failed_files": [],
            "database_operations": [],
            "overall_status": "pending"
        }
        
    def parse_connection_string(self):
        """Parse the PostgreSQL connection string."""
        # Remove postgresql:// prefix
        url = self.connection_string.replace('postgresql://', '')
        
        # Split into parts
        parts = url.split('@')
        if len(parts) != 2:
            raise ValueError("Invalid connection string format")
            
        credentials, host_port_db = parts
        
        # Parse credentials
        user_pass = credentials.split(':')
        if len(user_pass) != 2:
            raise ValueError("Invalid credentials format")
            
        username, password = user_pass
        
        # Parse host, port, and database
        host_port, database = host_port_db.split('/')
        host, port = host_port.split(':')
        
        return {
            'host': host,
            'port': int(port),
            'database': database,
            'username': username,
            'password': password
        }
    
    def create_ssl_context(self):
        """Create SSL context for secure connection."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    def connect_to_database(self):
        """Establish connection to PostgreSQL database."""
        try:
            config = self.parse_connection_string()
            
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            
            # Connect with SSL
            context = self.create_ssl_context()
            self.connection = context.wrap_socket(sock, server_hostname=config['host'])
            self.connection.connect((config['host'], config['port']))
            
            # Send startup message
            startup_message = self.create_startup_message(config)
            self.connection.send(startup_message)
            
            # Handle authentication
            self.handle_authentication(config['password'])
            
            print(f"Successfully connected to database: {config['database']}")
            return True
            
        except Exception as e:
            print(f"Failed to connect to database: {str(e)}")
            self.upload_results["overall_status"] = "failed"
            return False
    
    def create_startup_message(self, config):
        """Create PostgreSQL startup message."""
        # PostgreSQL protocol version 3.0
        version = b'\x00\x00\x00\x00'
        
        # Parameters
        params = {
            b'user': config['username'].encode('utf-8'),
            b'database': config['database'].encode('utf-8'),
            b'application_name': b'python_uploader',
            b'client_encoding': b'UTF8'
        }
        
        # Build message
        message = version
        for key, value in params.items():
            message += key + b'\x00' + value + b'\x00'
        message += b'\x00'
        
        # Add length
        length = len(message) + 4
        return length.to_bytes(4, 'big') + message
    
    def handle_authentication(self, password):
        """Handle PostgreSQL authentication."""
        while True:
            response = self.read_message()
            if response is None:
                break
                
            msg_type = response[0]
            
            if msg_type == b'R':  # Authentication request
                auth_type = int.from_bytes(response[5:9], 'big')
                if auth_type == 5:  # MD5 authentication
                    salt = response[9:13]
                    hashed_password = self.md5_password(password, salt)
                    self.send_password(hashed_password)
                elif auth_type == 0:  # OK
                    break
            elif msg_type == b'Z':  # Ready for query
                break
            elif msg_type == b'E':  # Error
                error_msg = response[5:].decode('utf-8', errors='ignore')
                raise Exception(f"Authentication error: {error_msg}")
    
    def md5_password(self, password, salt):
        """Generate MD5 password hash for PostgreSQL."""
        # First hash: md5(password + username)
        username = self.parse_connection_string()['username']
        first_hash = hashlib.md5((password + username).encode('utf-8')).hexdigest()
        
        # Second hash: md5(first_hash + salt)
        second_hash = hashlib.md5((first_hash + salt.hex()).encode('utf-8')).hexdigest()
        
        return 'md5' + second_hash
    
    def send_password(self, password):
        """Send password to PostgreSQL server."""
        message = b'p' + len(password + '\x00').to_bytes(4, 'big') + password.encode('utf-8') + b'\x00'
        self.connection.send(message)
    
    def read_message(self):
        """Read a message from PostgreSQL server."""
        try:
            # Read message length
            length_bytes = self.connection.recv(4)
            if not length_bytes:
                return None
                
            length = int.from_bytes(length_bytes, 'big')
            
            # Read message body
            message = self.connection.recv(length - 4)
            if len(message) < length - 4:
                # Read remaining bytes
                remaining = length - 4 - len(message)
                message += self.connection.recv(remaining)
            
            return message
            
        except Exception as e:
            print(f"Error reading message: {str(e)}")
            return None
    
    def execute_query(self, query, params=None):
        """Execute a SQL query."""
        try:
            # Prepare query
            if params:
                # Simple parameter substitution (not production-ready)
                for i, param in enumerate(params):
                    placeholder = f"${i+1}"
                    if isinstance(param, str):
                        param = f"'{param}'"
                    elif isinstance(param, list):
                        param = f"ARRAY{param}"
                    elif isinstance(param, dict):
                        param = f"'{json.dumps(param)}'::jsonb"
                    query = query.replace(placeholder, str(param))
            
            # Send query
            query_message = b'Q' + len(query + '\x00').to_bytes(4, 'big') + query.encode('utf-8') + b'\x00'
            self.connection.send(query_message)
            
            # Read response
            results = []
            while True:
                response = self.read_message()
                if response is None:
                    break
                    
                msg_type = response[0]
                
                if msg_type == b'T':  # Row description
                    # Parse column info
                    pass
                elif msg_type == b'D':  # Data row
                    # Parse data
                    pass
                elif msg_type == b'C':  # Command complete
                    command = response[5:].decode('utf-8', errors='ignore')
                    results.append(command)
                elif msg_type == b'Z':  # Ready for query
                    break
                elif msg_type == b'E':  # Error
                    error_msg = response[5:].decode('utf-8', errors='ignore')
                    raise Exception(f"Query error: {error_msg}")
            
            return results
            
        except Exception as e:
            print(f"Error executing query: {str(e)}")
            return None
    
    def upload_folder(self, folder_path):
        """Upload contents of a folder to Supabase."""
        if not os.path.exists(folder_path):
            print(f"Folder does not exist: {folder_path}")
            self.upload_results["overall_status"] = "failed"
            return False
        
        folder_name = os.path.basename(folder_path)
        print(f"Uploading folder: {folder_name}")
        
        # Connect to database
        if not self.connect_to_database():
            return False
        
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
            
            # Insert into database
            insert_query = """
            INSERT INTO device_test (
                folder_name, images, test_results, test_date, 
                test_status, upload_batch, metadata, data_type
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8
            ) ON CONFLICT (folder_name, device_id) 
            DO UPDATE SET 
                images = EXCLUDED.images,
                test_results = EXCLUDED.test_results,
                test_date = EXCLUDED.test_date,
                test_status = EXCLUDED.test_status,
                upload_batch = EXCLUDED.upload_batch,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            """
            
            metadata = {
                "upload_timestamp": test_date.isoformat(),
                "total_images": len(image_files),
                "files_processed": files
            }
            
            params = [
                folder_name,
                image_files,
                json.dumps(stats_data) if stats_data else None,
                test_date.isoformat(),
                test_status,
                upload_batch,
                json.dumps(metadata),
                "image_analysis"
            ]
            
            result = self.execute_query(insert_query, params)
            
            if result:
                print(f"Successfully uploaded folder: {folder_name}")
                self.upload_results["uploaded_files"].extend(image_files)
                if stats_file:
                    self.upload_results["uploaded_files"].append(stats_file)
                self.upload_results["database_operations"].append({
                    "operation": "insert",
                    "folder": folder_name,
                    "status": "success",
                    "rows_affected": len(result)
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
        finally:
            if self.connection:
                self.connection.close()
    
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
        print("Usage: python upload_to_supabase.py <folder_path>")
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
            print(f"  - {file}")
    
    if success:
        print("\n✅ Upload completed successfully!")
    else:
        print("\n❌ Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 