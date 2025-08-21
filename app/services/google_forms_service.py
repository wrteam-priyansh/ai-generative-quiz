from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import List, Dict, Any
import logging
from datetime import datetime

from app.models.quiz import Question, QuestionType, MultipleChoiceOption, GoogleFormResponse
from app.services.auth_service import GoogleAuthService
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class GoogleFormsService:
    """Service for creating and managing Google Forms"""
    
    def __init__(self):
        self.auth_service = GoogleAuthService()
    
    def create_form_with_questions(
        self,
        questions: List[Question],
        credentials_json: str,
        form_title: str = "AI Generated Quiz",
        form_description: str = None,
        is_quiz: bool = True
    ) -> GoogleFormResponse:
        """Create a Google Form with quiz questions"""
        
        try:
            credentials = self.auth_service.get_credentials_from_json(credentials_json)
            forms_service = build('forms', 'v1', credentials=credentials)
            
            # Create the form with only title (API restriction)
            form_body = {
                "info": {
                    "title": form_title
                }
            }
            
            # Create the form
            form = forms_service.forms().create(body=form_body).execute()
            form_id = form['formId']
            
            # Add form settings and description via batchUpdate
            self._update_form_settings(forms_service, form_id, form_description or f"Auto-generated quiz with {len(questions)} questions", is_quiz)
            
            # Add questions to the form
            self._add_questions_to_form(forms_service, form_id, questions, is_quiz)
            
            # Get the final form details
            final_form = forms_service.forms().get(formId=form_id).execute()
            
            return GoogleFormResponse(
                form_id=form_id,
                form_url=final_form['responderUri'],
                edit_url=f"https://docs.google.com/forms/d/{form_id}/edit",
                title=form_title,
                created_at=datetime.now().isoformat()
            )
        
        except Exception as e:
            logger.error(f"Error creating Google Form: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create Google Form: {str(e)}")
    
    def _update_form_settings(
        self,
        forms_service: Any,
        form_id: str,
        description: str,
        is_quiz: bool
    ) -> None:
        """Update form settings and description via batchUpdate"""
        
        requests = []
        
        # Add description
        requests.append({
            "updateFormInfo": {
                "info": {
                    "description": description
                },
                "updateMask": "description"
            }
        })
        
        # Add quiz settings if needed
        if is_quiz:
            requests.append({
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": True
                        }
                    },
                    "updateMask": "quizSettings"
                }
            })
        
        if requests:
            batch_update_body = {"requests": requests}
            forms_service.forms().batchUpdate(
                formId=form_id,
                body=batch_update_body
            ).execute()
    
    def _add_questions_to_form(
        self,
        forms_service: Any,
        form_id: str,
        questions: List[Question],
        is_quiz: bool
    ) -> None:
        """Add questions to the Google Form"""
        
        requests = []
        
        for index, question in enumerate(questions):
            request = self._create_question_request(question, index, is_quiz)
            requests.append(request)
        
        if requests:
            batch_update_body = {"requests": requests}
            forms_service.forms().batchUpdate(
                formId=form_id,
                body=batch_update_body
            ).execute()
    
    def _create_question_request(self, question: Question, index: int, is_quiz: bool) -> Dict[str, Any]:
        """Create a request object for adding a question to the form"""
        
        location = {"index": index}
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            return self._create_multiple_choice_request(question, location, is_quiz)
        elif question.question_type == QuestionType.TRUE_FALSE:
            return self._create_true_false_request(question, location, is_quiz)
        elif question.question_type == QuestionType.OPEN_ENDED:
            return self._create_open_ended_request(question, location)
        else:
            raise ValueError(f"Unsupported question type: {question.question_type}")
    
    def _create_multiple_choice_request(
        self,
        question: Question,
        location: Dict[str, int],
        is_quiz: bool
    ) -> Dict[str, Any]:
        """Create a multiple choice question request"""
        
        options = []
        correct_option_index = None
        
        for i, option in enumerate(question.options or []):
            options.append({"value": option.text})
            if option.is_correct:
                correct_option_index = i
        
        request = {
            "createItem": {
                "item": {
                    "title": question.question_text,
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": options
                            }
                        }
                    }
                },
                "location": location
            }
        }
        
        # Add grading information if this is a quiz
        if is_quiz and correct_option_index is not None:
            request["createItem"]["item"]["questionItem"]["question"]["grading"] = {
                "pointValue": 1,
                "correctAnswers": {
                    "answers": [{"value": options[correct_option_index]["value"]}]
                },
                "whenRight": {
                    "text": question.explanation or "Correct!"
                },
                "whenWrong": {
                    "text": question.explanation or "Incorrect. Please review the material."
                }
            }
        
        return request
    
    def _create_true_false_request(
        self,
        question: Question,
        location: Dict[str, int],
        is_quiz: bool
    ) -> Dict[str, Any]:
        """Create a true/false question request"""
        
        options = [{"value": "True"}, {"value": "False"}]
        correct_answer = question.correct_answer
        
        request = {
            "createItem": {
                "item": {
                    "title": question.question_text,
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": options
                            }
                        }
                    }
                },
                "location": location
            }
        }
        
        # Add grading information if this is a quiz
        if is_quiz and correct_answer:
            correct_value = "True" if correct_answer.lower() == "true" else "False"
            request["createItem"]["item"]["questionItem"]["question"]["grading"] = {
                "pointValue": 1,
                "correctAnswers": {
                    "answers": [{"value": correct_value}]
                },
                "whenRight": {
                    "text": question.explanation or "Correct!"
                },
                "whenWrong": {
                    "text": question.explanation or "Incorrect. Please review the material."
                }
            }
        
        return request
    
    def _create_open_ended_request(
        self,
        question: Question,
        location: Dict[str, int]
    ) -> Dict[str, Any]:
        """Create an open-ended question request"""
        
        return {
            "createItem": {
                "item": {
                    "title": question.question_text,
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": location
            }
        }
    
    def get_form_responses(self, form_id: str, credentials_json: str) -> Dict[str, Any]:
        """Get responses from a Google Form"""
        
        try:
            credentials = self.auth_service.get_credentials_from_json(credentials_json)
            forms_service = build('forms', 'v1', credentials=credentials)
            
            responses = forms_service.forms().responses().list(formId=form_id).execute()
            return responses
        
        except Exception as e:
            logger.error(f"Error getting form responses: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get form responses")
    
    def delete_form(self, form_id: str, credentials_json: str) -> bool:
        """Delete a Google Form (move to trash)"""
        
        try:
            credentials = self.auth_service.get_credentials_from_json(credentials_json)
            drive_service = build('drive', 'v3', credentials=credentials)
            
            # Move the form to trash
            drive_service.files().update(
                fileId=form_id,
                body={'trashed': True}
            ).execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting form: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete form")