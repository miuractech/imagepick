#!/usr/bin/env python3
"""
Configuration file for the Supabase Upload Manager
"""

# Database connection (for psql method)
SUPABASE_CONNECTION_STRING = "postgresql://postgres.owcanqgrymdruzdrttfo:dG.-pDR@fF$KZ4#@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

# REST API settings
SUPABASE_URL = "https://owcanqgrymdruzdrttfo.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93Y2FucWdyeW1kcnV6ZHJ0dGZvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAxMDk5NDgsImV4cCI6MjA2NTY4NTk0OH0.dTnDzGV86kttYh5fCzuQLTk3Klu9FkahEUMB0nLi60c"  # Replace with your actual anon key

# Device information
DEVICE_ID = "063bbb36-e3b5-4f39-9961-2379b3ec7df3"  # UUID from devices table
DEVICE_NAME = "TEST"  # Human-readable device name (from devices table)
DEVICE_TYPE = "image_analyzer"  # Type/category of device

# Upload settings
DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_RETRIES = 3
DEFAULT_DB_PATH = "upload_tracker.db"

# File patterns to look for
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
STATS_FILE_NAME = 'stats.json'

# Performance settings
BATCH_DELAY_SECONDS = 1  # Delay between batches
SCAN_PROGRESS_INTERVAL = 100  # Show progress every N folders
UPLOAD_TIMEOUT_SECONDS = 30

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Status file names
SUCCESS_FILE_NAME = "success.json"
FAILED_FILE_NAME = "failed.json"

# Database table names
DEVICE_TEST_TABLE = "device_test"
FOLDER_STATUS_TABLE = "folder_status"
UPLOAD_BATCHES_TABLE = "upload_batches"

# Test status logic
def determine_test_status(stats_data):
    """Determine test status based on stats.json content."""
    if not stats_data:
        return "pending"
    
    if stats_data.get("result") and len(stats_data["result"]) > 0:
        return "passed"
    else:
        return "failed"

# Metadata fields
METADATA_FIELDS = [
    "upload_timestamp",
    "total_images", 
    "files_processed",
    "folder_hash",
    "upload_batch_id",
    "device_id",
    "device_name",
    "device_type"
] 