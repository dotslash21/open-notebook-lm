# NotebookLM

An AI-powered note-taking and research assistant that helps you capture, summarize, and organize your notes with advanced features like semantic search and key information extraction.

## Features (Phase 1a)

- Natural language note capture
- AI-powered summarization
- Automatic extraction of key points, dates, names, and action items
- Semantic search with tag filtering
- Clean and intuitive Streamlit interface

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

Current phase: 1a (Text Ingestion)
- [x] Core note processing functionality
- [x] LLM integration
- [x] Vector storage setup
- [x] Basic search capabilities
- [x] Streamlit UI

Next phase: 1b (PDF Ingestion)
- [ ] PDF file upload support
- [ ] PDF text extraction
- [ ] Integration with existing summarization pipeline

## Project Structure

```
open-notebook-lm/
├── docs/               # Documentation
├── src/               # Source code
│   ├── config/        # Configuration
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   └── ui/           # Streamlit interface
├── .env.template      # Environment template
├── main.py           # Application entry
└── README.md         # This file
```

## License

[Add your license information here]
