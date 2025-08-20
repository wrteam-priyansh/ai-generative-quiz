# Development Documentation

## Project Overview

The AI Quiz Generator is a FastAPI-based backend service that integrates Google Gemini AI for question generation with Google Forms API for quiz creation and distribution. This document tracks the development progress, architecture decisions, and implementation details.

## Development Timeline

### Phase 1: Initial Setup (Completed)
- ✅ FastAPI project structure setup
- ✅ Environment configuration with pydantic-settings
- ✅ Basic router structure (auth, quiz, forms)
- ✅ Dependency management with requirements.txt
- ✅ Logging configuration

### Phase 2: Core Services Implementation (Completed)
- ✅ Text extraction service (PDF, DOCX, TXT)
- ✅ Google OAuth 2.0 authentication service
- ✅ Google Forms API integration service
- ✅ AI question generation service (initially OpenAI, migrated to Gemini)

### Phase 3: AI Integration Enhancement (Completed)
- ✅ Migration from OpenAI to Google Gemini
- ✅ Enhanced prompt engineering for educational content
- ✅ JSON response formatting for structured output
- ✅ Error handling and validation

### Phase 4: Text Processing Enhancement (Completed)
- ✅ Smart text chunking service
- ✅ Paragraph-based and sentence-based splitting
- ✅ Proportional question distribution across chunks
- ✅ Context preservation in chunking
- ✅ Token estimation and size validation

### Phase 5: API Standardization (Completed)
- ✅ Standardized response format `{error, data, message}`
- ✅ Comprehensive error handling
- ✅ Consistent exception handlers
- ✅ Input validation enhancement

### Phase 6: Feature Enhancement (Completed)
- ✅ Multiple question types support
- ✅ Multiple difficulty levels support
- ✅ Flexible input parsing (synonyms and abbreviations)
- ✅ Enhanced customization options
- ✅ Increased question limit to 40

### Phase 7: File Download System (Completed)
- ✅ File generation service implementation
- ✅ TXT file download with formatting
- ✅ PDF file download with ReportLab integration
- ✅ Answer key generation
- ✅ Professional document formatting
- ✅ JSON request body support for downloads

## Architecture

### Core Components

```
ai-generative-quiz/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   └── __init__.py
│   ├── models/
│   │   ├── auth.py            # Authentication models
│   │   ├── quiz.py            # Quiz-related models
│   │   ├── response.py        # Standardized response models
│   │   └── __init__.py
│   ├── routers/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── forms.py           # Google Forms endpoints
│   │   ├── quiz.py            # Quiz generation endpoints
│   │   └── __init__.py
│   ├── services/
│   │   ├── auth_service.py    # Google OAuth service
│   │   ├── gemini_service.py  # Google Gemini AI service
│   │   ├── google_forms_service.py  # Google Forms integration
│   │   ├── text_extraction.py # Document text extraction
│   │   ├── text_chunking.py   # Smart text chunking
│   │   ├── file_generation_service.py  # File download generation
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
├── .gitignore                # Git ignore rules
├── README.md                 # User documentation
└── DEVELOPMENT.md            # This file
```

### Service Architecture

#### 1. **Text Processing Pipeline**
```
Input (Text/File) → Text Extraction → Chunking (if needed) → AI Processing → Questions
```

#### 2. **Google Integration Pipeline**
```
OAuth Flow → Token Management → Forms API → Form Creation
```

#### 3. **Response Flow**
```
Service → Router → Standardized Response → Client
```

## Technical Decisions

### 1. **AI Provider Migration: OpenAI → Google Gemini**
**Reason**: Better integration with Google ecosystem, cost considerations, and JSON response formatting capabilities.

**Implementation**:
- Created dedicated `GeminiQuestionGenerationService`
- Enhanced prompt engineering for educational content
- Structured JSON output validation

### 2. **Text Chunking Strategy**
**Problem**: Large documents exceed AI model input limits and increase costs.

**Solution**: Smart chunking with context preservation
- Paragraph-based splitting (primary)
- Sentence-based splitting (fallback)
- Word-based splitting (last resort)
- Proportional question distribution

### 3. **Multiple Input Types Support**
**Requirement**: Flexible input handling for question types and difficulty levels.

**Implementation**:
- Synonym mapping for user-friendly input
- Robust parsing with fallbacks
- Duplicate removal with order preservation

### 4. **Standardized API Responses**
**Requirement**: Consistent response format across all endpoints.

**Implementation**:
```json
{
  "error": false,
  "data": { /* response data */ },
  "message": "Operation description"
}
```

## Configuration Management

### Environment Variables
- **Required**: `GOOGLE_GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- **Optional**: `GEMINI_MODEL`, `MAX_QUESTIONS_PER_QUIZ`, `ENABLE_TEXT_CHUNKING`

### Default Settings
- Max questions: 40
- Text chunk size: 4000 characters
- File size limit: 10MB
- Supported formats: PDF, DOCX, TXT

## API Design

### Endpoint Categories

#### 1. **Authentication** (`/auth`)
- OAuth URL generation
- Callback handling
- Token management

#### 2. **Quiz Generation** (`/quiz`)
- Text-based generation
- File-based generation
- Configuration endpoints

#### 3. **Google Forms** (`/forms`)
- Form creation
- Response management
- Form deletion

#### 4. **File Downloads** (`/quiz/download`)
- TXT file generation
- PDF file generation with professional formatting
- Answer key generation
- Customizable formatting options

### Input Flexibility

#### Question Types
- **Standard**: `multiple_choice`, `true_false`, `open_ended`
- **Synonyms**: `mcq`, `tf`, `essay`, etc.

#### Difficulty Levels
- **Standard**: `basic`, `intermediate`, `advanced`
- **Synonyms**: `easy/hard`, `simple/complex`, `beginner/expert`

## Testing Strategy

### Manual Testing Endpoints
- `GET /health` - Service health check
- `GET /quiz/test-gemini` - AI service connectivity
- `GET /quiz/usage-examples` - API documentation

### Integration Testing
- OAuth flow validation
- File upload and processing
- AI response validation
- Google Forms creation

## Performance Considerations

### 1. **Text Chunking**
- Reduces AI processing time
- Prevents token limit issues
- Maintains response quality

### 2. **Async Processing**
- FastAPI async endpoints
- Non-blocking file operations
- Concurrent chunk processing

### 3. **Error Resilience**
- Graceful chunk failure handling
- Retry mechanisms for AI calls
- Comprehensive error logging

## Security Measures

### 1. **Authentication**
- OAuth 2.0 implementation
- Secure token management
- Limited API scopes

### 2. **Input Validation**
- File type restrictions
- Size limitations
- Content sanitization

### 3. **Error Handling**
- No sensitive data in error messages
- Proper logging without credentials
- Rate limiting considerations

## Future Enhancements

### Planned Features
- [ ] Question quality scoring
- [ ] Custom prompt templates
- [ ] Batch processing capabilities
- [ ] Question bank management
- [ ] Analytics and reporting
- [ ] Additional file formats (XLSX, CSV)
- [ ] Template customization for downloads
- [ ] Bulk download functionality

### Technical Improvements
- [ ] Caching for frequently generated content
- [ ] Database integration for persistence
- [ ] Background job processing
- [ ] Enhanced monitoring and metrics

## Dependencies

### Core Dependencies
- **FastAPI**: Web framework
- **Google Generative AI**: AI question generation
- **Google API Client**: Forms and OAuth integration
- **PyPDF2**: PDF text extraction
- **python-docx**: DOCX text extraction
- **ReportLab**: PDF generation for downloads

### Development Dependencies
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **python-dotenv**: Environment management

## Monitoring and Logging

### Log Levels
- **INFO**: General operation logs
- **WARNING**: Non-critical issues
- **ERROR**: Service failures
- **DEBUG**: Detailed debugging info

### Metrics to Monitor
- API response times
- AI service latency
- Error rates by endpoint
- File processing success rates

## Deployment Considerations

### Environment Setup
1. Python 3.8+ environment
2. Google Cloud project setup
3. Environment variable configuration
4. Service account permissions

### Scalability
- Horizontal scaling via load balancers
- Stateless service design
- External session management
- API rate limiting

## Development Guidelines

### Code Standards
- Type hints for all functions
- Comprehensive error handling
- Consistent naming conventions
- Proper logging throughout

### Testing Requirements
- Unit tests for core services
- Integration tests for external APIs
- Mock testing for third-party services
- Performance testing for large files

## Troubleshooting

### Common Issues
1. **Gemini API errors**: Check API key and quotas
2. **OAuth failures**: Verify redirect URIs and credentials
3. **File processing errors**: Check file format and size
4. **Chunking issues**: Adjust chunk size settings

### Debug Tools
- `/quiz/test-gemini` endpoint
- Application logs in `app.log`
- Health check endpoints
- Environment variable validation

---

*Last updated: Phase 7 - File Download System completed*
*Next review: After frontend integration and download feature testing*