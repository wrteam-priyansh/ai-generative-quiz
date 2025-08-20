# AI Quiz Generator Backend

A FastAPI backend service for generating quiz questions using AI and creating Google Forms automatically.

## Features

- **AI-Powered Question Generation**: Uses Google Gemini to generate quiz questions from text or uploaded documents
- **Document Processing**: Supports PDF, DOCX, and TXT file formats for text extraction with smart chunking
- **Google Forms Integration**: Automatically creates Google Forms with generated questions
- **Google OAuth 2.0**: Secure authentication for Google Forms access
- **Multiple Question Types**: Supports multiple-choice, true/false, and open-ended questions
- **Multiple Difficulty Levels**: Generate questions across basic, intermediate, and advanced difficulty levels
- **Smart Text Chunking**: Handles large documents by intelligently splitting content while preserving context
- **Flexible Input Options**: Accept various question type and difficulty level formats (synonyms and abbreviations)
- **Enhanced Customization**: Configure up to 40 questions, multiple question types, multiple difficulty levels, and topic focus
- **Standardized API Responses**: Consistent `{error, data, message}` response format across all endpoints

## Prerequisites

- Python 3.8+
- Google Gemini API key
- Google Cloud Console project with Forms API enabled
- Google OAuth 2.0 credentials

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-generative-quiz
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
SECRET_KEY=your_secret_key_here
ALLOWED_ORIGINS=["http://localhost:3000"]
```

## Google Cloud Setup

### Google Forms API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Forms API and Google Drive API
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" in the APIs & Services section
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Set application type to "Web application"
   - Add authorized redirect URI: `http://localhost:8000/auth/callback`
5. Download the credentials and use the client ID and secret in your `.env` file

### Google Gemini API Setup
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key and add it to your `.env` file as `GOOGLE_GEMINI_API_KEY`

## Running the Application

1. Start the development server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Access the API documentation at: http://localhost:8000/docs

## API Endpoints

### Authentication
- `GET /auth/google/authorize` - Get Google OAuth authorization URL
- `GET /auth/callback` - Handle Google OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/validate` - Validate credentials

### Quiz Generation
- `POST /quiz/generate` - Generate quiz from text input (supports multiple question types and difficulty levels)
- `POST /quiz/generate-from-file` - Generate quiz from uploaded file (supports multiple question types and difficulty levels)
- `GET /quiz/test-gemini` - Test Gemini API connection
- `GET /quiz/question-types` - Get available question types
- `GET /quiz/difficulty-levels` - Get available difficulty levels
- `GET /quiz/usage-examples` - Get comprehensive usage examples and API documentation
- `GET /quiz/limits` - Get system limits and configuration

### Google Forms
- `POST /forms/create` - Create Google Form with questions
- `POST /forms/create-from-quiz` - Create form from quiz response
- `GET /forms/{form_id}/responses` - Get form responses
- `DELETE /forms/{form_id}` - Delete form

## Usage Examples

### 1. **Generate Quiz from Text with Multiple Options**:
```bash
curl -X POST "http://localhost:8000/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The American Revolution began in 1775...",
    "num_questions": 10,
    "question_types": ["multiple_choice", "true_false", "open_ended"],
    "difficulty_levels": ["basic", "intermediate", "advanced"],
    "topic": "American History"
  }'
```

### 2. **Generate Quiz from File**:
```bash
curl -X POST "http://localhost:8000/quiz/generate-from-file" \
  -F "file=@history_document.pdf" \
  -F "num_questions=15" \
  -F "question_types=mcq,tf,essay" \
  -F "difficulty_levels=easy,medium,hard" \
  -F "topic=World War 2"
```

### 3. **Create Google Form**:
```bash
curl -X POST "http://localhost:8000/forms/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: <google_credentials_json>" \
  -d '{
    "questions": [...],
    "form_title": "History Quiz",
    "form_description": "Quiz on American Revolution",
    "is_quiz": true
  }'
```

### 4. **Get Usage Examples**:
```bash
curl -X GET "http://localhost:8000/quiz/usage-examples"
```

## Project Structure

```
ai-generative-quiz/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   └── __init__.py
│   ├── models/
│   │   ├── auth.py            # Authentication models
│   │   ├── quiz.py            # Quiz-related models
│   │   └── __init__.py
│   ├── routers/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── forms.py           # Google Forms endpoints
│   │   ├── quiz.py            # Quiz generation endpoints
│   │   └── __init__.py
│   ├── services/
│   │   ├── gemini_service.py  # Google Gemini AI question generation
│   │   ├── auth_service.py    # Google OAuth service
│   │   ├── google_forms_service.py  # Google Forms integration
│   │   ├── text_extraction.py # Document text extraction
│   │   └── __init__.py
│   ├── utils/
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── logging_config.py  # Logging configuration
│   │   ├── validators.py      # Input validation
│   │   └── __init__.py
│   └── __init__.py
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Configuration

The application uses the following configuration options:

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `GOOGLE_REDIRECT_URI`: OAuth redirect URI
- `GOOGLE_GEMINI_API_KEY`: Google Gemini API key for question generation
- `GEMINI_MODEL`: Gemini model to use (default: gemini-1.5-flash)
- `GEMINI_MAX_INPUT_CHARS`: Maximum characters per chunk (default: 4000)
- `ENABLE_TEXT_CHUNKING`: Enable/disable text chunking (default: true)
- `MAX_QUESTIONS_PER_QUIZ`: Maximum questions per quiz (default: 40)
- `MIN_QUESTIONS_PER_QUIZ`: Minimum questions per quiz (default: 1)
- `SECRET_KEY`: Secret key for session management
- `ALLOWED_ORIGINS`: CORS allowed origins
- `MAX_FILE_SIZE`: Maximum file upload size (default: 10MB)
- `ALLOWED_FILE_TYPES`: Supported file types (pdf, docx, txt)

## Error Handling

The application includes comprehensive error handling:

- **QuizGenerationException**: AI service errors
- **TextExtractionException**: Document processing errors
- **GoogleAPIException**: Google API integration errors
- **AuthenticationException**: OAuth authentication errors
- **ValidationError**: Request validation errors

## Logging

Logs are written to both console and `app.log` file. Log levels can be configured via environment variables.

## Limitations

- Maximum 40 questions per quiz
- File size limit: 10MB
- Supported file types: PDF, DOCX, TXT (text-only)
- Minimum text length: 50 characters for meaningful quiz generation
- Google Forms API quotas apply
- No image processing - text-based content only
- Text chunking at 4000 characters per chunk (configurable)
- Gemini API rate limits apply

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.