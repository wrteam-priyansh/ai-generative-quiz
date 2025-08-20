from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
from datetime import datetime
import io

from app.services.gemini_service import GeminiQuestionGenerationService
from app.services.text_extraction import TextExtractionService
from app.services.file_generation_service import FileGenerationService
from app.models.quiz import (
    QuizGenerationRequest,
    FileUploadRequest,
    QuizResponse,
    Question,
    QuestionType,
    DifficultyLevel,
    DownloadRequest,
    AnswerKeyRequest
)
from app.models.response import success_response, error_response
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

ai_service = GeminiQuestionGenerationService()
text_service = TextExtractionService()
file_generation_service = FileGenerationService()

@router.post("/generate")
async def generate_quiz_from_text(request: QuizGenerationRequest):
    """Generate quiz questions from text input using Google Gemini"""
    try:
        # Validate text length
        if not text_service.validate_text_length(request.text):
            return error_response("Text is too short. Please provide at least 50 characters.")
        
        # Generate questions using Gemini
        questions = ai_service.generate_questions(
            text=request.text,
            num_questions=request.num_questions,
            question_types=request.question_types,
            difficulty_levels=request.difficulty_levels,
            topic=request.topic
        )
        
        # Get text processing info
        text_length = len(request.text)
        chunking_used = text_length > settings.GEMINI_MAX_INPUT_CHARS and settings.ENABLE_TEXT_CHUNKING
        
        quiz_data = {
            "questions": [q.__dict__ for q in questions],
            "total_questions": len(questions),
            "difficulty_levels": [dl.value for dl in request.difficulty_levels],
            "topic": request.topic,
            "generated_at": datetime.now().isoformat(),
            "quiz_settings": {
                "requested_questions": request.num_questions,
                "requested_question_types": [qt.value for qt in request.question_types],
                "difficulty_levels": [dl.value for dl in request.difficulty_levels],
                "topic_focus": request.topic
            },
            "text_processing": {
                "input_length": text_length,
                "chunking_used": chunking_used,
                "max_chunk_size": settings.GEMINI_MAX_INPUT_CHARS
            }
        }
        
        return success_response(quiz_data, "Quiz generated successfully")
    
    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        return error_response("Failed to generate quiz")

@router.post("/generate-from-file")
async def generate_quiz_from_file(
    file: UploadFile = File(...),
    num_questions: int = Form(default=5, ge=1, le=40),
    question_types: str = Form(default="multiple_choice", description="Comma-separated question types: multiple_choice,true_false,open_ended"),
    difficulty_levels: str = Form(default="intermediate", description="Comma-separated difficulty levels: basic,intermediate,advanced"),
    topic: Optional[str] = Form(default=None)
):
    """Generate quiz questions from uploaded file using Google Gemini"""
    try:
        # Validate file type
        file_extension = file.filename.split('.')[-1].lower() if file.filename else ""
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            return error_response(f"Unsupported file type. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}")
        
        # Read and validate file content
        file_content = await file.read()
        
        if not text_service.validate_file_size(file_content, settings.MAX_FILE_SIZE):
            return error_response(f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE} bytes")
        
        # Extract text from file
        extracted_text = text_service.extract_text(file_content, file_extension)
        
        # Validate extracted text length
        if not text_service.validate_text_length(extracted_text):
            return error_response("Extracted text is too short. Please provide a file with more content.")
        
        # Parse question types
        parsed_question_types = []
        question_type_strings = [qt.strip().lower() for qt in question_types.split(',')]
        
        for qt_str in question_type_strings:
            try:
                # Handle common variations
                if qt_str in ['multiple_choice', 'multiple-choice', 'mcq', 'mc']:
                    parsed_question_types.append(QuestionType.MULTIPLE_CHOICE)
                elif qt_str in ['true_false', 'true-false', 'tf', 'bool', 'boolean']:
                    parsed_question_types.append(QuestionType.TRUE_FALSE)
                elif qt_str in ['open_ended', 'open-ended', 'essay', 'text', 'open']:
                    parsed_question_types.append(QuestionType.OPEN_ENDED)
                else:
                    # Try direct enum conversion as fallback
                    parsed_question_types.append(QuestionType(qt_str))
            except ValueError:
                logger.warning(f"Invalid question type: {qt_str}")
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for qt in parsed_question_types:
            if qt not in seen:
                seen.add(qt)
                unique_types.append(qt)
        parsed_question_types = unique_types
        
        if not parsed_question_types:
            parsed_question_types = [QuestionType.MULTIPLE_CHOICE]
            logger.info("No valid question types provided, defaulting to multiple choice")
        
        # Parse difficulty levels
        parsed_difficulty_levels = []
        difficulty_level_strings = [dl.strip().lower() for dl in difficulty_levels.split(',')]
        
        for dl_str in difficulty_level_strings:
            try:
                if dl_str in ['basic', 'easy', 'simple', 'beginner']:
                    parsed_difficulty_levels.append(DifficultyLevel.BASIC)
                elif dl_str in ['intermediate', 'medium', 'moderate', 'normal']:
                    parsed_difficulty_levels.append(DifficultyLevel.INTERMEDIATE)
                elif dl_str in ['advanced', 'hard', 'difficult', 'expert', 'complex']:
                    parsed_difficulty_levels.append(DifficultyLevel.ADVANCED)
                else:
                    # Try direct enum conversion as fallback
                    parsed_difficulty_levels.append(DifficultyLevel(dl_str))
            except ValueError:
                logger.warning(f"Invalid difficulty level: {dl_str}")
                continue
        
        # Remove duplicates while preserving order
        seen_diff = set()
        unique_difficulties = []
        for dl in parsed_difficulty_levels:
            if dl not in seen_diff:
                seen_diff.add(dl)
                unique_difficulties.append(dl)
        parsed_difficulty_levels = unique_difficulties
        
        if not parsed_difficulty_levels:
            parsed_difficulty_levels = [DifficultyLevel.INTERMEDIATE]
            logger.info("No valid difficulty levels provided, defaulting to intermediate")
        
        # Generate questions using Gemini
        questions = ai_service.generate_questions(
            text=extracted_text,
            num_questions=num_questions,
            question_types=parsed_question_types,
            difficulty_levels=parsed_difficulty_levels,
            topic=topic
        )
        
        # Get text processing info
        text_length = len(extracted_text)
        chunking_used = text_length > settings.GEMINI_MAX_INPUT_CHARS and settings.ENABLE_TEXT_CHUNKING
        
        quiz_data = {
            "questions": [q.__dict__ for q in questions],
            "total_questions": len(questions),
            "difficulty_levels": [dl.value for dl in parsed_difficulty_levels],
            "topic": topic,
            "generated_at": datetime.now().isoformat(),
            "source_file": file.filename,
            "quiz_settings": {
                "requested_questions": num_questions,
                "requested_question_types": [qt.value for qt in parsed_question_types],
                "difficulty_levels": [dl.value for dl in parsed_difficulty_levels],
                "topic_focus": topic
            },
            "text_processing": {
                "extracted_text_length": text_length,
                "chunking_used": chunking_used,
                "max_chunk_size": settings.GEMINI_MAX_INPUT_CHARS
            }
        }
        
        return success_response(quiz_data, "Quiz generated successfully from file")
    
    except Exception as e:
        logger.error(f"Error generating quiz from file: {str(e)}")
        return error_response("Failed to generate quiz from file")

@router.get("/test-gemini")
async def test_gemini_connection():
    """Test Google Gemini API connection"""
    try:
        is_connected = ai_service.test_connection()
        return success_response({
            "gemini_connected": is_connected,
            "model": settings.GEMINI_MODEL,
            "status": "connected" if is_connected else "connection_failed"
        }, "Gemini connection test completed")
    except Exception as e:
        logger.error(f"Error testing Gemini connection: {str(e)}")
        return error_response("Failed to test Gemini connection", {
            "gemini_connected": False,
            "model": settings.GEMINI_MODEL,
            "status": "error",
            "error": str(e)
        })

@router.get("/question-types")
async def get_question_types():
    """Get available question types"""
    return success_response({
        "question_types": [
            {"value": qt.value, "label": qt.value.replace("_", " ").title()}
            for qt in QuestionType
        ]
    }, "Question types retrieved successfully")

@router.get("/difficulty-levels")
async def get_difficulty_levels():
    """Get available difficulty levels"""
    return success_response({
        "difficulty_levels": [
            {"value": dl.value, "label": dl.value.title()}
            for dl in DifficultyLevel
        ]
    }, "Difficulty levels retrieved successfully")

@router.get("/limits")
async def get_limits():
    """Get system limits and constraints"""
    return success_response({
        "max_questions": settings.MAX_QUESTIONS_PER_QUIZ,
        "min_questions": settings.MIN_QUESTIONS_PER_QUIZ,
        "max_file_size": settings.MAX_FILE_SIZE,
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "allowed_file_types": settings.ALLOWED_FILE_TYPES,
        "min_text_length": 50,
        "ai_model": settings.GEMINI_MODEL,
        "max_input_chars": settings.GEMINI_MAX_INPUT_CHARS,
        "chunking_enabled": settings.ENABLE_TEXT_CHUNKING
    }, "System limits retrieved successfully")

@router.get("/usage-examples")
async def get_usage_examples():
    """Get usage examples for API parameters"""
    return success_response({
        "question_types": {
            "description": "Specify one or more question types",
            "accepted_formats": [
                "multiple_choice", "multiple-choice", "mcq", "mc",
                "true_false", "true-false", "tf", "bool", "boolean", 
                "open_ended", "open-ended", "essay", "text", "open"
            ],
            "examples": {
                "single_type": "multiple_choice",
                "multiple_types": "multiple_choice,true_false,open_ended",
                "mixed_format": "mcq,tf,essay"
            }
        },
        "difficulty_levels": {
            "description": "Choose one or more difficulty levels for questions",
            "accepted_formats": [
                "basic", "easy", "simple", "beginner",
                "intermediate", "medium", "moderate", "normal",
                "advanced", "hard", "difficult", "expert", "complex"
            ],
            "examples": {
                "single_level": "intermediate",
                "multiple_levels": "basic,intermediate,advanced",
                "mixed_format": "easy,medium,hard"
            },
            "descriptions": {
                "basic": "Simple, straightforward questions",
                "intermediate": "Moderate complexity requiring some analysis", 
                "advanced": "Complex questions requiring deep understanding"
            }
        },
        "num_questions": {
            "description": "Number of questions to generate",
            "range": f"{settings.MIN_QUESTIONS_PER_QUIZ} to {settings.MAX_QUESTIONS_PER_QUIZ}",
            "examples": [5, 10, 20, 30, 40]
        },
        "api_examples": {
            "text_generation": {
                "method": "POST",
                "endpoint": "/quiz/generate",
                "sample_request": {
                    "text": "Your content here...",
                    "num_questions": 10,
                    "question_types": ["multiple_choice", "true_false"],
                    "difficulty_levels": ["basic", "intermediate"],
                    "topic": "Optional specific topic"
                }
            },
            "file_generation": {
                "method": "POST", 
                "endpoint": "/quiz/generate-from-file",
                "sample_form_data": {
                    "file": "document.pdf",
                    "num_questions": 15,
                    "question_types": "multiple_choice,open_ended",
                    "difficulty_levels": "intermediate,advanced",
                    "topic": "Optional specific topic"
                }
            }
        }
    }, "Usage examples retrieved successfully")

@router.post("/download/txt")
async def download_quiz_txt(request: DownloadRequest):
    """Download quiz questions as TXT file"""
    try:
        # Extract parameters from request
        questions = request.questions
        include_answers = request.include_answers
        topic = request.topic
        difficulty_levels = request.difficulty_levels
        
        # Convert dict questions back to Question objects
        question_objects = []
        for q_data in questions:
            try:
                # Convert question type
                question_type = QuestionType(q_data.get("question_type", "multiple_choice"))
                
                # Handle options for multiple choice
                options = None
                if question_type == QuestionType.MULTIPLE_CHOICE and q_data.get("options"):
                    from app.models.quiz import MultipleChoiceOption
                    options = [
                        MultipleChoiceOption(
                            text=opt["text"],
                            is_correct=opt["is_correct"]
                        )
                        for opt in q_data["options"]
                    ]
                
                question = Question(
                    id=q_data.get("id", ""),
                    question_text=q_data["question_text"],
                    question_type=question_type,
                    options=options,
                    correct_answer=q_data.get("correct_answer"),
                    explanation=q_data.get("explanation")
                )
                question_objects.append(question)
            except Exception as e:
                logger.warning(f"Skipping invalid question: {str(e)}")
                continue
        
        if not question_objects:
            return error_response("No valid questions provided")
        
        # Prepare metadata
        quiz_metadata = {
            "generated_at": datetime.now().isoformat(),
            "total_questions": len(question_objects),
            "topic": topic
        }
        
        if difficulty_levels:
            quiz_metadata["difficulty_levels"] = difficulty_levels
        
        # Generate content
        if include_answers:
            content = file_generation_service.generate_txt_content(question_objects, quiz_metadata)
        else:
            # Generate questions without answer markers
            content_lines = []
            content_lines.append("=" * 60)
            content_lines.append("AI GENERATED QUIZ")
            content_lines.append("=" * 60)
            content_lines.append("")
            
            if quiz_metadata:
                content_lines.append(f"Generated: {quiz_metadata.get('generated_at', datetime.now().isoformat())}")
                content_lines.append(f"Total Questions: {quiz_metadata.get('total_questions', len(question_objects))}")
                if quiz_metadata.get('topic'):
                    content_lines.append(f"Topic: {quiz_metadata['topic']}")
                content_lines.append("")
            
            content_lines.append("-" * 60)
            content_lines.append("QUESTIONS")
            content_lines.append("-" * 60)
            content_lines.append("")
            
            for i, question in enumerate(question_objects, 1):
                content_lines.append(f"Question {i}:")
                content_lines.append(f"Q: {question.question_text}")
                content_lines.append("")
                
                if question.question_type == QuestionType.MULTIPLE_CHOICE and question.options:
                    content_lines.append("Options:")
                    for j, option in enumerate(question.options):
                        letter = chr(65 + j)  # A, B, C, D
                        content_lines.append(f"  {letter}) {option.text}")
                    content_lines.append("")
                elif question.question_type == QuestionType.TRUE_FALSE:
                    content_lines.append("Options:")
                    content_lines.append("  A) True")
                    content_lines.append("  B) False")
                    content_lines.append("")
                
                content_lines.append("-" * 40)
                content_lines.append("")
            
            content = "\n".join(content_lines)
        
        # Generate filename
        filename = file_generation_service.get_filename(quiz_metadata, "txt", include_answers)
        
        # Create response
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error generating TXT download: {str(e)}")
        return error_response("Failed to generate TXT file")

@router.post("/download/pdf")
async def download_quiz_pdf(request: DownloadRequest):
    """Download quiz questions as PDF file"""
    try:
        # Extract parameters from request
        questions = request.questions
        include_answers = request.include_answers
        topic = request.topic
        difficulty_levels = request.difficulty_levels
        
        # Convert dict questions back to Question objects
        question_objects = []
        for q_data in questions:
            try:
                # Convert question type
                question_type = QuestionType(q_data.get("question_type", "multiple_choice"))
                
                # Handle options for multiple choice
                options = None
                if question_type == QuestionType.MULTIPLE_CHOICE and q_data.get("options"):
                    from app.models.quiz import MultipleChoiceOption
                    options = [
                        MultipleChoiceOption(
                            text=opt["text"],
                            is_correct=opt["is_correct"]
                        )
                        for opt in q_data["options"]
                    ]
                
                question = Question(
                    id=q_data.get("id", ""),
                    question_text=q_data["question_text"],
                    question_type=question_type,
                    options=options,
                    correct_answer=q_data.get("correct_answer"),
                    explanation=q_data.get("explanation")
                )
                question_objects.append(question)
            except Exception as e:
                logger.warning(f"Skipping invalid question: {str(e)}")
                continue
        
        if not question_objects:
            return error_response("No valid questions provided")
        
        # Prepare metadata
        quiz_metadata = {
            "generated_at": datetime.now().isoformat(),
            "total_questions": len(question_objects),
            "topic": topic
        }
        
        if difficulty_levels:
            quiz_metadata["difficulty_levels"] = difficulty_levels
        
        # Generate PDF content
        pdf_content = file_generation_service.generate_pdf_content(question_objects, quiz_metadata)
        
        # Generate filename
        filename = file_generation_service.get_filename(quiz_metadata, "pdf", include_answers)
        
        # Create response
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error generating PDF download: {str(e)}")
        return error_response("Failed to generate PDF file")

@router.post("/download/answer-key")
async def download_answer_key(request: AnswerKeyRequest):
    """Download answer key as TXT file"""
    try:
        # Extract parameters from request
        questions = request.questions
        topic = request.topic
        
        # Convert dict questions back to Question objects
        question_objects = []
        for q_data in questions:
            try:
                # Convert question type
                question_type = QuestionType(q_data.get("question_type", "multiple_choice"))
                
                # Handle options for multiple choice
                options = None
                if question_type == QuestionType.MULTIPLE_CHOICE and q_data.get("options"):
                    from app.models.quiz import MultipleChoiceOption
                    options = [
                        MultipleChoiceOption(
                            text=opt["text"],
                            is_correct=opt["is_correct"]
                        )
                        for opt in q_data["options"]
                    ]
                
                question = Question(
                    id=q_data.get("id", ""),
                    question_text=q_data["question_text"],
                    question_type=question_type,
                    options=options,
                    correct_answer=q_data.get("correct_answer"),
                    explanation=q_data.get("explanation")
                )
                question_objects.append(question)
            except Exception as e:
                logger.warning(f"Skipping invalid question: {str(e)}")
                continue
        
        if not question_objects:
            return error_response("No valid questions provided")
        
        # Generate answer key content
        content = file_generation_service.generate_answer_key_txt(question_objects)
        
        # Prepare metadata for filename
        quiz_metadata = {
            "topic": topic,
            "generated_at": datetime.now().isoformat()
        }
        
        # Generate filename
        filename = file_generation_service.get_filename(quiz_metadata, "txt", True).replace(".txt", "_answer_key.txt")
        
        # Create response
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        logger.error(f"Error generating answer key: {str(e)}")
        return error_response("Failed to generate answer key")