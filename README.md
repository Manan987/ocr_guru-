# OCR Document Scanner 📄

AI-powered document text extraction using Google Vision OCR and Gemini AI for intelligent text analysis.

## Features

✨ **Comprehensive OCR Solution**
- 🔍 **Google Vision OCR** - Accurate text extraction from images
- 🤖 **Gemini AI Analysis** - Intelligent document structuring and entity extraction
- 📤 **Drag & Drop Upload** - Modern, intuitive file upload interface
- 📦 **Batch Processing** - Process multiple documents simultaneously
- 💾 **Database Storage** - SQLite database for storing all records
- 📊 **Export Functionality** - Export records as JSON or CSV
- 🔎 **Search & Filter** - Find records quickly by content or type
- 📱 **Responsive Design** - Works perfectly on all devices

## Supported Document Types

- ✅ Receipts & Invoices
- ✅ Forms & Applications
- ✅ Letters & Documents
- ✅ Handwritten Notes
- ✅ Business Cards
- ✅ Any text-containing image

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Cloud API Key with Vision API enabled

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd "/Users/nischalvarshney/Documents/ocr "
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure API Key** (already done in `.env` file)
   ```
   GOOGLE_API_KEY=AIzaSyBwXKt4QJfqec2PeYos4BqXw9e7OFlrChM
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open your browser**
   ```
   http://localhost:5000
   ```

## Usage

### Upload Single Document
1. Click the upload zone or drag & drop an image
2. The system automatically processes the image
3. View extracted text and AI analysis in the results

### Batch Upload
1. Select or drag multiple images at once
2. All files are processed concurrently
3. View all results in the records grid

### Search & Filter
- Use the search box to find specific records
- Click filter pills to view documents by type
- Click any record card to see full details

### Export Data
- Click "Export JSON" for JSON format
- Click "Export CSV" for spreadsheet format
- All records are included in the export

## API Endpoints

### Upload Single File
```
POST /api/upload
Content-Type: multipart/form-data
Body: file (image file)
```

### Batch Upload
```
POST /api/batch-upload
Content-Type: multipart/form-data
Body: files[] (multiple image files)
```

### Get All Records
```
GET /api/records?limit=100&offset=0&search=query
```

### Get Single Record
```
GET /api/records/{id}
```

### Delete Record
```
DELETE /api/records/{id}
```

### Analyze Text
```
POST /api/analyze
Content-Type: application/json
Body: {"text": "...", "document_type": "receipt"}
```

### Export Records
```
GET /api/export?format=json
GET /api/export?format=csv
```

### Get Statistics
```
GET /api/stats
```

## Project Structure

```
ocr/
├── app.py                    # Flask server & REST API
├── ocr_processor.py          # Google Vision OCR integration
├── ai_analyzer.py            # Gemini AI text analysis
├── database.py               # SQLite database operations
├── requirements.txt          # Python dependencies
├── .env                      # API keys (git-ignored)
├── .gitignore               # Git ignore rules
├── README.md                 # This file
├── uploads/                  # Uploaded images (auto-created)
├── static/
│   ├── index.html           # Main web interface
│   ├── css/
│   │   └── styles.css       # Modern UI styles
│   └── js/
│       └── app.js           # Frontend JavaScript
└── ocr_records.db           # SQLite database (auto-created)
```

## Technology Stack

- **Backend**: Python 3, Flask
- **OCR**: Google Cloud Vision API
- **AI**: Google Gemini 2.0 Flash
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Custom glassmorphism design with dark mode

## Features in Detail

### Google Vision OCR
- Detects and extracts text from images
- Provides confidence scores for accuracy
- Supports multiple languages
- Handles rotated and skewed text
- Works with handwritten text

### Gemini AI Analysis
- Automatically classifies document types
- Extracts entities (names, dates, amounts, addresses, emails, phone numbers)
- Generates document summaries
- Structures unformatted text
- Provides intelligent insights

### Database Storage
- Stores all extracted records
- Maintains upload history
- Enables search and filtering
- Supports data export
- Tracks confidence scores

## Security

- 🔐 API keys stored in `.env` file (git-ignored)
- 🚫 Files not committed to version control
- 🛡️ Input validation on all uploads
- 📏 File size limits enforced
- ✅ Allowed file type restrictions

## Troubleshooting

### Import Error: google.cloud.vision
The Google Vision API client uses API keys directly - no service account needed.

### Upload Fails
- Check file format (supported: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP)
- Verify file size is under 10MB
- Ensure API key is valid

### No Text Extracted
- Image quality may be too low
- Try preprocessing (rotate, enhance contrast)
- Verify text is clearly visible in the image

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use this project for your own purposes.

## Author

Built with ❤️ using Google AI technologies

---

**Need Help?** Check the troubleshooting section or review the API documentation above.
