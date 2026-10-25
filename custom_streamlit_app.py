from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import streamlit as st
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="Smart AI Assistant",
    page_icon="✨",
    layout="wide"
)

# --- Custom Modern UI Styles ---
st.markdown("""
<style>
    /* Hide the top Streamlit header/toolbar */
    header {visibility: hidden !important;}
    .stAppHeader {display: none !important;}
    
    /* Global Styling */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Modern Card Layout for Login */
    .login-card {
        background: #161b22;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        border: 1px solid #30363d;
        max-width: 500px;
        margin: 80px auto;
        text-align: center;
    }

    /* Input Field Polish */
    .stTextInput input {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    
    /* Buttons */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* Chat Message Bubbles */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #30363d;
    }
    /* Fix Chat Input Container Background and Border */
    [data-testid="stChatInput"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
    }

    /* Fix the actual Text Area inside the Chat Input */
    [data-testid="stChatInput"] textarea {
        background-color: #161b22 !important;
        color: #ffffff !important;
    }

    /* Placeholder Text Color */
    [data-testid="stChatInput"] textarea::placeholder {
        color: #8b949e !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for API key
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("OPENAI_API_KEY", "")

# Gatekeeper: Attractive Login Card
if not st.session_state.api_key:
    st.markdown("""
        <div class="login-card">
            <h2 style="color: #58a6ff; margin-bottom: 10px;">✨ Smart AI Assistant</h2>
            <p style="color: #8b949e; font-size: 14px; margin-bottom: 25px;">
                Enter your OpenAI API key below to unlock your workspace.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Center input elements cleanly inside columns
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        api_input = st.text_input("OpenAI API Key", type="password", label_visibility="collapsed", placeholder="sk-...")
        if st.button("Access Assistant", use_container_width=True, type="primary"):
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
    if not os.path.exists(CHAT_DIR):
        return []
    files = [f for f in os.listdir(CHAT_DIR) if f.endswith(".json")]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(CHAT_DIR, x)), reverse=True)
    return files

def get_chat_title(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            for item in data:
                if item["role"] == "user":
                    text = item["content"]
                    return text[:28] + "..." if len(text) > 28 else text
    except:
        pass
    return "New Conversation"

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

# --- Modern Sidebar ---
with st.sidebar:
    st.markdown("### ✨ Smart AI")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        save_current_chat()
        st.session_state.current_chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        st.session_state.messages = []
        st.rerun()
        
    st.divider()
    system_message = st.text_input(label='System Role', value="You are a helpful assistant.")

    st.divider()
    st.markdown("💬 **Recent Chats**")
    
    saved_chats = get_saved_chats()
    for chat_file in saved_chats:
        file_path = os.path.join(CHAT_DIR, chat_file)
        display_name = get_chat_title(file_path)
            
        is_selected = (chat_file == st.session_state.current_chat_id)
        btn_type = "primary" if is_selected else "secondary"
        
        if st.button(display_name, key=chat_file, type=btn_type, use_container_width=True):
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

# --- Main Workspace Header ---
st.markdown("### 💬 Smart AI Assistant Workspace")
st.divider()

if system_message:
    if not any(isinstance(x, SystemMessage) for x in st.session_state.messages):
        st.session_state.messages.insert(0, SystemMessage(content=system_message))
    else:
        for x in st.session_state.messages:
            if isinstance(x, SystemMessage):
                x.content = system_message

chat = ChatOpenAI(model_name='gpt-4o', temperature=0.5)

# Render Chat History
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("human", avatar="👤"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("ai", avatar="✨"):
            st.write(msg.content)

# Bottom Floating Input Box
if user_prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append(HumanMessage(content=user_prompt))
    with st.chat_message("human", avatar="👤"):
        st.write(user_prompt)

    with st.chat_message("ai", avatar="✨"):
        with st.spinner('Thinking...'):
            response = chat.invoke(st.session_state.messages)
            st.write(response.content)

    st.session_state.messages.append(AIMessage(content=response.content))
    save_current_chat()
    st.rerun()
