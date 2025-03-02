"""Streamlit application for Open NotebookLM."""

import streamlit as st

from src.services.pdf_parser import PDFParserService
from src.services.source import SourceService


# Initialize services
@st.cache_resource
def get_source_service() -> SourceService:
    """Get or create a cached source service instance."""
    return SourceService()


def initialize_session_state() -> None:
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "uploaded_source" not in st.session_state:
        st.session_state.uploaded_source = None
    if "source_id" not in st.session_state:
        st.session_state.source_id = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0


def handle_upload(content: str | None) -> None:
    """Handle source content upload."""
    if content:
        # Store the source content and create a source
        st.session_state.uploaded_source = content
        source_service = get_source_service()
        source = source_service.create_source(content)
        st.session_state.source_id = str(source.id)
        st.rerun()


def show_upload_modal():
    """Show modal dialog for source material upload."""
    source_content = None

    with st.popover("Upload Source Material"):
        source_type = st.radio("Select source type:", ["Text", "PDF"])

        if source_type == "PDF":
            uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
            if uploaded_file is not None:
                pdf_parser = PDFParserService()
                source_content = pdf_parser.extract_text(uploaded_file.read())
                if not source_content:
                    st.error(
                        "Failed to extract text from the PDF. Please try another file."
                    )
        else:
            source_content = st.text_area("Enter or paste text content", height=200)

        if st.button("Upload"):
            if source_content:
                handle_upload(source_content)
            else:
                st.error("Please provide some content to upload.")


def show_sources_list() -> None:
    """Display list of available sources with pagination."""
    source_service = get_source_service()
    page_size = 5

    sources = source_service.list_sources(
        limit=page_size, offset=st.session_state.current_page * page_size
    )

    if not sources.data:
        st.info("No sources available")
        return

    for source in sources.data:
        col1, col2 = st.columns([4, 1])
        with col1:
            summary = source_service.get_source_summary(str(source.id))
            if summary:
                st.write(f"**Source {source.id}**")
                st.write(summary.summary)
            else:
                preview = (
                    source.content[:100] + "..."
                    if len(source.content) > 100
                    else source.content
                )
                st.write(f"**Source {source.id}**")
                st.write(preview)

        with col2:
            # Select button replaces current source
            if st.button("Select", key=f"select_{source.id}"):
                st.session_state.source_id = str(source.id)
                st.session_state.uploaded_source = source.content
                st.session_state.messages = []
                st.rerun()

            if st.button("Delete", key=f"delete_{source.id}"):
                source_service.delete_source(str(source.id))
                if st.session_state.source_id == str(source.id):
                    st.session_state.source_id = None
                    st.session_state.uploaded_source = None
                    st.session_state.messages = []
                st.rerun()

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.current_page > 0:
            if st.button("Previous"):
                st.session_state.current_page -= 1
                st.rerun()

    with col2:
        st.write(f"Page {st.session_state.current_page + 1}")

    with col3:
        if len(sources.data) == page_size:
            if st.button("Next"):
                st.session_state.current_page += 1
                st.rerun()


def chat_interface() -> None:
    """Display chat interface for source Q&A."""
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the source"):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.status("Generating response..."):
                source_service = get_source_service()
                response = source_service.get_response(
                    st.session_state.source_id, prompt
                )

                # Stream the response
                message = {"role": "assistant", "content": response}
                st.write_stream(response.split())
                st.session_state.messages.append(message)


def main() -> None:
    """Main Streamlit application."""
    st.title("Open NotebookLM")
    st.subheader("AI-Powered Source Analysis Assistant")

    # Initialize session state
    initialize_session_state()

    # Upload and source management in sidebar
    with st.sidebar:
        st.button("Upload Source Material", on_click=show_upload_modal)

        # Show sources list
        st.subheader("Available Sources")
        show_sources_list()

        if st.session_state.uploaded_source:
            st.success("Source material loaded")
            if st.button("Clear Current Source"):
                st.session_state.uploaded_source = None
                st.session_state.source_id = None
                st.session_state.messages = []
                st.rerun()

    # Main chat interface
    if st.session_state.uploaded_source:
        chat_interface()
    else:
        st.info("Please select or upload source material to begin the conversation.")


if __name__ == "__main__":
    main()
