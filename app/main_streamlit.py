import os
import streamlit as st
import time
from dotenv import load_dotenv
from vector_search import load_vectordb
from chat_utils import create_chat_chain, chatbot, ChatHistory

# Load environment variables and setup initial configurations
def setup():
    """
    Initialize environment and load vector database
    """
    load_dotenv()
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OpenAI API key not found in environment variables")
    
    base_dir = os.path.dirname(__file__)
    vectordb_path = os.path.join(base_dir, 'data', 'vectordb')
    vectordb = load_vectordb(vectordb_path)

    chain = create_chat_chain(openai_api_key)

    return vectordb, chain

# Initialize setup only once
if 'vectordb' not in st.session_state or 'chain' not in st.session_state:
    vectordb, chain = setup()
    st.session_state.vectordb = vectordb
    st.session_state.chain = chain

# Initialize display chat history for Streamlit and LLM chat history separately
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "llm_chat_history" not in st.session_state:
    st.session_state.llm_chat_history = ChatHistory()

st.title("🏫 AI Assistant for the UChicago MS-ADS Program")
st.write("💡 Ask any questions about the MS-ADS Program")

# Display chat messages from display-only history
for entry in st.session_state.chat_history:
    role = "👤" if entry["role"] == "user" else "🤖"
    st.write(f"**{role}:** {entry['content']}")

# Chat input for user to type messages
user_input = st.text_input(
    "Enter your question here:",
    key="input_text" if not st.session_state.get('clear_input', False) else "input_text_new"
)

# Process the user's query and get a response
if user_input:
    # Add user query to display history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Get AI response with conversation history
    response = chatbot(
        user_input, 
        st.session_state.vectordb, 
        st.session_state.chain, 
        st.session_state.llm_chat_history, 
        routing=True, 
        fusion=True
    )
    
    # Add AI response to display history and to LLM chat history
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.session_state.llm_chat_history.add_interaction(user_input, response)

    # Display AI's response gradually
    placeholder = st.empty()
    gradual_text = ""
    
    with st.spinner("Thinking..."):
        for word in response.split():
            gradual_text += word + " "
            placeholder.markdown(f"**🤖:** {gradual_text}")
            time.sleep(0.05)

    # Toggle the input box key to reset the input field
    st.session_state.clear_input = True  # Set to True to clear input

# Reset clear_input flag after the input box has been re-rendered
if st.session_state.get('clear_input', False):
    st.session_state.clear_input = False  # Reset flag after rerendering input box

