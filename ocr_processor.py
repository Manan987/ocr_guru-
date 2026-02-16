import os
import io
from PIL import Image
from google.cloud import vision
import google.generativeai as genai

class OCRProcessor:
    def __init__(self, api_key):
        """Initialize the OCR processor with Google Vision API"""
        self.api_key = api_key
        
        # Configure Google Vision client
        os.environ['GOOGLE_APPLICATION_CREDENTIALS_JSON'] = f'{{"type": "service_account", "project_id": "ocr-project"}}'
        
        # Initialize Vision client with API key
        self.client = vision.ImageAnnotatorClient(
            client_options={"api_key": api_key}
        )
    
    def process_image(self, image_path):
        """
        Process a single image and extract text using Google Vision OCR
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict: OCR results with text, confidence, and metadata
        """
        try:
            # Read and preprocess image
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f'Vision API Error: {response.error.message}')
            
            # Extract full text
            full_text = texts[0].description if texts else ""
            
            # Calculate average confidence
            confidence = self._calculate_confidence(texts)
            
            # Detect document features
            document_response = self.client.document_text_detection(image=image)
            document = document_response.full_text_annotation
            
            # Extract structured information
            structured_data = self._extract_structured_data(texts, document)
            
            # Classify document type
            document_type = self._classify_document(full_text)
            
            return {
                'success': True,
                'raw_text': full_text,
                'confidence_score': confidence,
                'document_type': document_type,
                'structured_data': structured_data,
                'word_count': len(full_text.split()) if full_text else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'raw_text': '',
                'confidence_score': 0,
                'document_type': 'unknown',
                'structured_data': {}
            }
    
    def process_batch(self, image_paths):
        """
        Process multiple images in batch
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            list: Results for each image
        """
        results = []
        for image_path in image_paths:
            result = self.process_image(image_path)
            result['filename'] = os.path.basename(image_path)
            results.append(result)
        
        return results
    
    def _calculate_confidence(self, texts):
        """Calculate average confidence score from OCR results"""
        if not texts or len(texts) <= 1:
            return 0.0
        
        # Skip the first element (full text) and calculate average
        total_confidence = 0
        count = 0
        
        for text in texts[1:]:  # Skip first element (full text)
            if hasattr(text, 'confidence'):
                total_confidence += text.confidence
                count += 1
        
        if count == 0:
            return 0.85  # Default confidence if not available
        
        return round(total_confidence / count, 3)
    
    def _extract_structured_data(self, texts, document):
        """Extract structured information like entities from text"""
        structured = {
            'blocks': [],
            'paragraphs': [],
            'words': []
        }
        
        if document and hasattr(document, 'pages'):
            for page in document.pages:
                for block in page.blocks:
                    block_text = ""
                    for paragraph in block.paragraphs:
                        para_text = ""
                        for word in paragraph.words:
                            word_text = "".join([symbol.text for symbol in word.symbols])
                            para_text += word_text + " "
                            structured['words'].append(word_text)
                        
                        structured['paragraphs'].append(para_text.strip())
                        block_text += para_text
                    
                    if block_text.strip():
                        structured['blocks'].append(block_text.strip())
        
        return structured
    
    def _classify_document(self, text):
        """Classify document type based on content"""
        text_lower = text.lower()
        
        # Simple classification logic
        if any(keyword in text_lower for keyword in ['receipt', 'total', 'tax', 'payment', 'invoice']):
            return 'receipt'
        elif any(keyword in text_lower for keyword in ['form', 'application', 'signature', 'date of birth']):
            return 'form'
        elif any(keyword in text_lower for keyword in ['letter', 'dear', 'sincerely', 'regards']):
            return 'letter'
        elif len(text.split()) < 50:
            return 'note'
        else:
            return 'document'
    
    def preprocess_image(self, image_path, output_path=None):
        """
        Preprocess image for better OCR results
        
        Args:
            image_path: Input image path
            output_path: Output path (optional)
            
        Returns:
            str: Path to processed image
        """
        try:
            img = Image.open(image_path)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 4096x4096 for Vision API)
            max_size = 4096
            if img.width > max_size or img.height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save processed image
            if output_path is None:
                output_path = image_path
            
            img.save(output_path, quality=95)
            return output_path
            
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return image_path
