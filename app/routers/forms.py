from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, List
import logging
import json

from app.services.google_forms_service import GoogleFormsService
from app.models.quiz import GoogleFormRequest, GoogleFormResponse, Question
from app.models.response import success_response, error_response
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

forms_service = GoogleFormsService()

async def get_credentials_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract Google credentials from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        # Expecting format: "Bearer <credentials_json_base64>" or just the credentials JSON
        if authorization.startswith("Bearer "):
            credentials_json = authorization[7:]  # Remove "Bearer " prefix
        else:
            credentials_json = authorization
        
        # Try to parse as JSON to validate
        json.loads(credentials_json)
        return credentials_json
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid credentials format")
    except Exception as e:
        logger.error(f"Error parsing credentials: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authorization header")

@router.post("/create", responses={
    200: {
        "description": "Google Form created successfully",
        "content": {
            "application/json": {
                "examples": {
                    "form_creation_success": {
                        "summary": "Successful Form Creation",
                        "description": "Example response when Google Form is created successfully",
                        "value": {
                            "error": False,
                            "data": {
                                "form_id": "1FAIpQLSd4vJ5RQ7...",
                                "form_url": "https://forms.gle/ABC123",
                                "edit_url": "https://docs.google.com/forms/d/1FAIpQLSd4vJ5RQ7.../edit",
                                "title": "AI Generated Quiz - Kane Williamson",
                                "created_at": "2025-08-20T15:30:45.123456"
                            },
                            "message": "Google Form created successfully"
                        }
                    }
                }
            }
        }
    }
})
async def create_google_form(
    request: GoogleFormRequest,
    credentials_json: str = Depends(get_credentials_from_header)
):
    """Create a Google Form with quiz questions"""
    try:
        if not request.questions:
            return error_response("No questions provided")
        
        if len(request.questions) > settings.MAX_QUESTIONS_PER_QUIZ:
            return error_response(f"Maximum {settings.MAX_QUESTIONS_PER_QUIZ} questions allowed")
        
        # Create the Google Form
        form_response = forms_service.create_form_with_questions(
            questions=request.questions,
            credentials_json=credentials_json,
            form_title=request.form_title,
            form_description=request.form_description,
            is_quiz=request.is_quiz
        )
        
        return success_response({
            "form_id": form_response.form_id,
            "form_url": form_response.form_url,
            "edit_url": form_response.edit_url,
            "title": form_response.title,
            "created_at": form_response.created_at
        }, "Google Form created successfully")
    
    except Exception as e:
        logger.error(f"Error creating Google Form: {str(e)}")
        return error_response("Failed to create Google Form")

@router.post("/create-from-quiz", responses={
    200: {
        "description": "Google Form created successfully from quiz questions",
        "content": {
            "application/json": {
                "examples": {
                    "quiz_form_creation_success": {
                        "summary": "Form Created from Quiz Questions",
                        "description": "Example response when creating Google Form from generated quiz",
                        "value": {
                            "error": False,
                            "data": {
                                "form_id": "1FAIpQLSe8xK2vN9...",
                                "form_url": "https://forms.gle/DEF456",
                                "edit_url": "https://docs.google.com/forms/d/1FAIpQLSe8xK2vN9.../edit",
                                "title": "AI Generated Quiz",
                                "created_at": "2025-08-20T15:35:22.987654"
                            },
                            "message": "Google Form created successfully"
                        }
                    }
                }
            }
        }
    }
})
async def create_form_from_quiz_response(
    questions: List[Question],
    credentials_json: str = Depends(get_credentials_from_header),
    form_title: str = "AI Generated Quiz",
    form_description: Optional[str] = None,
    is_quiz: bool = True
):
    """Create a Google Form directly from a list of questions"""
    try:
        if not questions:
            return error_response("No questions provided")
        
        if len(questions) > settings.MAX_QUESTIONS_PER_QUIZ:
            return error_response(f"Maximum {settings.MAX_QUESTIONS_PER_QUIZ} questions allowed")
        
        # Create the Google Form
        form_response = forms_service.create_form_with_questions(
            questions=questions,
            credentials_json=credentials_json,
            form_title=form_title,
            form_description=form_description,
            is_quiz=is_quiz
        )
        
        return success_response({
            "form_id": form_response.form_id,
            "form_url": form_response.form_url,
            "edit_url": form_response.edit_url,
            "title": form_response.title,
            "created_at": form_response.created_at
        }, "Google Form created successfully")
    
    except Exception as e:
        logger.error(f"Error creating Google Form: {str(e)}")
        return error_response("Failed to create Google Form")

@router.get("/{form_id}/responses", responses={
    200: {
        "description": "Form responses retrieved successfully",
        "content": {
            "application/json": {
                "examples": {
                    "form_responses_success": {
                        "summary": "Form Responses Retrieved",
                        "description": "Example response when getting form responses",
                        "value": {
                            "error": False,
                            "data": {
                                "form_id": "1FAIpQLSd4vJ5RQ7...",
                                "total_responses": 3,
                                "responses": [
                                    {
                                        "response_id": "ACYDBNhX8Q...",
                                        "timestamp": "2025-08-20T16:00:12.345Z",
                                        "respondent_email": "student1@example.com",
                                        "answers": [
                                            {
                                                "question_id": "12345678",
                                                "question_text": "In what year did Kane Williamson make his first-class debut?",
                                                "answer": "2007",
                                                "is_correct": True,
                                                "score": 1
                                            },
                                            {
                                                "question_id": "87654321",
                                                "question_text": "Kane Williamson's international cricket debut was in 2007.",
                                                "answer": "False",
                                                "is_correct": True,
                                                "score": 1
                                            }
                                        ],
                                        "total_score": 2,
                                        "max_score": 2
                                    }
                                ],
                                "retrieved_at": "2025-08-20T16:15:30.123456"
                            },
                            "message": "Form responses retrieved successfully"
                        }
                    }
                }
            }
        }
    }
})
async def get_form_responses(
    form_id: str,
    credentials_json: str = Depends(get_credentials_from_header)
):
    """Get responses from a Google Form"""
    try:
        responses = forms_service.get_form_responses(form_id, credentials_json)
        return success_response(responses, "Form responses retrieved successfully")
    
    except Exception as e:
        logger.error(f"Error getting form responses: {str(e)}")
        return error_response("Failed to get form responses")

@router.delete("/{form_id}", responses={
    200: {
        "description": "Form deleted successfully",
        "content": {
            "application/json": {
                "examples": {
                    "form_deletion_success": {
                        "summary": "Form Deleted Successfully",
                        "description": "Example response when form is moved to trash",
                        "value": {
                            "error": False,
                            "data": {
                                "deleted": True,
                                "form_id": "1FAIpQLSd4vJ5RQ7..."
                            },
                            "message": "Form moved to trash successfully"
                        }
                    }
                }
            }
        }
    }
})
async def delete_form(
    form_id: str,
    credentials_json: str = Depends(get_credentials_from_header)
):
    """Delete a Google Form (move to trash)"""
    try:
        success = forms_service.delete_form(form_id, credentials_json)
        return success_response({
            "deleted": success,
            "form_id": form_id
        }, "Form moved to trash successfully")
    
    except Exception as e:
        logger.error(f"Error deleting form: {str(e)}")
        return error_response("Failed to delete form")

@router.get("/", responses={
    200: {
        "description": "Google Forms integration information",
        "content": {
            "application/json": {
                "examples": {
                    "forms_info": {
                        "summary": "Google Forms Integration Info",
                        "description": "Information about Google Forms API integration",
                        "value": {
                            "error": False,
                            "data": {
                                "message": "Google Forms API integration",
                                "features": [
                                    "Create forms with AI-generated questions",
                                    "Support for multiple question types",
                                    "Quiz mode with automatic grading",
                                    "Secure OAuth 2.0 authentication"
                                ],
                                "supported_question_types": [
                                    "multiple_choice",
                                    "true_false",
                                    "open_ended"
                                ],
                                "max_questions_per_form": 40
                            },
                            "message": "Google Forms integration information retrieved successfully"
                        }
                    }
                }
            }
        }
    }
})
async def get_forms_info():
    """Get information about Google Forms integration"""
    return success_response({
        "message": "Google Forms API integration",
        "features": [
            "Create forms with AI-generated questions",
            "Support for multiple question types",
            "Quiz mode with automatic grading",
            "Secure OAuth 2.0 authentication"
        ],
        "supported_question_types": [
            "multiple_choice",
            "true_false",
            "open_ended"
        ],
        "max_questions_per_form": settings.MAX_QUESTIONS_PER_QUIZ
    }, "Google Forms integration information retrieved successfully")