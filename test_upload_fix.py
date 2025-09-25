#!/usr/bin/env python3
"""
Test script for the improved upload system.
This simulates folder creation and tests the upload mechanism.
"""

import os
import sys
import time
import tempfile
import shutil
import json
from PIL import Image
import numpy as np

# Add src to path
sys.path.append('src')

def create_test_folder(base_path, folder_name):
    """Create a test folder with sample images and stats.json"""
    folder_path = os.path.join(base_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # Create sample images
    for i in range(3):
        # Create a simple test image
        image = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
        image_path = os.path.join(folder_path, f"test_image_{i}.jpg")
        image.save(image_path)
    
    # Create stats.json
    stats_data = {
        "test_name": f"test_{folder_name}",
        "result": ["pass", "pass", "fail"],
        "timestamp": time.time(),
        "metadata": {
            "device": "test_device",
            "version": "1.0.0"
        }
    }
    
    with open(os.path.join(folder_path, "stats.json"), 'w') as f:
        json.dump(stats_data, f, indent=2)
    
    print(f"Created test folder: {folder_path}")
    return folder_path

def test_specific_folder_upload(test_folder):
    """Test the specific folder upload mechanism"""
    print(f"\n{'='*60}")
    print("TESTING SPECIFIC FOLDER UPLOAD")
    print(f"{'='*60}")
    
    script_path = "src/upload_manager_rest.py"
    db_path = "test_upload_tracker.db"
    
    # Test with dry run first (we don't want to actually upload during testing)
    command = f"python3 {script_path} data --force-folder \"{test_folder}\" --wait-and-retry --db-path \"{db_path}\" --scan-only"
    print(f"Testing command: {command}")
    
    result = os.system(command)
    print(f"Command result: {result}")
    
    # Test status report
    status_command = f"python3 {script_path} data --status --db-path \"{db_path}\""
    print(f"Status command: {status_command}")
    os.system(status_command)

def test_listener_simulation(test_folder):
    """Simulate what the listener would do"""
    print(f"\n{'='*60}")
    print("SIMULATING LISTENER BEHAVIOR")
    print(f"{'='*60}")
    
    # Import the improved functions
    from listner import wait_for_folder_ready, on_new_folder
    
    print(f"Testing folder readiness for: {test_folder}")
    is_ready = wait_for_folder_ready(test_folder, timeout=10)
    print(f"Folder ready: {is_ready}")
    
    if is_ready:
        print("Folder is ready, would trigger upload")
    else:
        print("Folder not ready within timeout")

def main():
    """Main test function"""
    print("Testing Improved Upload System")
    print("=" * 60)
    
    # Create temporary test environment
    test_base = "test_data"
    os.makedirs(test_base, exist_ok=True)
    
    try:
        # Test 1: Create a test folder
        test_folder = create_test_folder(test_base, f"test_batch_{int(time.time())}")
        
        # Test 2: Check folder readiness
        test_listener_simulation(test_folder)
        
        # Test 3: Test specific folder upload
        test_specific_folder_upload(test_folder)
        
        print(f"\n{'='*60}")
        print("TEST COMPLETED")
        print(f"{'='*60}")
        print(f"Test folder created: {test_folder}")
        print("Review the output above for any issues.")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test database
        if os.path.exists("test_upload_tracker.db"):
            os.remove("test_upload_tracker.db")
            print("Cleaned up test database")

if __name__ == "__main__":
    # Install required packages if needed
    try:
        import PIL
    except ImportError:
        print("Installing required test dependencies...")
        os.system("pip install pillow numpy")
    
    main()
