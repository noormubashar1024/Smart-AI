from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Custom Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state for API key
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")

# Gatekeeper: Ask for API key before showing any other app content
if not st.session_state.api_key:
    st.subheader("Smart AI Assistant")
    st.write("Please enter your OpenAI API key to access the application.")
    
    api_input = st.text_input("OpenAI API Key", type="password")
    if st.button("Submit Key"):
        if api_input:
            st.session_state.api_key = api_input
            os.environ["OPENAI_API_KEY"] = api_input
            st.rerun()
        else:
            st.error("Please enter a valid API key.")
    st.stop()

# --- Main App ---
os.environ["OPENAI_API_KEY"] = st.session_state.api_key

CHAT_DIR = "saved_chats"
os.makedirs(CHAT_DIR, exist_ok=True)

def get_saved_chats():
    """Returns a list of saved chat files sorted by newest first."""
    if not os.path.exists(CHAT_DIR):
        return []
    files = [f for f in os.listdir(CHAT_DIR) if f.endswith(".json")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(CHAT_DIR, x)), reverse=True)
    return files

def get_chat_title(file_path):
    """Reads the JSON file and returns a title based on the first user message."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            # Find the first user message content
            for item in data:
                if item["role"] == "user":
                    text = item["content"]
                    # Truncate to ~30 characters for clean sidebar display
                    return text[:30] + "..." if len(text) > 30 else text
    except:
        pass
    return "New Chat"

# Initialize session state variables
if "current_chat_id" not in st.session_state:
    saved_files = get_saved_chats()
    if saved_files:
        st.session_state.current_chat_id = saved_files[0]
    else:
        st.session_state.current_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

if 'messages' not in st.session_state:
    st.session_state.messages = []
    file_path = os.path.join(CHAT_DIR, st.session_state.current_chat_id)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            chat_data = json.load(f)
            for item in chat_data:
                if item["role"] == "system":
                    st.session_state.messages.append(SystemMessage(content=item["content"]))
                elif item["role"] == "user":
                    st.session_state.messages.append(HumanMessage(content=item["content"]))
                elif item["role"] == "assistant":
                    st.session_state.messages.append(AIMessage(content=item["content"]))

def save_current_chat():
    """Saves current messages to individual JSON file."""
    if not st.session_state.messages:
        return
    chat_data = []
    for msg in st.session_state.messages:
        if isinstance(msg, SystemMessage):
            chat_data.append({"role": "system", "content": msg.content})
        elif isinstance(msg, HumanMessage):
            chat_data.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            chat_data.append({"role": "assistant", "content": msg.content})
            
    file_path = os.path.join(CHAT_DIR, st.session_state.current_chat_id)
    with open(file_path, "w") as f:
        json.dump(chat_data, f, indent=4)

# --- Sidebar UI ---
with st.sidebar:
    st.subheader("🤖 Smart AI Assistant")
    
    if st.button("➕ New chat", use_container_width=True):
        save_current_chat()
        st.session_state.current_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    system_message = st.text_input(label='System role', value=" ")

    st.divider()
    st.markdown("### Chat History")
    
    saved_chats = get_saved_chats()
    for chat_file in saved_chats:
        file_path = os.path.join(CHAT_DIR, chat_file)
        display_name = get_chat_title(file_path)
            
        is_selected = (chat_file == st.session_state.current_chat_id)
        button_type = "primary" if is_selected else "secondary"
        
        if st.button(display_name, key=chat_file, type=button_type, use_container_width=True):
            save_current_chat()
            st.session_state.current_chat_id = chat_file
            st.session_state.messages = []
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    chat_data = json.load(f)
                    for item in chat_data:
                        if item["role"] == "system":
                            st.session_state.messages.append(SystemMessage(content=item["content"]))
                        elif item["role"] == "user":
                            st.session_state.messages.append(HumanMessage(content=item["content"]))
                        elif item["role"] == "assistant":
                            st.session_state.messages.append(AIMessage(content=item["content"]))
            st.rerun()

# --- Main Page Chat Interface ---
st.subheader("Smart AI Assistant")

if system_message:
    if not any(isinstance(x, SystemMessage) for x in st.session_state.messages):
        st.session_state.messages.insert(0, SystemMessage(content=system_message))
    else:
        for x in st.session_state.messages:
            if isinstance(x, SystemMessage):
                x.content = system_message

chat = ChatOpenAI(model_name='gpt-4o', temperature=0.5)

for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("human"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("ai"):
            st.write(msg.content)

if user_prompt := st.chat_input("Send a message..."):
    st.session_state.messages.append(HumanMessage(content=user_prompt))
    with st.chat_message("human"):
        st.write(user_prompt)

    with st.chat_message("ai"):
        with st.spinner('Working on your request ...'):
            response = chat.invoke(st.session_state.messages)
            st.write(response.content)

    st.session_state.messages.append(AIMessage(content=response.content))
    save_current_chat()
    st.rerun() # Rerun immediately so the sidebar chat title updates automatically from the first prompt