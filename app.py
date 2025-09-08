# Import necessary libraries
import streamlit as st
import openai
from brain import get_index_for_pdf
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up the OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure Streamlit page
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    
    .stApp {
        background-color: #f8f9fa;
    }
    
    .center-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-height: 60vh;
    }
    
    .sparkle-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: #6366f1;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1f2937;
        margin-bottom: 2rem;
    }
    
    .suggestion-cards {
        display: flex;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .suggestion-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        min-width: 200px;
        max-width: 280px;
    }
    
    .suggestion-card:hover {
        border-color: #6366f1;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
        transform: translateY(-2px);
    }
    
    .suggestion-text {
        color: #374151;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    .upload-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 2px dashed #d1d5db;
        text-align: center;
    }
    
    .stChatMessage {
        background: white;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .stChatInputContainer {
        background: white;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .suggestions-header {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 1rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# Cached function to create a vectordb for the provided PDF files
@st.cache_resource
def create_vectordb(files, filenames):
    # Show a spinner while creating the vectordb
    with st.spinner("Creating vector database..."):
        vectordb = get_index_for_pdf(
            [file.getvalue() for file in files], filenames, openai.api_key
        )
    return vectordb

# Initialize session state
if "conversation_started" not in st.session_state:
    st.session_state.conversation_started = False
if "vectordb" not in st.session_state:
    st.session_state.vectordb = None

# Main UI Logic
if not st.session_state.conversation_started and not st.session_state.vectordb:
    # Landing page with centered content
    st.markdown('<div class="center-content">', unsafe_allow_html=True)
    
    # Sparkle icon and main title
    st.markdown('<div class="sparkle-icon">✨</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">Ask our AI anything</h1>', unsafe_allow_html=True)
    
    # PDF Upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.markdown("**Upload your PDF documents to get started**")
    pdf_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True, key="pdf_uploader")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # If PDF files are uploaded, create the vectordb
    if pdf_files:
        pdf_file_names = [file.name for file in pdf_files]
        st.session_state["vectordb"] = create_vectordb(pdf_files, pdf_file_names)
        st.rerun()
    
    # Suggestion cards
    st.markdown('<div class="suggestions-header">Suggestions on what to ask Our AI</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("What can I ask you to do?", key="suggestion1", use_container_width=True):
            st.session_state.conversation_started = True
            st.session_state.suggested_question = "What can I ask you to do?"
            st.rerun()
    
    with col2:
        if st.button("Which one of my projects is performing the best?", key="suggestion2", use_container_width=True):
            st.session_state.conversation_started = True
            st.session_state.suggested_question = "Which one of my projects is performing the best?"
            st.rerun()
    
    with col3:
        if st.button("What projects should I be concerned about right now?", key="suggestion3", use_container_width=True):
            st.session_state.conversation_started = True
            st.session_state.suggested_question = "What projects should I be concerned about right now?"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # Chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Define the template for the chatbot prompt
    prompt_template = """
        You are a helpful Assistant who answers to users questions based on multiple contexts given to you.

        Keep your answer short and to the point.
        
        The evidence are the context of the pdf extract with metadata. 
        
        Carefully focus on the metadata specially 'filename' and 'page' whenever answering.
        
        Make sure to add filename and page number at the end of sentence you are citing to.
            
        Reply "Not applicable" if text is irrelevant.
         
        The PDF content is:
        {pdf_extract}
    """

    # Header with back button
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("← Back", key="back_button"):
            st.session_state.conversation_started = False
            st.session_state.vectordb = None
            if "prompt" in st.session_state:
                del st.session_state["prompt"]
            st.rerun()
    
    with col2:
        st.markdown("### 💬 Chat with your documents")

    # Get the current prompt from the session state or set a default value
    prompt = st.session_state.get("prompt", [{"role": "system", "content": "none"}])

    # Handle suggested question from landing page
    if "suggested_question" in st.session_state and st.session_state.suggested_question:
        question = st.session_state.suggested_question
        st.session_state.suggested_question = None
    else:
        question = None

    # Display previous chat messages
    for message in prompt:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Get the user's question using Streamlit's chat input
    if not question:
        question = st.chat_input("Ask me anything about your documents...")

    # Handle the user's question
    if question:
        vectordb = st.session_state.get("vectordb", None)
        if not vectordb:
            with st.chat_message("assistant"):
                st.write("You need to provide a PDF first. Please go back and upload your documents.")
                st.stop()

        # Search the vectordb for similar content to the user's question
        search_results = vectordb.similarity_search(question, k=3)
        pdf_extract = "/n ".join([result.page_content for result in search_results])

        # Update the prompt with the pdf extract
        prompt[0] = {
            "role": "system",
            "content": prompt_template.format(pdf_extract=pdf_extract),
        }

        # Add the user's question to the prompt and display it
        prompt.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        # Display an empty assistant message while waiting for the response
        with st.chat_message("assistant"):
            botmsg = st.empty()

        # Call ChatGPT with streaming and display the response as it comes
        response = []
        result = ""
        client = openai.OpenAI()
        for chunk in client.chat.completions.create(
            model="gpt-4", messages=prompt, stream=True
        ):
            if chunk.choices[0].delta.content is not None:
                response.append(chunk.choices[0].delta.content)
                result = "".join(response).strip()
                botmsg.write(result)

        # Add the assistant's response to the prompt
        prompt.append({"role": "assistant", "content": result})

        # Store the updated prompt in the session state
        st.session_state["prompt"] = prompt
    
    st.markdown('</div>', unsafe_allow_html=True)
