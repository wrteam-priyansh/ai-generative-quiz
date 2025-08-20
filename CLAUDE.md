# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start development server
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Environment Setup
Required environment variables must be configured in `.env`:
- `GOOGLE_GEMINI_API_KEY` - Google AI Studio API key for question generation
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` - Google OAuth credentials for Forms API
- `SECRET_KEY` - Random string for session management

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Test Gemini connectivity
curl http://localhost:8000/quiz/test-gemini

# Get API documentation
curl http://localhost:8000/quiz/usage-examples
```

## Architecture Overview

### Core Service Architecture
The application follows a **service-oriented architecture** with four main integration layers:

1. **Text Processing Pipeline**: `text_extraction.py` → `text_chunking.py` → `gemini_service.py`
2. **Google Integration**: `auth_service.py` → `google_forms_service.py`
3. **File Generation Pipeline**: `file_generation_service.py` → Professional TXT/PDF downloads
4. **Response Standardization**: All endpoints use `response.py` helpers for consistent `{error, data, message}` format

### Key Architectural Patterns

#### Smart Text Chunking
Large documents are automatically chunked when exceeding `GEMINI_MAX_INPUT_CHARS` (default: 4000). The chunking strategy:
- Primary: Paragraph-based splitting
- Fallback: Sentence-based splitting  
- Last resort: Word-based splitting
Questions are distributed proportionally across chunks based on content size.

#### Multi-Type Input Handling
Both question types and difficulty levels support flexible input parsing:
- `question_types`: Accepts "mcq", "multiple_choice", "tf", "true_false", "essay", "open_ended"
- `difficulty_levels`: Accepts "easy", "basic", "medium", "intermediate", "hard", "advanced"

#### Standardized Response Format
All API responses follow the pattern:
```json
{
  "error": false,
  "data": { /* actual response content */ },
  "message": "Success description"
}
```
Use `success_response()` and `error_response()` helpers from `app.models.response`.

### Service Dependencies
- **GeminiQuestionGenerationService**: Requires `GOOGLE_GEMINI_API_KEY`, handles both single-text and chunked processing
- **GoogleAuthService**: Manages OAuth flow, requires Google Cloud Console setup
- **GoogleFormsService**: Creates forms with up to 40 questions, requires authenticated credentials
- **TextExtractionService**: Processes PDF/DOCX/TXT files without external dependencies
- **FileGenerationService**: Generates TXT and PDF downloads using ReportLab, no external dependencies

## Configuration Management

### Critical Settings in `app/core/config.py`
- `MAX_QUESTIONS_PER_QUIZ: int = 40` - Maximum questions per generation
- `GEMINI_MAX_INPUT_CHARS: int = 4000` - Text chunking threshold
- `ENABLE_TEXT_CHUNKING: bool = True` - Toggle chunking for large texts
- `MAX_FILE_SIZE: int = 10MB` - File upload limit
- `ALLOWED_FILE_TYPES: List[str] = ["pdf", "docx", "txt"]`

### Router-Specific Behavior
- **Quiz router** (`/quiz`): Handles both text and file input with automatic chunking
- **Auth router** (`/auth`): Manages Google OAuth flow and token refresh
- **Forms router** (`/forms`): Creates Google Forms, requires Authorization header with credentials JSON
- **Download endpoints** (`/quiz/download`): Generate formatted files from quiz questions in JSON format

## Working with Question Generation

### Supported Input Combinations
```python
# Multiple question types and difficulty levels
{
  "question_types": ["multiple_choice", "true_false", "open_ended"],
  "difficulty_levels": ["basic", "intermediate", "advanced"],
  "num_questions": 20  # Up to 40 supported
}
```

### File Upload Processing
File uploads automatically extract text and apply the same chunking logic as text input. The response includes `text_processing` metadata showing whether chunking was used.

### Google Forms Integration
Forms are created with automatic question type conversion:
- `multiple_choice` → Radio buttons with correct answer marking
- `true_false` → Radio buttons (True/False)
- `open_ended` → Paragraph text input
Quiz mode is enabled by default with automatic scoring.

## Error Handling

### Custom Exception Types
- `QuizGenerationException` - AI service failures
- `TextExtractionException` - Document processing errors  
- `GoogleAPIException` - Google service integration issues
- `AuthenticationException` - OAuth and credential problems

All exceptions are automatically caught and converted to standardized error responses via registered exception handlers in `main.py`.

## Key Integration Points

### Google Services Setup
1. Enable Google Forms API and Google Drive API in Google Cloud Console
2. Create OAuth 2.0 credentials with authorized redirect URI: `http://localhost:8000/auth/callback`
3. Get Gemini API key from Google AI Studio

### Text Processing Flow
Large documents trigger automatic chunking, with questions distributed across chunks proportionally. The system preserves context by splitting on paragraph boundaries first, falling back to sentences, then words if necessary.

### Response Enhancement
All quiz generation responses include `quiz_settings` and `text_processing` metadata to inform clients about the processing that occurred, including whether chunking was used and what parameters were applied.

## File Download System

### Download Endpoints
- `POST /quiz/download/txt` - Generate formatted TXT file with questions
- `POST /quiz/download/pdf` - Generate professional PDF using ReportLab 
- `POST /quiz/download/answer-key` - Generate answer key in TXT format

### Download Request Format
All download endpoints accept JSON requests with the following structure:
```json
{
  "questions": [
    {
      "id": "uuid",
      "question_text": "Question content",
      "question_type": "multiple_choice",
      "options": [
        {"text": "Option A", "is_correct": false},
        {"text": "Option B", "is_correct": true}
      ],
      "explanation": "Optional explanation"
    }
  ],
  "include_answers": true,  // TXT/PDF only
  "topic": "Optional topic name",
  "difficulty_levels": ["intermediate", "advanced"]  // Optional metadata
}
```

### File Generation Features
- **Professional PDF formatting**: Multi-page layout with proper styling, headers, and page breaks
- **Answer marking**: Visual indicators (✓) for correct answers when `include_answers: true`
- **Metadata inclusion**: Topic, generation date, difficulty levels in file headers
- **Multiple formats**: Questions-only or questions-with-answers for TXT files
- **Automatic filenames**: Generated based on topic and timestamp
- **Streaming responses**: Files are generated and streamed directly without temporary storage

### Working with Downloads
After generating a quiz using `/quiz/generate` or `/quiz/generate-from-file`, extract the `questions` array from the response data and POST it to any download endpoint:

```python
# 1. Generate quiz
quiz_response = POST("/quiz/generate", {...})
questions = quiz_response["data"]["questions"]

# 2. Download as PDF with answers
pdf_response = POST("/quiz/download/pdf", {
    "questions": questions,
    "include_answers": True,
    "topic": "My Quiz Topic"
})
```

The FileGenerationService handles all formatting automatically, including question type-specific formatting, option labeling (A, B, C, D), and professional document structure.

## Enhanced API Documentation

### Interactive Response Examples
All API endpoints now include comprehensive response examples in the FastAPI documentation at `/docs`:

- **Multiple Scenarios**: Success/failure cases, different question types, mixed formats
- **Real JSON Data**: Actual response structures with realistic sample data  
- **Question Type Showcase**: Demonstrates the consistent options array format for true/false questions
- **OAuth Flow Examples**: Complete authentication flow with real URLs and responses
- **Error Cases**: Detailed error response examples with specific error messages

### Documentation Access
- **FastAPI Docs**: `http://localhost:8000/docs` - Interactive API documentation
- **Usage Examples**: `GET /quiz/usage-examples` - Comprehensive API usage guide
- **Debug Information**: `GET /auth/debug` - OAuth configuration debugging

## OAuth Integration Enhancements

### Fixed OAuth Flow Issues
- **Scope Management**: Resolved OAuth scope mismatch by including `openid` scope proactively
- **Frontend Redirect**: Backend now redirects to frontend after successful authentication instead of returning JSON
- **Error Handling**: Enhanced error messages for common OAuth issues (`invalid_grant`, `scope_mismatch`)

### OAuth Flow Process
1. **Authorization**: `GET /auth/google/authorize?state=<frontend_url>` 
2. **User Authentication**: Google OAuth consent screen
3. **Backend Processing**: Token exchange and validation
4. **Frontend Redirect**: Automatic redirect to frontend with auth results in URL parameters

### OAuth Response Format
After successful authentication, users are redirected to:
```
http://localhost:3000/generate?auth=success&user_email=user@example.com&user_name=John%20Doe&credentials=eyJ0b2tlbiI6InlhMjk...
```

Frontend can extract authentication data:
```javascript
const urlParams = new URLSearchParams(window.location.search);
const authStatus = urlParams.get('auth'); // 'success' or 'error'
const credentialsB64 = urlParams.get('credentials');
const credentials = JSON.parse(atob(credentialsB64)); // Decode credentials
```

### OAuth Debugging
- **Debug Endpoint**: `GET /auth/debug` provides configuration validation
- **Enhanced Logging**: Detailed OAuth flow tracking in application logs
- **Error Categorization**: Specific error types with troubleshooting guidance

## AI Question Generation Improvements

### True/False Question Format Standardization
True/false questions now use consistent options array format:
```json
{
  "question_type": "true_false",
  "options": [
    {"text": "True", "is_correct": true},
    {"text": "False", "is_correct": false}
  ],
  "correct_answer": null,
  "explanation": "Natural explanation without text references"
}
```

### Enhanced Question Quality
- **Natural Explanations**: Removed mechanical text references ("The text states..." → natural explanations)
- **Strict Type Enforcement**: AI generates only requested question types with proper distribution
- **Smart Distribution**: Questions are distributed proportionally across requested types and difficulty levels
- **Improved Prompts**: Enhanced prompt engineering for better educational content

### Question Type Distribution
When requesting multiple question types, the system automatically distributes questions:
- Single type: ALL questions of that type
- Multiple types: Proportional distribution (e.g., 5 questions → 3 MCQ, 2 T/F)
- Fallback handling: If AI deviates, system enforces requested types