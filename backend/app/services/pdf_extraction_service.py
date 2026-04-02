import re
from datetime import datetime
from typing import Dict, Tuple
import logging

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFExtractionService:
    
    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> Tuple[str, str]:
        """
        Extract text from PDF using available libraries
        Returns: (text, method_used)
        """
        text = ""
        method = "none"
        
        # Try pdfplumber first (better for structured PDFs)
        if PDFPLUMBER_AVAILABLE:
            try:
                import io
                pdf_file = io.BytesIO(pdf_content)
                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    method = "pdfplumber"
                    return text, method
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {str(e)}")
        
        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE and not text:
            try:
                import io
                pdf_file = io.BytesIO(pdf_content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                if text.strip():
                    method = "pypdf2"
                    return text, method
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed: {str(e)}")
        
        return text, method
    
    @staticmethod
    def extract_invoice_data(text: str) -> Dict:
        """
        Extract invoice data from text using regex patterns for AFIP invoices
        """
        data = {
            'cuit': None,
            'proveedor': None,
            'tipo_comprobante': None,
            'numero_comprobante': None,
            'fecha_emision': None,
            'importe_total': None,
            'cae': None
        }
        
        # Extract CUIT (formato: XX-XXXXXXXX-X)
        cuit_match = re.search(r'CUIT[:\s]*(\d{2}[-\s]?\d{8}[-\s]?\d{1})', text, re.IGNORECASE)
        if cuit_match:
            cuit = cuit_match.group(1)
            # Normalize CUIT format
            cuit = re.sub(r'[-\s]', '', cuit)
            if len(cuit) == 11:
                data['cuit'] = f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"
        
        # Extract Proveedor (razón social) - usually before CUIT
        if cuit_match:
            text_before_cuit = text[:cuit_match.start()]
            # Look for capitalized text in the lines before CUIT
            lines = text_before_cuit.split('\n')
            for line in reversed(lines[-5:]):  # Check last 5 lines before CUIT
                line = line.strip()
                if len(line) > 5 and line.isupper():
                    data['proveedor'] = line
                    break
        
        # Extract Tipo de Comprobante (FACTURA A/B/C, NOTA DE CRÉDITO, etc.)
        tipo_match = re.search(
            r'(FACTURA|NOTA\s+DE\s+CR[EÉ]DITO|NOTA\s+DE\s+D[EÉ]BITO)\s+([ABC])',
            text,
            re.IGNORECASE
        )
        if tipo_match:
            tipo = tipo_match.group(1).upper()
            letra = tipo_match.group(2).upper()
            data['tipo_comprobante'] = f"{tipo} {letra}"
        
        # Extract Número de Comprobante (formato: XXXX-XXXXXXXX)
        numero_match = re.search(r'N[°º]?\s*(\d{4}[-\s]?\d{8})', text, re.IGNORECASE)
        if not numero_match:
            numero_match = re.search(r'(\d{4}[-\s]\d{8})', text)
        if numero_match:
            numero = numero_match.group(1)
            # Normalize format
            numero = re.sub(r'[-\s]', '', numero)
            if len(numero) == 12:
                data['numero_comprobante'] = f"{numero[:4]}-{numero[4:]}"
        
        # Extract Fecha de Emisión (formato: DD/MM/YYYY)
        fecha_match = re.search(
            r'FECHA\s+DE?\s+EMISI[OÓ]N[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            text,
            re.IGNORECASE
        )
        if not fecha_match:
            fecha_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4})', text)
        
        if fecha_match:
            fecha_str = fecha_match.group(1)
            try:
                # Try to parse date
                fecha = datetime.strptime(fecha_str.replace('-', '/'), '%d/%m/%Y').date()
                data['fecha_emision'] = fecha
            except ValueError:
                pass
        
        # Extract Importe Total
        # Look for patterns like "TOTAL $X,XXX.XX" or "IMPORTE TOTAL: $X,XXX.XX"
        importe_match = re.search(
            r'(?:TOTAL|IMPORTE\s+TOTAL)[:\s]*\$?\s*([\d,.]+)',
            text,
            re.IGNORECASE
        )
        if importe_match:
            importe_str = importe_match.group(1)
            # Remove thousands separator and convert to float
            importe_str = importe_str.replace('.', '').replace(',', '.')
            try:
                data['importe_total'] = float(importe_str)
            except ValueError:
                pass
        
        # Extract CAE (Código de Autorización Electrónico - 14 digits)
        cae_match = re.search(r'CAE[:\s]*(\d{14})', text, re.IGNORECASE)
        if cae_match:
            data['cae'] = cae_match.group(1)
        
        return data
    
    @staticmethod
    def calculate_confidence_score(data: Dict) -> int:
        """
        Calculate confidence score (0-100) based on extracted fields
        """
        score = 0
        
        # Required fields (60% total)
        required_fields = ['cuit', 'tipo_comprobante', 'numero_comprobante', 'fecha_emision', 'importe_total']
        required_weight = 60 / len(required_fields)
        
        for field in required_fields:
            if data.get(field):
                score += required_weight
        
        # Optional fields (20% total)
        optional_fields = ['proveedor', 'cae']
        optional_weight = 20 / len(optional_fields)
        
        for field in optional_fields:
            if data.get(field):
                score += optional_weight
        
        # Format validation (20% total)
        format_score = 0
        
        # CUIT format validation
        if data.get('cuit'):
            if re.match(r'\d{2}-\d{8}-\d{1}', data['cuit']):
                format_score += 5
        
        # Número comprobante format validation
        if data.get('numero_comprobante'):
            if re.match(r'\d{4}-\d{8}', data['numero_comprobante']):
                format_score += 5
        
        # Date validation
        if data.get('fecha_emision'):
            if isinstance(data['fecha_emision'], datetime) or hasattr(data['fecha_emision'], 'year'):
                format_score += 5
        
        # Amount validation
        if data.get('importe_total'):
            if isinstance(data['importe_total'], (int, float)) and data['importe_total'] > 0:
                format_score += 5
        
        score += format_score
        
        return int(min(score, 100))
    
    @staticmethod
    def extract_invoice_from_pdf(pdf_content: bytes) -> Tuple[Dict, str, str]:
        """
        Complete extraction: text extraction + data parsing + confidence calculation
        Returns: (extracted_data, raw_text, extraction_method)
        """
        # Extract text
        text, method = PDFExtractionService.extract_text_from_pdf(pdf_content)
        
        if not text.strip():
            logger.warning("No text extracted from PDF")
            return {
                'confidence': 0,
                'error': 'No text could be extracted from PDF'
            }, "", method
        
        # Extract invoice data
        data = PDFExtractionService.extract_invoice_data(text)
        
        # Calculate confidence
        confidence = PDFExtractionService.calculate_confidence_score(data)
        data['confidence'] = confidence
        
        logger.info(f"Extracted invoice data with {confidence}% confidence using {method}")
        
        return data, text, method
