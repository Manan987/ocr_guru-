from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

from ocr_processor import OCRProcessor
from ai_analyzer import AIAnalyzer
from database import Database

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyBwXKt4QJfqec2PeYos4BqXw9e7OFlrChM')
ocr_processor = OCRProcessor(API_KEY)
ai_analyzer = AIAnalyzer(API_KEY)
database = Database()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle single file upload and OCR processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Preprocess image
        ocr_processor.preprocess_image(filepath)
        
        # Perform OCR
        ocr_result = ocr_processor.process_image(filepath)
        
        if not ocr_result['success']:
            return jsonify(ocr_result), 500
        
        # Analyze with AI
        ai_result = ai_analyzer.analyze_text(
            ocr_result['raw_text'], 
            ocr_result['document_type']
        )
        
        # Extract entities
        entities = ai_analyzer.extract_entities(ocr_result['raw_text'])
        
        # Save to database
        record_id = database.insert_record(
            filename=filename,
            raw_text=ocr_result['raw_text'],
            structured_data=entities,
            document_type=ocr_result['document_type'],
            confidence_score=ocr_result['confidence_score'],
            ai_analysis=ai_result.get('analysis') if ai_result['success'] else None
        )
        
        return jsonify({
            'success': True,
            'record_id': record_id,
            'filename': filename,
            'ocr_result': ocr_result,
            'ai_analysis': ai_result,
            'entities': entities
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/batch-upload', methods=['POST'])
def batch_upload():
    """Handle batch file upload and processing"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        results = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Process image
                ocr_processor.preprocess_image(filepath)
                ocr_result = ocr_processor.process_image(filepath)
                
                if ocr_result['success']:
                    # AI analysis
                    entities = ai_analyzer.extract_entities(ocr_result['raw_text'])
                    ai_result = ai_analyzer.analyze_text(
                        ocr_result['raw_text'],
                        ocr_result['document_type']
                    )
                    
                    # Save to database
                    record_id = database.insert_record(
                        filename=filename,
                        raw_text=ocr_result['raw_text'],
                        structured_data=entities,
                        document_type=ocr_result['document_type'],
                        confidence_score=ocr_result['confidence_score'],
                        ai_analysis=ai_result.get('analysis') if ai_result['success'] else None
                    )
                    
                    results.append({
                        'success': True,
                        'filename': filename,
                        'record_id': record_id,
                        'document_type': ocr_result['document_type'],
                        'confidence': ocr_result['confidence_score']
                    })
                else:
                    results.append({
                        'success': False,
                        'filename': filename,
                        'error': ocr_result.get('error', 'Processing failed')
                    })
        
        return jsonify({
            'success': True,
            'total': len(files),
            'processed': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/records', methods=['GET'])
def get_records():
    """Get all records with pagination"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '')
        
        if search:
            records = database.search_records(search)
        else:
            records = database.get_all_records(limit, offset)
        
        return jsonify({
            'success': True,
            'records': records,
            'count': len(records)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/records/<int:record_id>', methods=['GET'])
def get_record(record_id):
    """Get a specific record by ID"""
    try:
        record = database.get_record(record_id)
        
        if record:
            return jsonify({
                'success': True,
                'record': record
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Record not found'
            }), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/records/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """Delete a record"""
    try:
        success = database.delete_record(record_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Record deleted'})
        else:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    """Analyze text using Gemini AI"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        document_type = data.get('document_type', 'document')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Perform AI analysis
        result = ai_analyzer.analyze_text(text, document_type)
        entities = ai_analyzer.extract_entities(text)
        summary = ai_analyzer.summarize_document(text)
        
        return jsonify({
            'success': True,
            'analysis': result,
            'entities': entities,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_records():
    """Export records as JSON or CSV"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'json':
            data = database.export_to_json()
            return app.response_class(
                response=data,
                mimetype='application/json',
                headers={'Content-Disposition': 'attachment;filename=ocr_records.json'}
            )
        elif format_type == 'csv':
            data = database.export_to_csv()
            return app.response_class(
                response=data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=ocr_records.csv'}
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid format'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        stats = database.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 OCR Server starting...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"🔑 API Key configured: {API_KEY[:10]}...")
    print("🌐 Server running at http://localhost:5002")
    app.run(debug=True, host='0.0.0.0', port=5002)
