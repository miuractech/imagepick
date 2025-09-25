import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Path to the parent directory you want to monitor
WATCHED_DIR = "/home/rpi/gui/data"

def wait_for_folder_ready(folder_path, timeout=30, check_interval=0.5):
    """
    Wait for folder to be ready (unlocked, stable, and files accessible)
    Returns True if folder is ready, False if timeout
    """
    start_time = time.time()
    last_file_count = None
    last_mod_time = None
    stable_duration = 0
    required_stable_time = 5  # Wait for 5 seconds of stability (increased for safety)
    
    while time.time() - start_time < timeout:
        try:
            # Check if folder exists and is accessible
            if not os.path.exists(folder_path):
                time.sleep(check_interval)
                continue
                
            # Try to list folder contents and access files
            try:
                files = os.listdir(folder_path)
                
                # Try to access each file to ensure they're not locked
                accessible_files = []
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    try:
                        # Try to get file stats to check if accessible
                        os.stat(file_path)
                        # For regular files, try to open briefly to ensure not locked
                        if os.path.isfile(file_path):
                            with open(file_path, 'rb') as f:
                                f.read(1)  # Read just 1 byte to test access
                        accessible_files.append(file)
                    except (PermissionError, OSError, IOError):
                        print(f"File {file_path} not yet accessible, waiting...")
                        break
                else:
                    # All files are accessible
                    current_file_count = len(accessible_files)
                    current_mod_time = os.path.getmtime(folder_path)
                    
                    # Check for stability (no new files and no folder modifications)
                    if (last_file_count is not None and 
                        last_mod_time is not None and
                        current_file_count == last_file_count and 
                        current_mod_time == last_mod_time):
                        
                        stable_duration += check_interval
                        if stable_duration >= required_stable_time:
                            print(f"Folder {folder_path} is ready with {current_file_count} accessible files after {time.time() - start_time:.1f}s")
                            return True
                    else:
                        # Reset stability counter if changes detected
                        last_file_count = current_file_count
                        last_mod_time = current_mod_time
                        stable_duration = 0
                        if current_file_count > 0:
                            print(f"Folder {folder_path} has {current_file_count} accessible files, checking stability...")
                        else:
                            print(f"Folder {folder_path} exists but no files yet...")
                
            except PermissionError:
                print(f"Folder {folder_path} is locked, waiting...")
            except OSError:
                print(f"Folder {folder_path} is busy, waiting...")
                
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"Error checking folder {folder_path}: {e}")
            time.sleep(check_interval)
    
    print(f"Timeout waiting for folder {folder_path} to be ready")
    return False

# This is the script or function to call when a new folder is created
def on_new_folder(folder_path):
    print(f"New folder created: {folder_path}")
    
    # Wait for folder to be ready before processing
    if wait_for_folder_ready(folder_path):
        print(f"Processing folder: {folder_path}")
        script_path = "/opt/imagepick/src/upload_manager_rest.py"
        db_path = "/opt/imagepick/upload_tracker.db"
        
        # Use the new force-folder feature to target this specific folder
        command = f"python3 {script_path} \"/home/rpi/gui/data\" --force-folder \"{folder_path}\" --wait-and-retry --db-path \"{db_path}\""
        print(f"Executing: {command}")
        
        result = os.system(command)
        if result == 0:
            print(f"✅ Successfully processed folder: {folder_path}")
        else:
            print(f"❌ Failed to process folder: {folder_path} (exit code: {result})")
            
            # Fallback: try a general scan in case the specific folder approach failed
            print("Attempting fallback with general scan...")
            fallback_command = f"python3 {script_path} \"/home/rpi/gui/data\" --db-path \"{db_path}\""
            fallback_result = os.system(fallback_command)
            if fallback_result == 0:
                print(f"✅ Fallback scan completed successfully")
            else:
                print(f"❌ Fallback scan also failed (exit code: {fallback_result})")
    else:
        print(f"Skipping folder {folder_path} - not ready within timeout")
        
        # Even if folder readiness check fails, try to force upload it anyway
        print(f"Attempting force upload anyway for: {folder_path}")
        script_path = "/opt/imagepick/src/upload_manager_rest.py"
        db_path = "/opt/imagepick/upload_tracker.db"
        command = f"python3 {script_path} \"/home/rpi/gui/data\" --force-folder \"{folder_path}\" --db-path \"{db_path}\""
        result = os.system(command)
        if result == 0:
            print(f"✅ Force upload succeeded: {folder_path}")
        else:
            print(f"❌ Force upload failed: {folder_path}")

class FolderCreationHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            on_new_folder(event.src_path)

if __name__ == "__main__":
    event_handler = FolderCreationHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCHED_DIR, recursive=False)
    observer.start()
    print(f"Watching for new folders in: {WATCHED_DIR}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
