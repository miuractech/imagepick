#!/usr/bin/env python3
import datetime
import argparse
import os
import sys

def create_timestamped_file(prefix="file", ext="txt", dir_path="."):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{ext}"
    full_path = os.path.join(dir_path, filename)
    with open(full_path, "w") as f:
        pass
    return full_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a timestamped file.")
    parser.add_argument("--prefix", default="file", help="Prefix for the filename")
    parser.add_argument("--ext", default="txt", help="File extension")
    parser.add_argument("--dir", default=".", help="Directory to create the file in")
    args = parser.parse_args()

    try:
        path = create_timestamped_file(args.prefix, args.ext, args.dir)
        print(f"Created file: {path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
