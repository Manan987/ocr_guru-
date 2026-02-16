import sqlite3
import json
from datetime import datetime
import csv
import io

class Database:
    def __init__(self, db_path='ocr_records.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                raw_text TEXT,
                structured_data TEXT,
                document_type TEXT,
                confidence_score REAL,
                ai_analysis TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_record(self, filename, raw_text, structured_data=None, 
                     document_type=None, confidence_score=None, ai_analysis=None):
        """Insert a new OCR record into the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        upload_date = datetime.now().isoformat()
        structured_data_json = json.dumps(structured_data) if structured_data else None
        ai_analysis_json = json.dumps(ai_analysis) if ai_analysis else None
        
        cursor.execute('''
            INSERT INTO records (filename, upload_date, raw_text, structured_data, 
                               document_type, confidence_score, ai_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (filename, upload_date, raw_text, structured_data_json, 
              document_type, confidence_score, ai_analysis_json))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_record(self, record_id):
        """Retrieve a specific record by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM records WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_records(self, limit=100, offset=0):
        """Retrieve all records with pagination"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM records ORDER BY upload_date DESC LIMIT ? OFFSET ?', 
                      (limit, offset))
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def search_records(self, query):
        """Search records by text content"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_query = f'%{query}%'
        cursor.execute('''
            SELECT * FROM records 
            WHERE raw_text LIKE ? OR filename LIKE ?
            ORDER BY upload_date DESC
        ''', (search_query, search_query))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def delete_record(self, record_id):
        """Delete a record by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM records WHERE id = ?', (record_id,))
        affected_rows = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected_rows > 0
    
    def export_to_json(self):
        """Export all records as JSON"""
        records = self.get_all_records(limit=10000)
        return json.dumps(records, indent=2)
    
    def export_to_csv(self):
        """Export all records as CSV"""
        records = self.get_all_records(limit=10000)
        
        if not records:
            return ""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        
        return output.getvalue()
    
    def _row_to_dict(self, row):
        """Convert database row to dictionary"""
        record = dict(row)
        
        # Parse JSON fields
        if record.get('structured_data'):
            try:
                record['structured_data'] = json.loads(record['structured_data'])
            except:
                pass
        
        if record.get('ai_analysis'):
            try:
                record['ai_analysis'] = json.loads(record['ai_analysis'])
            except:
                pass
        
        return record
    
    def get_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM records')
        total_records = cursor.fetchone()[0]
        
        cursor.execute('SELECT document_type, COUNT(*) FROM records GROUP BY document_type')
        by_type = dict(cursor.fetchall())
        
        cursor.execute('SELECT AVG(confidence_score) FROM records WHERE confidence_score IS NOT NULL')
        avg_confidence = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_records': total_records,
            'by_document_type': by_type,
            'average_confidence': round(avg_confidence, 2) if avg_confidence else 0
        }
