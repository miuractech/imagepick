# Supabase Upload System - REST API Version

A comprehensive system for efficiently uploading millions of folders to Supabase using the REST API instead of direct database connections. **Now includes proper image file uploads to Supabase Storage!**

## 🚀 Key Advantages

### ✅ **No External Dependencies**
- **No PostgreSQL Client**: No need to install `psql` or PostgreSQL client tools
- **Built-in Python Modules**: Uses only `urllib`, `ssl`, `json`, and other built-in modules
- **Universal Compatibility**: Works on any system with Python 3.7+

### ✅ **REST API Benefits**
- **Simpler Setup**: Just need Supabase URL and anon key
- **Better Error Handling**: HTTP status codes provide clear error information
- **Rate Limiting**: Built-in protection against overwhelming the API
- **Firewall Friendly**: Uses standard HTTPS ports

### ✅ **Proper Image Upload**
- **Supabase Storage**: Images are uploaded to Supabase Storage buckets
- **Public URLs**: Images get public URLs that can be accessed directly
- **Organized Structure**: Images are stored in `images/{device_id}/{folder_name}/{filename}` structure
- **Multi-Device Support**: Each device's images are isolated in their own directory
- **Database References**: Database stores image URLs instead of just filenames
- **Filename Safety**: Handles filenames with spaces and special characters using URL encoding

### ✅ **Device Information Tracking**
- **Device ID**: Unique identifier for each device
- **Device Name**: Human-readable device name for easy identification
- **Device Type**: Category/type of device for classification
- **Metadata Integration**: Device info included in both database records and metadata
- **Storage Isolation**: Each device's images are stored in separate directories for organization

## 📁 File Structure

```
src/
├── upload_manager_rest.py    # Main upload manager (REST API)
├── quick_upload_rest.py      # Simple script for single folder uploads
├── config.py                 # Configuration settings
├── upload_tracker.db         # SQLite database (created automatically)
└── README_rest_api.md        # This file
```

## 🛠️ Setup

### Prerequisites
1. **Python 3.7+**
2. **Supabase Anon Key**: Get this from your Supabase project settings
3. **Storage Permissions**: Ensure your anon key has storage permissions

### Configuration
Edit `config.py` to set your Supabase credentials and device information:

```python
# REST API settings
SUPABASE_URL = "https://owcanqgrymdruzdrttfo.supabase.co"
SUPABASE_ANON_KEY = "your_actual_anon_key_here"

# Device information
DEVICE_ID = "device_001"  # Unique device identifier
DEVICE_NAME = "Test Device"  # Human-readable device name
DEVICE_TYPE = "image_analyzer"  # Type/category of device
```

### Storage Setup
The system will automatically:
1. Create an `images` bucket in Supabase Storage
2. Make the bucket public for easy access
3. Upload images to `images/{device_id}/{folder_name}/{filename}` structure for multi-device support

## 📖 Usage

### 1. **Quick Upload (Single Folder)**
For uploading individual folders quickly:

```bash
# Using config.py defaults
python quick_upload_rest.py "data/Batch54"

# With custom URL
python quick_upload_rest.py "data/Batch54" "https://owcanqgrymdruzdrttfo.supabase.co"

# With custom URL and key
python quick_upload_rest.py "data/Batch54" "https://owcanqgrymdruzdrttfo.supabase.co" "your_anon_key"
```

**Output:**
```
🚀 Quick Upload Script (REST API)
==================================================
📁 Uploading folder: Batch54
📸 Found 1 image files
📊 Found stats.json file
  📤 Uploading image: 2025-06-02 16_42_55.jpg
  ✅ Image uploaded: https://owcanqgrymdruzdrttfo.supabase.co/storage/v1/object/public/images/device_001/Batch54/2025-06-02%2016_42_55.jpg
✅ Loaded stats.json successfully
🏷️  Test status: passed
🚀 Executing REST API request...
✅ Successfully uploaded folder: Batch54
📄 Created success.json in Batch54
==================================================
✅ Upload completed successfully!
```

**Note:** Filenames with spaces and special characters are automatically URL-encoded for safe storage and access.

### 2. **Advanced Upload Manager (Millions of Folders)**

#### **Initial Scan and Upload**
```bash
# Scan all folders and upload them (uses config.py defaults)
python upload_manager_rest.py "data/"

# With custom batch size
python upload_manager_rest.py "data/" --batch-size 100

# With custom retry limit
python upload_manager_rest.py "data/" --max-retries 5

# With custom supabase key
python upload_manager_rest.py "data/" --supabase-key "your_anon_key"
```

#### **Scan Only (No Upload)**
```bash
# Just scan and record folders without uploading
python upload_manager_rest.py "data/" --scan-only
```

#### **Status Report**
```bash
# View detailed status report
python upload_manager_rest.py "data/" --status
```

#### **Resume Failed Uploads**
```bash
# Resume processing failed folders
python upload_manager_rest.py "data/" --max-retries 5
```

## 🔧 Command Line Options

### **upload_manager_rest.py**
```bash
python upload_manager_rest.py <base_path> [options]

Required:
  None (uses config.py defaults)

Optional:
  --supabase-key KEY    Supabase anon key (default: from config.py)
  --scan-only          Only scan and record folders, don't upload
  --batch-size INT     Number of folders per batch (default: 50)
  --max-retries INT    Maximum retry attempts (default: 3)
  --db-path PATH       SQLite database path (default: upload_tracker.db)
  --status             Show status report and exit
  --supabase-url URL   Supabase URL (default: from config.py)
```

### **quick_upload_rest.py**
```bash
python quick_upload_rest.py <folder_path> [supabase_url] [supabase_key]
```

## 🔄 How It Works

### **1. Image Upload Process**
1. **Scan Folder**: Identifies image files and stats.json
2. **Create Storage Bucket**: Creates `images` bucket if it doesn't exist
3. **Upload Images**: Uploads each image to `images/{device_id}/{folder_name}/{filename}`
4. **Generate URLs**: Creates public URLs for uploaded images
5. **Database Insert**: Stores image URLs in the database

### **2. REST API Communication**
- Uses `urllib.request` to make HTTP requests
- Sends JSON data to `https://your-project.supabase.co/rest/v1/device_test`
- Handles authentication via `apikey` and `Authorization` headers

### **3. Data Format**
The REST API expects data in this format:
```json
{
  "folder_name": "Batch54",
  "device_id": "device_001",
  "images": [
    "https://your-project.supabase.co/storage/v1/object/public/images/device_001/Batch54/image1.jpg",
    "https://your-project.supabase.co/storage/v1/object/public/images/device_001/Batch54/image%20with%20spaces.jpg"
  ],
  "test_results": {"result": [...]},
  "test_date": "2024-01-15T14:30:22",
  "test_status": "passed",
  "upload_batch": "batch_1705315822",
  "metadata": {
    "upload_timestamp": "2024-01-15T14:30:22",
    "total_images": 2,
    "files_processed": ["image1.jpg", "image2.jpg", "stats.json"],
    "image_urls": [...],
    "device_id": "device_001",
    "device_name": "Test Device",
    "device_type": "image_analyzer"
  },
  "data_type": "image_analysis"
}
```

### **4. Error Handling**
- HTTP status codes provide clear error information
- Automatic retry logic for failed requests
- Detailed error logging in SQLite database
- Graceful handling of storage upload failures

## 🛡️ Security

### **Authentication**
- Uses Supabase anon key for authentication
- All requests are made over HTTPS
- SSL certificate verification can be disabled for testing

### **Storage Security**
- Images are stored in public buckets for easy access
- URLs are generated with proper authentication
- Storage permissions are handled via Supabase policies

### **Rate Limiting**
- Built-in delays between requests to respect API limits
- Configurable batch sizes to control request frequency
- Automatic retry with exponential backoff

## 📊 Performance

### **Scalability**
- **1,000 folders**: ~5-6 minutes (includes image uploads)
- **10,000 folders**: ~30-40 minutes (includes image uploads)
- **100,000 folders**: ~4-5 hours (includes image uploads)
- **1,000,000+ folders**: ~3-4 days (with proper batch sizing)

### **Memory Usage**
- **Low Memory**: Uses streaming file operations
- **Efficient Hashing**: Only hashes file metadata, not content
- **Batch Processing**: Processes folders in chunks to manage memory

### **Storage Optimization**
- Images are uploaded individually to avoid memory issues
- Progress tracking for each image upload
- Automatic retry for failed image uploads

## 🚨 Troubleshooting

### **Common Issues**

1. **"HTTP 401 Unauthorized"**
   ```bash
   # Check your anon key
   # Make sure it's correct and not expired
   ```

2. **"HTTP 403 Forbidden"**
   ```bash
   # Check table permissions in Supabase
   # Ensure your anon key has INSERT permissions on device_test table
   # Check storage permissions for image uploads
   ```

3. **"Storage upload error"**
   ```bash
   # Check storage bucket permissions
   # Ensure anon key has storage write permissions
   # Check if bucket exists and is public
   ```

4. **"HTTP 429 Too Many Requests"**
   ```bash
   # Reduce batch size
   python upload_manager_rest.py "data/" --batch-size 25
   ```

5. **"Connection timeout"**
   ```bash
   # Check network connectivity
   # Increase timeout in config.py
   UPLOAD_TIMEOUT_SECONDS = 60
   ```

### **Debugging**

1. **Check API Response**
   ```bash
   # The scripts will show HTTP status codes and error messages
   ```

2. **Check Storage Bucket**
   ```bash
   # Verify the 'images' bucket exists in Supabase Storage
   # Check bucket permissions and policies
   ```

3. **Database Queries**
   ```bash
   # Check failed folders
   sqlite3 upload_tracker.db "SELECT folder_name, error_message FROM folder_status WHERE upload_status='failed';"
   ```

4. **Test Single Upload**
   ```bash
   # Test with a single folder first (uses config.py defaults)
   python quick_upload_rest.py "data/Batch54"
   ```

## 🔄 Migration from psql Version

### **From psql to REST API**
If you were using the psql version:

1. **Backup your data**
2. **Update config.py** with your Supabase URL and anon key
3. **Run initial scan**:
   ```bash
   python upload_manager_rest.py "data/" --scan-only
   ```
4. **Process all folders**:
   ```bash
   python upload_manager_rest.py "data/"
   ```

### **Data Compatibility**
- Same SQLite tracking database format
- Same folder structure and file processing
- Same success.json/failed.json output format
- **New**: Images are now properly uploaded to storage with URLs

## 📞 Support

### **Getting Help**
1. Check the status report: `python upload_manager_rest.py "data/" --status`
2. Review error messages in the database
3. Check console output for HTTP status codes
4. Verify storage bucket permissions

### **Common Commands**
```bash
# Quick status check
python upload_manager_rest.py "data/" --status

# Resume failed uploads
python upload_manager_rest.py "data/" --max-retries 5

# Process in smaller batches
python upload_manager_rest.py "data/" --batch-size 25

# Quick single folder upload
python quick_upload_rest.py "data/Batch54"
```

This REST API version now properly uploads images to Supabase Storage and provides the same powerful features as the psql version but with simpler setup and better compatibility across different environments. 