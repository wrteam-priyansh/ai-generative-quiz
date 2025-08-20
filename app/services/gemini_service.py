import google.generativeai as genai
from typing import List, Dict, Any
import json
import uuid
from datetime import datetime
from fastapi import HTTPException
import logging

from app.models.quiz import Question, QuestionType, DifficultyLevel, MultipleChoiceOption
from app.services.text_chunking import TextChunkingService
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiQuestionGenerationService:
    """Service for generating quiz questions using Google Gemini API"""
    
    def __init__(self):
        if not settings.GOOGLE_GEMINI_API_KEY:
            raise ValueError("Google Gemini API key not configured")
        
        genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    def generate_questions(
        self,
        text: str,
        num_questions: int = 5,
        question_types: List[QuestionType] = None,
        difficulty_levels: List[DifficultyLevel] = None,
        topic: str = None
    ) -> List[Question]:
        """Generate quiz questions from text using Google Gemini with smart chunking"""
        
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE]
        if difficulty_levels is None:
            difficulty_levels = [DifficultyLevel.INTERMEDIATE]
        
        try:
            # Check if text needs chunking
            max_chunk_size = settings.GEMINI_MAX_INPUT_CHARS
            
            if not settings.ENABLE_TEXT_CHUNKING or len(text) <= max_chunk_size:
                # Text is small enough, process directly
                return self._generate_from_single_text(text, num_questions, question_types, difficulty_levels, topic)
            else:
                # Text is large, use chunking approach
                return self._generate_from_chunked_text(text, num_questions, question_types, difficulty_levels, topic, max_chunk_size)
        
        except Exception as e:
            logger.error(f"Error generating questions with Gemini: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate questions")
    
    def _generate_from_single_text(
        self,
        text: str,
        num_questions: int,
        question_types: List[QuestionType],
        difficulty_levels: List[DifficultyLevel],
        topic: str = None
    ) -> List[Question]:
        """Generate questions from single text chunk"""
        
        prompt = self._create_prompt(text, num_questions, question_types, difficulty_levels, topic)
        
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
        )
        
        content = response.text
        questions_data = self._parse_ai_response(content)
        
        return self._convert_to_question_objects(questions_data, question_types)
    
    def _generate_from_chunked_text(
        self,
        text: str,
        num_questions: int,
        question_types: List[QuestionType],
        difficulty_levels: List[DifficultyLevel],
        topic: str = None,
        max_chunk_size: int = 4000
    ) -> List[Question]:
        """Generate questions from large text using chunking strategy"""
        
        logger.info(f"Text length {len(text)} exceeds limit, using chunking approach")
        
        # Chunk the text intelligently
        chunks = TextChunkingService.smart_chunk_text(text, max_chunk_size, strategy="paragraphs")
        chunk_summary = TextChunkingService.get_chunk_summary(chunks)
        
        logger.info(f"Chunking summary: {chunk_summary}")
        
        # Distribute questions across chunks based on chunk sizes
        questions_per_chunk = self._distribute_questions_across_chunks(chunks, num_questions)
        
        all_questions = []
        
        for i, (chunk, chunk_questions) in enumerate(zip(chunks, questions_per_chunk)):
            if chunk_questions <= 0:
                continue
                
            logger.info(f"Generating {chunk_questions} questions from chunk {i+1}/{len(chunks)}")
            
            try:
                chunk_questions_list = self._generate_from_single_text(
                    chunk, chunk_questions, question_types, difficulty_levels, topic
                )
                all_questions.extend(chunk_questions_list)
                
            except Exception as e:
                logger.warning(f"Failed to generate questions from chunk {i+1}: {str(e)}")
                continue
        
        # If we didn't get enough questions, try to generate more from the best chunks
        if len(all_questions) < num_questions:
            remaining = num_questions - len(all_questions)
            logger.info(f"Need {remaining} more questions, trying largest chunks")
            
            # Sort chunks by size and try the largest ones
            chunk_sizes = [(i, len(chunk)) for i, chunk in enumerate(chunks)]
            chunk_sizes.sort(key=lambda x: x[1], reverse=True)
            
            for chunk_idx, _ in chunk_sizes[:2]:  # Try top 2 largest chunks
                if len(all_questions) >= num_questions:
                    break
                    
                try:
                    additional_questions = self._generate_from_single_text(
                        chunks[chunk_idx], min(remaining, 3), question_types, difficulty_levels, topic
                    )
                    all_questions.extend(additional_questions)
                    remaining = num_questions - len(all_questions)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate additional questions: {str(e)}")
                    continue
        
        # Return up to the requested number of questions
        return all_questions[:num_questions]
    
    def _distribute_questions_across_chunks(self, chunks: List[str], total_questions: int) -> List[int]:
        """Distribute questions across chunks based on their relative sizes"""
        
        if not chunks:
            return []
        
        chunk_sizes = [len(chunk) for chunk in chunks]
        total_size = sum(chunk_sizes)
        
        # Calculate proportional distribution
        questions_per_chunk = []
        distributed = 0
        
        for i, size in enumerate(chunk_sizes):
            if i == len(chunk_sizes) - 1:
                # Last chunk gets remaining questions
                questions_per_chunk.append(total_questions - distributed)
            else:
                proportion = size / total_size
                chunk_questions = max(1, int(total_questions * proportion))  # At least 1 question per chunk
                questions_per_chunk.append(chunk_questions)
                distributed += chunk_questions
        
        return questions_per_chunk
    
    def _create_prompt(
        self,
        text: str,
        num_questions: int,
        question_types: List[QuestionType],
        difficulty_levels: List[DifficultyLevel],
        topic: str = None
    ) -> str:
        """Create a detailed prompt for Gemini"""
        
        types_str = ", ".join([t.value.replace("_", " ") for t in question_types])
        difficulty_str = ", ".join([d.value for d in difficulty_levels])
        
        prompt = f"""
You are an expert educational content creator. Based on the following text, create {num_questions} high-quality quiz questions.

Text to analyze:
{text}

Requirements:
- Question types: {types_str}
- Difficulty levels: {difficulty_str} (distribute questions across these difficulty levels)
- Focus on key concepts, facts, and important details from the text
- Ensure questions test comprehension and knowledge retention
- Make questions educational and meaningful
- Mix different difficulty levels throughout the quiz
"""
        
        if topic:
            prompt += f"- Focus specifically on: {topic}\n"
        
        prompt += """
Return your response as a JSON array with the following exact structure:
[
  {
    "question_text": "Your question here",
    "question_type": "multiple_choice" | "true_false" | "open_ended",
    "options": [
      {"text": "Option A", "is_correct": false},
      {"text": "Option B", "is_correct": true},
      {"text": "Option C", "is_correct": false},
      {"text": "Option D", "is_correct": false}
    ],
    "correct_answer": "For true/false or open-ended questions",
    "explanation": "Brief explanation of the correct answer"
  }
]

Important guidelines:
- For multiple choice: Include exactly 4 options with only one correct answer
- For true/false: Set correct_answer to "true" or "false" and omit options array
- For open-ended: Provide a sample correct answer in correct_answer field and omit options array
- Make questions clear and unambiguous
- Ensure incorrect options are plausible but clearly wrong
- Base all questions strictly on the provided text content
- Questions should be at the specified difficulty level
- Include helpful explanations for learning purposes

Return only valid JSON without any additional text or formatting.
"""
        
        return prompt
    
    def _parse_ai_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse the Gemini response and extract questions"""
        try:
            # Clean the response - remove any potential markdown formatting
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            if content.startswith("```"):
                content = content[3:]
            
            questions = json.loads(content)
            
            if not isinstance(questions, list):
                raise ValueError("Response should be a list of questions")
            
            if not questions:
                raise ValueError("No questions generated")
            
            return questions
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {str(e)}")
            logger.error(f"Raw response: {content}")
            raise HTTPException(status_code=500, detail="Invalid AI response format")
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to parse AI response")
    
    def _convert_to_question_objects(
        self,
        questions_data: List[Dict[str, Any]],
        question_types: List[QuestionType]
    ) -> List[Question]:
        """Convert parsed data to Question objects"""
        
        questions = []
        
        for q_data in questions_data:
            try:
                question_type = QuestionType(q_data.get("question_type", "multiple_choice"))
                
                # Ensure the question type is in the requested types
                if question_type not in question_types:
                    question_type = question_types[0]  # Default to first requested type
                
                options = None
                correct_answer = None
                
                if question_type == QuestionType.MULTIPLE_CHOICE:
                    options_data = q_data.get("options", [])
                    if options_data:
                        options = [
                            MultipleChoiceOption(
                                text=opt["text"],
                                is_correct=opt["is_correct"]
                            )
                            for opt in options_data
                        ]
                    else:
                        logger.warning(f"No options provided for multiple choice question: {q_data.get('question_text', '')}")
                        continue
                else:
                    correct_answer = q_data.get("correct_answer")
                
                question = Question(
                    id=str(uuid.uuid4()),
                    question_text=q_data["question_text"],
                    question_type=question_type,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=q_data.get("explanation")
                )
                
                questions.append(question)
            
            except Exception as e:
                logger.warning(f"Skipping invalid question: {str(e)}")
                logger.warning(f"Question data: {q_data}")
                continue
        
        if not questions:
            raise HTTPException(status_code=500, detail="No valid questions generated")
        
        return questions
    
    def test_connection(self) -> bool:
        """Test if Gemini API is accessible"""
        try:
            response = self.model.generate_content(
                "Say 'Hello' if you can understand this message.",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10
                )
            )
            return "hello" in response.text.lower()
        except Exception as e:
            logger.error(f"Gemini API test failed: {str(e)}")
            return False