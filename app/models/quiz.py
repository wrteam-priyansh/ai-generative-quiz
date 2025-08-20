from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    OPEN_ENDED = "open_ended"

class DifficultyLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuizGenerationRequest(BaseModel):
    text: str = Field(..., min_length=50, description="Text content to generate questions from")
    num_questions: int = Field(default=5, ge=1, le=40, description="Number of questions to generate")
    question_types: List[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE], description="Types of questions to generate")
    difficulty_levels: List[DifficultyLevel] = Field(default=[DifficultyLevel.INTERMEDIATE], description="Difficulty levels of questions")
    topic: Optional[str] = Field(default=None, description="Specific topic focus for the quiz")

class FileUploadRequest(BaseModel):
    num_questions: int = Field(default=5, ge=1, le=40, description="Number of questions to generate")
    question_types: List[QuestionType] = Field(default=[QuestionType.MULTIPLE_CHOICE], description="Types of questions to generate")
    difficulty_levels: List[DifficultyLevel] = Field(default=[DifficultyLevel.INTERMEDIATE], description="Difficulty levels of questions")
    topic: Optional[str] = Field(default=None, description="Specific topic focus for the quiz")

class MultipleChoiceOption(BaseModel):
    text: str
    is_correct: bool

class Question(BaseModel):
    id: str
    question_text: str
    question_type: QuestionType
    options: Optional[List[MultipleChoiceOption]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None

class QuizResponse(BaseModel):
    questions: List[Question]
    total_questions: int
    difficulty: DifficultyLevel
    topic: Optional[str] = None
    generated_at: str

class GoogleFormRequest(BaseModel):
    questions: List[Question]
    form_title: str = Field(default="AI Generated Quiz", description="Title for the Google Form")
    form_description: Optional[str] = Field(default=None, description="Description for the Google Form")

class DownloadRequest(BaseModel):
    questions: List[dict] = Field(..., description="List of question objects to download")
    include_answers: bool = Field(default=True, description="Include answers in the download")
    topic: Optional[str] = Field(default=None, description="Topic for the quiz")
    difficulty_levels: Optional[List[str]] = Field(default=None, description="Difficulty levels for metadata")

class AnswerKeyRequest(BaseModel):
    questions: List[dict] = Field(..., description="List of question objects for answer key")
    topic: Optional[str] = Field(default=None, description="Topic for the quiz")

class GoogleFormResponse(BaseModel):
    form_id: str
    form_url: str
    edit_url: str
    title: str
    created_at: str