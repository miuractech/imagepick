import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Path to the parent directory you want to monitor
WATCHED_DIR = "/home/rpi/gui/data"

def wait_for_pdf_file(folder_path, timeout=60, check_interval=0.5):
    """
    Wait for a PDF file to appear in the folder
    Returns True if PDF file found, False if timeout (1 minute)
    """
    start_time = time.time()
    last_file_count = None
    last_mod_time = None
    stable_duration = 0
    required_stable_time = 3  # Wait for 3 seconds of stability after PDF appears
    pdf_found = False
    
    print(f"Waiting for PDF file in folder: {folder_path} (timeout: {timeout}s)")
    
    while time.time() - start_time < timeout:
        try:
            # Check if folder exists and is accessible
            if not os.path.exists(folder_path):
                time.sleep(check_interval)
                continue
                
            # Try to list folder contents and look for PDF files
            try:
                files = os.listdir(folder_path)
                
                # Check for PDF files and verify they're accessible
                accessible_files = []
                pdf_files = []
                
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    try:
                        # Try to get file stats to check if accessible
                        os.stat(file_path)
                        # For regular files, try to open briefly to ensure not locked
                        if os.path.isfile(file_path):
                            with open(file_path, 'rb') as f:
                                f.read(1)  # Read just 1 byte to test access
                            
                            # Check if this is a PDF file
                            if file.lower().endswith('.pdf'):
                                pdf_files.append(file)
                                pdf_found = True
                        
                        accessible_files.append(file)
                    except (PermissionError, OSError, IOError):
                        print(f"File {file_path} not yet accessible, waiting...")
                        break
                else:
                    # All files are accessible
                    current_file_count = len(accessible_files)
                    current_mod_time = os.path.getmtime(folder_path)
                    
                    if pdf_found:
                        print(f"PDF file(s) found: {pdf_files}")
                        
                        # Check for stability (no new files and no folder modifications)
                        if (last_file_count is not None and 
                            last_mod_time is not None and
                            current_file_count == last_file_count and 
                            current_mod_time == last_mod_time):
                            
                            stable_duration += check_interval
                            if stable_duration >= required_stable_time:
                                print(f"Folder {folder_path} is ready with PDF file(s) {pdf_files} after {time.time() - start_time:.1f}s")
                                return True
                        else:
                            # Reset stability counter if changes detected
                            last_file_count = current_file_count
                            last_mod_time = current_mod_time
                            stable_duration = 0
                            print(f"Folder {folder_path} has {len(pdf_files)} PDF file(s), checking stability...")
                    else:
                        print(f"Folder {folder_path} has {current_file_count} files but no PDF yet, waiting...")
                        # Reset counters when no PDF found
                        last_file_count = current_file_count
                        last_mod_time = current_mod_time
                        stable_duration = 0
                
            except PermissionError:
                print(f"Folder {folder_path} is locked, waiting...")
            except OSError:
                print(f"Folder {folder_path} is busy, waiting...")
                
            time.sleep(check_interval)
            
        except Exception as e:
            print(f"Error checking folder {folder_path}: {e}")
            time.sleep(check_interval)
    
    if pdf_found:
        print(f"Timeout waiting for folder {folder_path} to be stable (PDF found but folder still changing)")
    else:
        print(f"Timeout waiting for PDF file in folder {folder_path} (no PDF file found within {timeout} seconds)")
    return False

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
    
    # Wait specifically for PDF file to appear in the folder (1 minute timeout)
    if wait_for_pdf_file(folder_path, timeout=60):
        print(f"PDF file found in folder, proceeding with upload processing...")
        
        # After PDF is found, ensure folder is stable
        if wait_for_folder_ready(folder_path, timeout=10):
            print(f"Folder ready with PDF, processing all folders in base directory...")
            script_path = "/opt/imagepick/src/upload_manager_rest.py"
            db_path = "/opt/imagepick/upload_tracker.db"
            
            # Process all folders (with improved scanning that includes recent folders)
            command = f"python3 {script_path} \"/home/rpi/gui/data\" --db-path \"{db_path}\""
            print(f"Executing: {command}")
            
            result = os.system(command)
            if result == 0:
                print(f"✅ Successfully processed all folders (triggered by: {folder_path})")
            else:
                print(f"❌ Failed to process folders (exit code: {result})")
                
                # Retry once more after a short delay
                print("Retrying after 5 seconds...")
                time.sleep(5)
                retry_result = os.system(command)
                if retry_result == 0:
                    print(f"✅ Retry successful")
                else:
                    print(f"❌ Retry also failed (exit code: {retry_result})")
        else:
            print(f"PDF found but folder {folder_path} not stable, attempting upload anyway...")
            script_path = "/opt/imagepick/src/upload_manager_rest.py"
            db_path = "/opt/imagepick/upload_tracker.db"
            command = f"python3 {script_path} \"/home/rpi/gui/data\" --db-path \"{db_path}\""
            result = os.system(command)
            if result == 0:
                print(f"✅ Upload processing completed despite instability")
            else:
                print(f"❌ Upload processing failed: {folder_path}")
    else:
        print(f"❌ No PDF file found in folder {folder_path} within 1 minute, ignoring this folder")
        print(f"Folder {folder_path} will be skipped as no PDF file appeared")

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
