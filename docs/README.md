# NotebookLM Documentation

## Project Overview
NotebookLM is an AI-powered note-taking and research assistant that focuses on capturing, summarizing, and organizing information from various sources.

## Implementation Phases

### Phase 1: MVP Implementation
- [Phase 1a: Text Ingestion](./phase_1a_text_ingestion.md)
  - Basic note capture and processing
  - Text summarization using LLM
  - Vector storage setup
  
- [Phase 1b: PDF Ingestion](./phase_1b_pdf_ingestion.md)
  - PDF file upload and processing
  - Integration with existing summarization pipeline

### Phase 2: Feature Expansion
- Website ingestion capabilities
- Enhanced auto-tagging and categorization
- Knowledge graph visualization
- Improved search and retrieval

## Project Structure
```
open-notebook-lm/
├── docs/               # Documentation files
├── src/               # Source code
│   ├── config/        # Configuration management
│   ├── models/        # Data models and schemas
│   ├── services/      # Core business logic
│   ├── storage/       # Database and vector store interfaces
│   └── ui/           # Streamlit UI components
└── tests/            # Test files
```

## Environment Setup
1. Create a `.env` file in the project root
2. Configure required environment variables (see `.env.template`)
3. Install dependencies: `pip install -e .`
4. Run the application: `streamlit run src/ui/app.py`
