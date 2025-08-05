#!/usr/bin/env python3
"""
Test script to demonstrate the upload functionality.
This script will test uploading a sample folder to Supabase.
"""

import os
import json
import tempfile
import shutil
from datetime import datetime

def create_test_folder():
    """Create a test folder with sample data."""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="test_upload_")
    test_folder = os.path.join(temp_dir, "TestBatch")
    os.makedirs(test_folder, exist_ok=True)
    
    # Create sample stats.json
    stats_data = {
        "result": [[[99, 104, 203]]],
        "mean": [[99.0, 104.0, 203.0]],
        "standard deviation": [[0.0, 0.0, 0.0]],
        "variance": [[0.0, 0.0, 0.0]],
        "max": [[99, 104, 203]],
        "min": [[99, 104, 203]],
        "range": [[0, 0, 0]]
    }
    
    with open(os.path.join(test_folder, "stats.json"), 'w') as f:
        json.dump(stats_data, f, indent=2)
    
    # Create sample image files (empty files for testing)
    sample_images = [
        "test_image_1.jpg",
        "test_image_2.png",
        "sample_photo.jpeg"
    ]
    
    for img in sample_images:
        with open(os.path.join(test_folder, img), 'w') as f:
            f.write(f"# This is a test image file: {img}\n")
            f.write(f"# Created at: {datetime.now().isoformat()}\n")
    
    # Create a PDF file (not an image, should be ignored)
    with open(os.path.join(test_folder, "document.pdf"), 'w') as f:
        f.write("This is a test PDF document\n")
    
    print(f"Created test folder: {test_folder}")
    print(f"Files created:")
    for file in os.listdir(test_folder):
        print(f"  - {file}")
    
    return test_folder

def test_upload_script():
    """Test the upload script with the created test folder."""
    print("\n" + "="*60)
    print("TESTING UPLOAD SCRIPT")
    print("="*60)
    
    # Create test folder
    test_folder = create_test_folder()
    
    try:
        # Import and test the simple upload script
        print(f"\nTesting upload with folder: {test_folder}")
        
        # Note: This is a demonstration - actual upload requires:
        # 1. psql to be installed (for simple version)
        # 2. Valid Supabase credentials
        # 3. Network connectivity to Supabase
        
        print("\nTo actually test the upload, run:")
        print(f"python upload_to_supabase_simple.py \"{test_folder}\"")
        
        print("\nOr for HTTP API version:")
        print(f"python upload_to_supabase_http.py \"{test_folder}\"")
        
        print("\nExpected behavior:")
        print("- Script will scan the folder for images and stats.json")
        print("- Upload data to Supabase device_test table")
        print("- Create success.json or failed.json based on result")
        print("- Display upload summary")
        
        # Check what files would be processed
        image_files = []
        stats_file = None
        
        for file in os.listdir(test_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                image_files.append(file)
            elif file.lower() == 'stats.json':
                stats_file = file
        
        print(f"\nFiles that would be processed:")
        print(f"Images: {image_files}")
        print(f"Stats: {stats_file}")
        
        # Show expected database record
        test_date = datetime.now()
        upload_batch = f"batch_{int(datetime.now().timestamp())}"
        
        expected_record = {
            "folder_name": "TestBatch",
            "images": image_files,
            "test_results": {
                "result": [[[99, 104, 203]]],
                "mean": [[99.0, 104.0, 203.0]],
                "standard deviation": [[0.0, 0.0, 0.0]],
                "variance": [[0.0, 0.0, 0.0]],
                "max": [[99, 104, 203]],
                "min": [[99, 104, 203]],
                "range": [[0, 0, 0]]
            },
            "test_date": test_date.isoformat(),
            "test_status": "passed",  # Because stats.json has result data
            "upload_batch": upload_batch,
            "metadata": {
                "upload_timestamp": test_date.isoformat(),
                "total_images": len(image_files),
                "files_processed": os.listdir(test_folder)
            },
            "data_type": "image_analysis"
        }
        
        print(f"\nExpected database record:")
        print(json.dumps(expected_record, indent=2))
        
    except Exception as e:
        print(f"Error during test: {str(e)}")
    
    finally:
        # Clean up test folder
        print(f"\nCleaning up test folder: {test_folder}")
        shutil.rmtree(os.path.dirname(test_folder))
        print("Test folder cleaned up.")

def show_usage_examples():
    """Show usage examples for different scenarios."""
    print("\n" + "="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    examples = [
        {
            "description": "Upload a single batch folder",
            "command": "python upload_to_supabase_simple.py \"data/Batch54\"",
            "expected": "Uploads Batch54 folder with images and stats.json"
        },
        {
            "description": "Upload using HTTP API",
            "command": "python upload_to_supabase_http.py \"data/Batch58\"",
            "expected": "Uploads Batch58 folder using Supabase REST API"
        },
        {
            "description": "Upload folder with spaces in name",
            "command": "python upload_to_supabase_simple.py \"data/My Batch Folder\"",
            "expected": "Uploads folder with spaces in the name"
        },
        {
            "description": "Upload folder with only images (no stats.json)",
            "command": "python upload_to_supabase_simple.py \"data/Batch60\"",
            "expected": "Uploads images only, test_status will be 'pending'"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   Command: {example['command']}")
        print(f"   Expected: {example['expected']}")

def main():
    """Main function to run the test."""
    print("Supabase Upload Script Test")
    print("="*60)
    
    # Show usage examples
    show_usage_examples()
    
    # Run test
    test_upload_script()
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
    print("\nNext steps:")
    print("1. Install PostgreSQL client tools if using simple version")
    print("2. Get Supabase anon key if using HTTP version")
    print("3. Run one of the upload scripts with a real folder")
    print("4. Check the generated success.json or failed.json file")

if __name__ == "__main__":
    main() 