"""Streamlit application for NotebookLM."""

import streamlit as st

from src.services.note import NoteService


# Initialize services
@st.cache_resource
def get_note_service():
    """Get or create a cached note service instance."""
    return NoteService()


def main():
    """Main Streamlit application."""
    st.title("NotebookLM")
    st.subheader("AI-Powered Note Taking Assistant")

    # Initialize services
    note_service = get_note_service()

    # Sidebar for search
    with st.sidebar:
        st.subheader("Search Notes")
        search_query = st.text_input("Search by content or topic")
        search_tags = st.text_input("Filter by tags (comma-separated)")

        if search_query:
            tags = (
                [tag.strip() for tag in search_tags.split(",")] if search_tags else None
            )
            results = note_service.search_notes(search_query, tags=tags)

            if results:
                st.subheader("Search Results")
                for result in results:
                    with st.expander(f"Score: {result.score:.2f}"):
                        st.text(result.note.content[:200] + "...")
                        if result.summary:
                            st.markdown("**Key Points:**")
                            for point in result.summary.key_points:
                                st.markdown(f"- {point}")

    # Main content area - Note Input
    st.subheader("Create New Note")
    note_input = st.text_area("Enter your note", height=200)
    tags_input = st.text_input("Add tags (comma-separated)")

    if st.button("Process Note"):
        if note_input:
            tags = (
                [tag.strip() for tag in tags_input.split(",")] if tags_input else None
            )
            note = note_service.create_note(note_input, tags=tags)
            summary = note_service.get_summary(str(note.id))

            st.success("Note processed successfully!")

            # Display results
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Summary")
                st.write(summary.summary)

                st.subheader("Key Points")
                for point in summary.key_points:
                    st.markdown(f"- {point}")

            with col2:
                st.subheader("Extracted Information")

                if summary.entities["dates"]:
                    st.markdown("**Dates:**")
                    for date in summary.entities["dates"]:
                        st.markdown(f"- {date}")

                if summary.entities["names"]:
                    st.markdown("**Names:**")
                    for name in summary.entities["names"]:
                        st.markdown(f"- {name}")

                if summary.entities["actions"]:
                    st.markdown("**Action Items:**")
                    for action in summary.entities["actions"]:
                        st.markdown(f"- {action}")
        else:
            st.warning("Please enter some text to process.")


if __name__ == "__main__":
    main()
