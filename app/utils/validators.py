import re
from typing import List, Optional
from fastapi import HTTPException
from app.models.quiz import QuestionType, DifficultyLevel

class RequestValidator:
    """Utility class for validating API requests"""
    
    @staticmethod
    def validate_text_content(text: str, min_length: int = 50, max_length: int = 50000) -> None:
        """Validate text content for quiz generation"""
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")
        
        text = text.strip()
        
        if len(text) < min_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text content must be at least {min_length} characters long"
            )
        
        if len(text) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text content must not exceed {max_length} characters"
            )
    
    @staticmethod
    def validate_question_count(num_questions: int, min_count: int = 1, max_count: int = 20) -> None:
        """Validate number of questions to generate"""
        if num_questions < min_count:
            raise HTTPException(
                status_code=400,
                detail=f"Number of questions must be at least {min_count}"
            )
        
        if num_questions > max_count:
            raise HTTPException(
                status_code=400,
                detail=f"Number of questions cannot exceed {max_count}"
            )
    
    @staticmethod
    def validate_question_types(question_types: List[str]) -> List[QuestionType]:
        """Validate and convert question types"""
        if not question_types:
            return [QuestionType.MULTIPLE_CHOICE]
        
        valid_types = []
        for qt in question_types:
            try:
                valid_types.append(QuestionType(qt.lower().strip()))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid question type: {qt}. Valid types: {[t.value for t in QuestionType]}"
                )
        
        return valid_types
    
    @staticmethod
    def validate_difficulty_level(difficulty: str) -> DifficultyLevel:
        """Validate and convert difficulty level"""
        try:
            return DifficultyLevel(difficulty.lower().strip())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid difficulty level: {difficulty}. Valid levels: {[d.value for d in DifficultyLevel]}"
            )
    
    @staticmethod
    def validate_form_title(title: str, max_length: int = 100) -> str:
        """Validate Google Form title"""
        if not title or not title.strip():
            return "AI Generated Quiz"
        
        title = title.strip()
        
        if len(title) > max_length:
            title = title[:max_length].rstrip()
        
        # Remove any potentially problematic characters
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        
        return title if title else "AI Generated Quiz"
    
    @staticmethod
    def validate_form_description(description: Optional[str], max_length: int = 500) -> Optional[str]:
        """Validate Google Form description"""
        if not description:
            return None
        
        description = description.strip()
        
        if len(description) > max_length:
            description = description[:max_length].rstrip()
        
        # Remove any potentially problematic characters
        description = re.sub(r'[<>]', '', description)
        
        return description if description else None
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> str:
        """Validate file extension"""
        if not filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        file_extension = filename.split('.')[-1].lower() if '.' in filename else ""
        
        if not file_extension:
            raise HTTPException(status_code=400, detail="File must have an extension")
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return file_extension
    
    @staticmethod
    def validate_file_size(file_size: int, max_size: int) -> None:
        """Validate file size"""
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size} bytes) exceeds maximum limit of {max_size_mb:.1f}MB"
            )
    
    @staticmethod
    def sanitize_text_input(text: str) -> str:
        """Sanitize text input by removing potentially harmful content"""
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove any potentially harmful patterns
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        return text.strip()
    
    @staticmethod
    def validate_topic(topic: Optional[str], max_length: int = 100) -> Optional[str]:
        """Validate and sanitize topic"""
        if not topic:
            return None
        
        topic = topic.strip()
        
        if len(topic) > max_length:
            topic = topic[:max_length].rstrip()
        
        # Basic sanitization
        topic = re.sub(r'[<>"]', '', topic)
        
        return topic if topic else None