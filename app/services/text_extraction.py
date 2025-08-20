import PyPDF2
import docx
from io import BytesIO
from typing import Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class TextExtractionService:
    """Service for extracting text from various document formats"""
    
    @staticmethod
    def extract_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from PDF")
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
    
    @staticmethod
    def extract_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(BytesIO(file_content))
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from DOCX")
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to extract text from DOCX")
    
    @staticmethod
    def extract_from_txt(file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            text = file_content.decode('utf-8')
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="Text file is empty")
            
            return text.strip()
        
        except UnicodeDecodeError:
            try:
                text = file_content.decode('latin-1')
                return text.strip()
            except Exception as e:
                logger.error(f"Error decoding text file: {str(e)}")
                raise HTTPException(status_code=400, detail="Failed to decode text file")
        
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise HTTPException(status_code=400, detail="Failed to extract text from TXT")
    
    @classmethod
    def extract_text(cls, file_content: bytes, file_type: str) -> str:
        """Extract text based on file type"""
        file_type = file_type.lower()
        
        if file_type == "pdf":
            return cls.extract_from_pdf(file_content)
        elif file_type == "docx":
            return cls.extract_from_docx(file_content)
        elif file_type == "txt":
            return cls.extract_from_txt(file_content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
    
    @staticmethod
    def validate_file_size(file_content: bytes, max_size: int = 10 * 1024 * 1024) -> bool:
        """Validate file size (default 10MB)"""
        return len(file_content) <= max_size
    
    @staticmethod
    def validate_text_length(text: str, min_length: int = 50) -> bool:
        """Validate minimum text length for meaningful quiz generation"""
        return len(text.strip()) >= min_length