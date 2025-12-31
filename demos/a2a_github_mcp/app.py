"""Streamlit UI for A2A MCP Lab."""

import sys
import warnings
import asyncio
from pathlib import Path

# Add the a2a_github_mcp directory to Python path
current_file = Path(__file__).resolve()
current_dir = current_file.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Suppress warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="crewai.telemetry")
warnings.filterwarnings("ignore", message=".*signal only works in main thread.*")

import streamlit as st
import logging
import re
from typing import Dict, Any, List

# Import using absolute imports from current directory
import crew
import config as app_config

# Create aliases for cleaner usage
run_crew = crew.run_crew
config = app_config.config

# Import and setup custom logging
from logging_config import setup_logging, get_agent_logger
setup_logging(level=logging.INFO, verbose=False)
logger = logging.getLogger(__name__)

# Suppress specific log messages from CrewAI telemetry
logging.getLogger("crewai.telemetry").setLevel(logging.ERROR)

# Page configuration
st.set_page_config(
    page_title="A2A MCP Lab",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .answer-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .citation-box {
        background-color: #e8f4f8;
        padding: 0.5rem 1rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_citations_as_github_links(text: str) -> str:
    """
    Convert citations in format (owner/repo/path) to clickable GitHub markdown links.
    
    Pattern: (owner/repo/path/to/file) -> [owner/repo/path/to/file](https://github.com/owner/repo/blob/main/path/to/file)
    """
    # Pattern to match citations like (owner/repo/path) or (owner/repo/path/to/file.py)
    citation_pattern = r'\(([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_./-]+)*)\)'
    
    def replace_citation(match):
        citation_path = match.group(1)
        # Extract owner and repo from the path
        parts = citation_path.split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            # Get the file path (everything after repo name)
            file_path = '/'.join(parts[2:]) if len(parts) > 2 else ''
            
            # Build GitHub URL
            if file_path:
                github_url = f"https://github.com/{owner}/{repo}/blob/main/{file_path}"
            else:
                github_url = f"https://github.com/{owner}/{repo}"
            
            # Return markdown link format
            return f"([{citation_path}]({github_url}))"
        
        return match.group(0)  # Return original if pattern doesn't match expected format
    
    # Replace all citations
    formatted_text = re.sub(citation_pattern, replace_citation, text)
    
    return formatted_text


def extract_citations_and_repos(text: str) -> tuple[List[str], List[str]]:
    """
    Extract citations and unique repositories from the response text.
    
    Returns:
        Tuple of (citations_list, repos_list)
    """
    citations_set = set()  # Use set to avoid duplicates
    repos = set()
    
    # Pattern for markdown links: [text](url)
    link_pattern = r'\[([^\]]+)\]\((https://github\.com/([^/]+)/([^/]+)(?:/blob/[^/]+/(.+?))?)\)'
    
    for match in re.finditer(link_pattern, text):
        link_text = match.group(1)
        full_url = match.group(2)
        owner = match.group(3)
        repo = match.group(4)
        file_path = match.group(5) if match.group(5) else ''
        
        # Build citation markdown link (use the original URL from the text)
        citation = f"[{link_text}]({full_url})"
        citations_set.add(citation)
        
        # Add to repos set
        repos.add(f"{owner}/{repo}")
    
    # Also look for plain (owner/repo/path) format if not already in a markdown link
    # Only extract if it's not already part of a markdown link we've seen
    plain_citation_pattern = r'(?<!\[)\(([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)(?:/([a-zA-Z0-9_./-]+))?\)'
    for match in re.finditer(plain_citation_pattern, text):
        owner = match.group(1)
        repo = match.group(2)
        file_path = match.group(3) if match.group(3) else ''
        repos.add(f"{owner}/{repo}")
        
        # Create citation
        if file_path:
            citation = f"[{owner}/{repo}/{file_path}](https://github.com/{owner}/{repo}/blob/main/{file_path})"
        else:
            citation = f"[{owner}/{repo}](https://github.com/{owner}/{repo})"
        
        citations_set.add(citation)
    
    # Convert set to sorted list for consistent ordering
    citations_list = sorted(list(citations_set))
    
    return citations_list, sorted(list(repos))


def process_user_question(question: str) -> Dict[str, Any]:
    """
    Process a user question through the crew workflow and return structured result.
    
    Args:
        question: User's question
    
    Returns:
        Dictionary with 'answer', 'citations', 'repos_accessed', and 'notes'
    """
    try:
        # Run the crew
        answer = run_crew(question)
        
        # Format citations as clickable GitHub links
        formatted_answer = format_citations_as_github_links(answer)
        
        # Extract citations and repos
        citations, repos_accessed = extract_citations_and_repos(formatted_answer)
        
        # Build result dictionary
        result = {
            "answer": formatted_answer,
            "citations": citations,
            "repos_accessed": repos_accessed,
            "notes": None,  # Could be extracted from answer if needed
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise


def main():
    st.markdown('<div class="main-header">A2A MCP Lab</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">CrewAI Agents with GitHub MCP Server</div>',
        unsafe_allow_html=True,
    )

    # Sidebar with information
    with st.sidebar:
        st.header("About")
        st.write(
            "This lab demonstrates CrewAI agents communicating via A2A protocol "
            "while using GitHub MCP server to fetch code from allowlisted repositories."
        )
        st.write(
            "**Ask questions about code implementation** - the agents will search and fetch "
            "relevant code from the allowlisted repositories."
        )

        st.header("Allowlisted Repositories")
        repos = config.get_allowlisted_repo_strings()
        for repo in repos:
            st.code(f"github.com/{repo}", language=None)

        st.info(
            "💡 **Tip**: Ask questions like 'Write code to implement X' or "
            "'Show me how to do Y' to fetch code examples from these repos."
        )

        st.header("Architecture")
        st.write(
            """
            **Manager Agent**: Orchestrates the workflow
            - Receives user questions
            - Coordinates between Fetcher and Curator agents

            **Fetcher Agent**: Uses GitHub MCP tools
            - Searches allowlisted repositories
            - Fetches relevant code files

            **Curator Agent**: Produces answers
            - Analyzes code context
            - Generates answers with citations
            """
        )

    # Main content area
    st.header("Ask a Question")

    # Example questions - focused on fetching code from allowlisted repos
    st.subheader("Example Questions")
    example_questions = [
        "Write code to implement A2A evaluation from a2a-samples",
        "Show me how to create a CrewAI agent from crewAI repo",
        "How does AutoGen implement agent communication?",
        "Fetch A2A protocol implementation code",
    ]

    cols = st.columns(len(example_questions))
    for i, example in enumerate(example_questions):
        with cols[i]:
            if st.button(f"📝 {example}", key=f"example_{i}", use_container_width=True):
                st.session_state.user_question = example

    # User input
    user_question = st.text_input(
        "Enter your question:",
        value=st.session_state.get("user_question", ""),
        placeholder="e.g., Write code to implement A2A evaluation from a2a-samples repo",
    )

    if st.button("🔍 Search", type="primary", use_container_width=True):
        if not user_question:
            st.warning("Please enter a question.")
            return

        # Process the question
        with st.spinner("Processing your question..."):
            try:
                # Run the crew workflow (synchronous, no need for asyncio here)
                result = process_user_question(user_question)

                # Store result in session state
                st.session_state.last_result = result
                st.session_state.last_question = user_question

            except Exception as e:
                st.error(f"Error processing question: {str(e)}")
                logger.error(f"Error in streamlit app: {e}", exc_info=True)
                return

    # Display results
    if "last_result" in st.session_state:
        result = st.session_state.last_result
        question = st.session_state.get("last_question", "")

        st.divider()

        st.subheader("Question")
        st.write(question)

        st.subheader("Answer")
        st.markdown(f'<div class="answer-box">{result["answer"]}</div>', unsafe_allow_html=True)

        # Citations
        if result.get("citations"):
            st.subheader("Citations")
            for citation in result["citations"]:
                # Use markdown to render the citation link properly (not inside HTML div)
                # The citation is already in markdown format [text](url)
                st.markdown(f"📎 {citation}")

        # Repos accessed
        if result.get("repos_accessed"):
            st.subheader("Repositories Accessed")
            repos_text = ", ".join(result["repos_accessed"])
            st.info(f"🔗 {repos_text}")

        # Notes
        if result.get("notes"):
            st.subheader("Notes")
            st.warning(result["notes"])

        # Expandable details
        with st.expander("View Raw Response"):
            st.json(result)


if __name__ == "__main__":
    main()
