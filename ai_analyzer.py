import google.generativeai as genai
import json
import re

class AIAnalyzer:
    def __init__(self, api_key):
        """Initialize the AI analyzer with Google Gemini API"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def analyze_text(self, text, document_type='document'):
        """
        Analyze extracted text using Gemini AI
        
        Args:
            text: Extracted OCR text
            document_type: Type of document (receipt, form, etc.)
            
        Returns:
            dict: Structured analysis with entities and insights
        """
        if not text or len(text.strip()) < 10:
            return {
                'success': False,
                'error': 'Text too short for analysis'
            }
        
        try:
            # Create prompt based on document type
            prompt = self._create_analysis_prompt(text, document_type)
            
            # Generate analysis
            response = self.model.generate_content(prompt)
            analysis_text = response.text
            
            # Parse the structured response
            structured_analysis = self._parse_analysis(analysis_text)
            
            return {
                'success': True,
                'analysis': structured_analysis,
                'raw_analysis': analysis_text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_entities(self, text):
        """
        Extract specific entities from text (names, dates, amounts, etc.)
        
        Args:
            text: Text to analyze
            
        Returns:
            dict: Extracted entities
        """
        prompt = f"""
        Extract the following entities from this text:
        - Names (people, organizations)
        - Dates (any date mentioned)
        - Amounts (monetary values)
        - Addresses (physical addresses)
        - Phone numbers
        - Email addresses
        - Other important information
        
        Text:
        {text}
        
        Provide the result as a structured JSON with these keys:
        {{
            "names": [],
            "dates": [],
            "amounts": [],
            "addresses": [],
            "phone_numbers": [],
            "emails": [],
            "other": []
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                return entities
            
            return self._extract_entities_fallback(text)
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return self._extract_entities_fallback(text)
    
    def summarize_document(self, text):
        """
        Generate a concise summary of the document
        
        Args:
            text: Document text
            
        Returns:
            str: Summary
        """
        prompt = f"""
        Provide a concise summary (2-3 sentences) of the following document:
        
        {text}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def classify_and_structure(self, text):
        """
        Classify document and extract structured data
        
        Args:
            text: Document text
            
        Returns:
            dict: Classification and structured data
        """
        prompt = f"""
        Analyze this document and provide:
        1. Document type (receipt, invoice, form, letter, contract, note, other)
        2. Key information extracted in a structured format
        3. Confidence level (high, medium, low)
        
        Document text:
        {text}
        
        Respond in JSON format:
        {{
            "document_type": "",
            "confidence": "",
            "key_info": {{}},
            "suggestions": []
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {
                "document_type": "unknown",
                "confidence": "low",
                "key_info": {},
                "suggestions": []
            }
            
        except Exception as e:
            print(f"Error in classification: {e}")
            return {
                "document_type": "unknown",
                "confidence": "low",
                "key_info": {},
                "suggestions": [],
                "error": str(e)
            }
    
    def _create_analysis_prompt(self, text, document_type):
        """Create tailored prompt based on document type"""
        base_prompt = f"""
        Analyze the following {document_type} and extract structured information.
        
        Document text:
        {text}
        
        """
        
        if document_type == 'receipt':
            return base_prompt + """
            Extract:
            - Store name
            - Date and time
            - Items purchased
            - Subtotal, tax, and total amounts
            - Payment method
            - Receipt number
            
            Format as JSON.
            """
        elif document_type == 'form':
            return base_prompt + """
            Extract:
            - Form title/type
            - All field names and values
            - Dates
            - Signatures (if mentioned)
            
            Format as JSON.
            """
        else:
            return base_prompt + """
            Extract:
            - Main topic/subject
            - Key points
            - Important dates
            - Named entities (people, organizations, locations)
            - Any action items or deadlines
            
            Format as JSON.
            """
    
    def _parse_analysis(self, analysis_text):
        """Parse Gemini response into structured format"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback: return as text analysis
            return {
                "summary": analysis_text,
                "structured": False
            }
        except:
            return {
                "summary": analysis_text,
                "structured": False
            }
    
    def _extract_entities_fallback(self, text):
        """Fallback entity extraction using regex"""
        entities = {
            "names": [],
            "dates": [],
            "amounts": [],
            "addresses": [],
            "phone_numbers": [],
            "emails": [],
            "other": []
        }
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities["emails"] = re.findall(email_pattern, text)
        
        # Extract phone numbers (simple pattern)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        entities["phone_numbers"] = re.findall(phone_pattern, text)
        
        # Extract amounts (currency)
        amount_pattern = r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|INR|Rs)'
        entities["amounts"] = re.findall(amount_pattern, text)
        
        # Extract dates (simple patterns)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
        entities["dates"] = re.findall(date_pattern, text, re.IGNORECASE)
        
        return entities
