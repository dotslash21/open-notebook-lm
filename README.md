# Open NotebookLM

An AI-powered note-taking and research assistant that helps you organize and understand your documents through intelligent summarization, interactive Q&A, and information extraction.

This tool enables you to:
- Capture and Organize Information: Import PDF or plain text notes and have the system help organize and structure large amounts of information.
- Summarize Content: Automatically generate summaries of lengthy documents, making it easier to digest and recall important points.
- Interactive Q&A: Engage in a conversational interface to ask follow-up questions about your material, allowing for deeper insights and connections between ideas.
- Enhance Research Efficiency: The AI assists in identifying key themes and connections, enabling more efficient retrieval of information and a better understanding of complex topics.

## Features

Phase 1a: Text Ingestion
- Natural language note capture
- AI-powered summarization
- Automatic extraction of key points, dates, names, and action items
- Semantic search with tag filtering
- Clean and intuitive Streamlit interface

Phase 1b: PDF Ingestion
- PDF file upload support
- Automatic text extraction from PDF documents
- Integration with summarization pipeline
- Unified processing for both text and PDF inputs

## Requirements

- Python 3.12+
- OpenAI API access or compatible API endpoint
- Qdrant vector database (running locally or remote instance)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd open-notebook-lm
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

4. Configure environment variables:
```bash
cp .env.template .env
```
Edit `.env` and add your configuration:
- `OPENAI_API_KEY`: Your OpenAI API key or compatible service key
- `OPENAI_BASE_URL`: Base URL for the OpenAI-compatible API
- `QDRANT_HOST`: Qdrant server host (default: localhost)
- `QDRANT_PORT`: Qdrant server port (default: 6333)

5. Start Qdrant:
You can run Qdrant using Docker:
```bash
docker run -p 6333:6333 qdrant/qdrant
```
Or install and run it locally following the [Qdrant installation guide](https://qdrant.tech/documentation/quick_start/).

## Usage

Start the Streamlit application:
```bash
streamlit run src/ui/app.py
```

The application will be available at `http://localhost:8501` with the following features:
- Create and process new notes
- View AI-generated summaries and extracted information
- Search through your notes using natural language queries
- Filter search results by tags

## Development Status

Current phase: 1b (PDF Ingestion)
- [x] Core note processing functionality
- [x] LLM integration
- [x] Vector storage setup
- [x] Basic search capabilities
- [x] Streamlit UI
- [x] PDF file upload support
- [x] PDF text extraction
- [x] Integration with existing summarization pipeline

Phase 2: Source-Grounded Q&A
- [x] Plain text source upload support
- [x] Source-grounded query responses
- [x] Natural language Q&A interface
- [x] RAG-like response generation

Phase 3: Enhanced Text Processing
- [x] Advanced text preprocessing
  • Whitespace and Unicode normalization
  • Headers/footers removal
  • Line and paragraph standardization
  • Section boundary detection
- [x] Intelligent chunking strategy
  • 400 token chunks with overlap
  • Chunk linking for context
  • Section and page metadata
  • Source position tracking
- [x] Enhanced retrieval system
  • Chunk-based semantic search
  • Multi-metric reranking
  • Efficient data storage
  • Structure-aware results

## Project Structure

```
open-notebook-lm/
├── docs/                # Documentation
├── src/                # Source code
│   ├── config/         # Configuration
│   ├── models/         # Data models
│   │   └── source.py   # Source and chunk models
│   ├── services/       # Business logic
│   │   ├── llm.py     # LLM integration
│   │   ├── source.py  # Source processing
│   │   └── text_processing.py  # Text preprocessing
│   └── ui/            # Streamlit interface
├── .env.template       # Environment template
├── main.py            # Application entry
└── README.md          # This file
```

## License

[Add your license information here]
