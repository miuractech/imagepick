import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Path to the parent directory you want to monitor
WATCHED_DIR = "/home/rpi/gui/data"

# This is the script or function to call when a new folder is created
def on_new_folder(folder_path):
    print(f"New folder created: {folder_path}")
    # You can run your actual script here
    script_path = "/opt/imagepick/src/upload_manager_rest.py"
    os.system(f"python3 {script_path} \"/home/rpi/gui/data\"")
    # Or call a function directly

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
