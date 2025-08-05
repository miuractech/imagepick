# Supabase Upload Scripts

This repository contains Python scripts to upload folder contents to a Supabase database. The scripts handle multiple images, stats.json files, and create status reports.

## Scripts Overview

### 1. `upload_to_supabase.py` (Complex - Raw PostgreSQL Protocol)
- **Pros**: No external dependencies, works with any Python installation
- **Cons**: Complex implementation, may have edge cases
- **Use case**: When you can't install any packages and need a pure Python solution

### 2. `upload_to_supabase_simple.py` (Recommended - Uses psql)
- **Pros**: Simple, reliable, uses standard PostgreSQL client
- **Cons**: Requires psql command-line tool to be installed
- **Use case**: Most reliable option when psql is available

### 3. `upload_to_supabase_http.py` (HTTP API)
- **Pros**: Uses Supabase REST API, no database client needed
- **Cons**: Requires Supabase anon key configuration
- **Use case**: When you prefer HTTP API over direct database connection

## Prerequisites

### For `upload_to_supabase_simple.py`:
Install PostgreSQL client tools:
- **Windows**: Download from https://www.postgresql.org/download/windows/
- **macOS**: `brew install postgresql`
- **Ubuntu/Debian**: `sudo apt-get install postgresql-client`

### For `upload_to_supabase_http.py`:
1. Get your Supabase anon key:
   - Go to your Supabase project dashboard
   - Navigate to Settings > API
   - Copy the 'anon public' key
   - Replace `your_supabase_anon_key_here` in the script

## Usage

### Basic Usage
```bash
# Using the simple version (recommended)
python upload_to_supabase_simple.py "path/to/your/folder"

# Using the HTTP API version
python upload_to_supabase_http.py "path/to/your/folder"

# Using the complex version
python upload_to_supabase.py "path/to/your/folder"
```

### Example
```bash
python upload_to_supabase_simple.py "data/Batch54"
```

## Folder Structure Expected

The scripts expect folders with the following structure:
```
Batch54/
├── 2025-06-02 16_42_55.jpg
├── 2025-06-02 16_42.pdf
└── stats.json
```

### Supported File Types
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`
- **Data**: `stats.json` (optional)

## Database Schema

The scripts upload to a `device_test` table with the following structure:

```sql
CREATE TABLE device_test (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  folder_name text NOT NULL,
  images text[] DEFAULT '{}',
  device_id uuid,
  device_name text,
  device_type text,
  test_results jsonb,
  test_date timestamp with time zone,
  test_status text CHECK (test_status IN ('pending', 'passed', 'failed', 'incomplete')),
  upload_batch text,
  notes text,
  metadata jsonb DEFAULT '{}',
  data jsonb,
  data_type text
);
```

## Output Files

### Status Files
The scripts create one of two status files in the uploaded folder:

#### `success.json` (when upload succeeds)
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "folder": "Batch54",
  "overall_status": "success",
  "uploaded_files": ["2025-06-02 16_42_55.jpg", "stats.json"],
  "failed_files": [],
  "database_operations": [
    {
      "operation": "insert",
      "folder": "Batch54",
      "status": "success",
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "summary": {
    "total_files_processed": 2,
    "successful_uploads": 2,
    "failed_uploads": 0
  }
}
```

#### `failed.json` (when upload fails)
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "folder": "Batch54",
  "overall_status": "failed",
  "uploaded_files": [],
  "failed_files": ["2025-06-02 16_42_55.jpg", "stats.json"],
  "database_operations": [],
  "summary": {
    "total_files_processed": 2,
    "successful_uploads": 0,
    "failed_uploads": 2
  }
}
```

## Test Status Logic

The scripts automatically determine the test status based on the `stats.json` content:

- **`passed`**: When `stats.json` has `result` array with data
- **`failed`**: When `stats.json` has empty `result` array
- **`pending`**: When no `stats.json` file is present

## Error Handling

The scripts handle various error scenarios:

1. **Folder not found**: Creates `failed.json` with appropriate error message
2. **Database connection issues**: Logs error and creates `failed.json`
3. **File reading errors**: Continues with other files, logs specific errors
4. **Network timeouts**: Retries with appropriate timeout settings

## Configuration

### Connection String
The scripts use this connection string:
```
postgresql://postgres.owcanqgrymdruzdrttfo:dG.-pDR@fF$KZ4#@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

### Supabase URL (for HTTP version)
```
https://owcanqgrymdruzdrttfo.supabase.co
```

## Troubleshooting

### Common Issues

1. **"psql command not found"**
   - Install PostgreSQL client tools (see Prerequisites)

2. **"Connection refused"**
   - Check if the connection string is correct
   - Verify network connectivity to Supabase

3. **"Permission denied"**
   - Ensure you have read access to the folder
   - Check database permissions

4. **"Invalid JSON"**
   - Verify that `stats.json` contains valid JSON
   - Check file encoding (should be UTF-8)

### Debug Mode
Add debug prints by modifying the scripts to include more verbose logging.

## Security Notes

- The connection string contains credentials - keep it secure
- The HTTP version requires the anon key - this is safe to use in client applications
- Consider using environment variables for sensitive data in production

## Performance

- **Small folders** (< 10 files): ~1-2 seconds
- **Medium folders** (10-50 files): ~2-5 seconds  
- **Large folders** (50+ files): ~5-10 seconds

Performance depends on network latency and file sizes.

## Contributing

To improve these scripts:

1. Add better error handling
2. Implement retry logic for failed uploads
3. Add support for more file types
4. Implement batch processing for multiple folders
5. Add progress indicators for large uploads 