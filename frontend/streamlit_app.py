import streamlit as st
import requests
from datetime import datetime
import json
import os

# Page configuration
st.set_page_config(
    page_title="Google Drive AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Get backend URL from environment variable or use default
# For Streamlit Cloud, this will come from secrets
BACKEND_URL = st.secrets.get("BACKEND_URL", "https://google-drive-ai-backend.onrender.com")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4285f4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        text-align: right;
    }
    .assistant-message {
        background-color: #f5f5f5;
        text-align: left;
    }
    .file-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #4285f4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def send_message(message: str):
    """Send message to backend API and get response"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"query": message, "user_id": "streamlit_user"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "response": f"Error: {response.status_code} - Please make sure the backend is running"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "response": "Cannot connect to backend. Please make sure the backend server is running."}
    except Exception as e:
        return {"success": False, "response": f"Error: {str(e)}"}

def clear_chat():
    """Clear chat history"""
    st.session_state.messages = []
    try:
        requests.post(f"{BACKEND_URL}/clear_memory", params={"user_id": "streamlit_user"})
    except:
        pass

# Header
st.markdown('<div class="main-header">🤖 Google Drive AI Assistant</div>', unsafe_allow_html=True)
st.markdown("*Search your Google Drive using natural language*")

# Sidebar
with st.sidebar:
    st.markdown("## 🔍 Search Examples")
    st.markdown("Try these natural language queries:")
    
    examples = [
        "Find my PDF files",
        "Show invoices from April",
        "Search presentation files",
        "Find recently modified documents",
        "Spreadsheets modified last week",
        "Images from last month",
        "Documents containing 'project proposal'"
    ]
    
    for example in examples:
        if st.button(example, key=example):
            with st.spinner("Searching..."):
                response = send_message(example)
                st.session_state.messages.append({
                    "role": "user",
                    "content": example,
                    "timestamp": datetime.now()
                })
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("response", "No response"),
                    "timestamp": datetime.now()
                })
                st.rerun()
    
    st.markdown("---")
    st.markdown("## 📊 Filters")
    
    # Quick filters
    file_type = st.selectbox(
        "File Type",
        ["All", "PDF", "Document", "Spreadsheet", "Presentation", "Image"]
    )
    
    date_range = st.selectbox(
        "Date Range",
        ["All time", "Today", "Last 7 days", "Last 30 days", "Last year"]
    )
    
    if st.button("Apply Filters"):
        query = f"Show {file_type.lower() if file_type != 'All' else ''} files "
        if date_range != "All time":
            query += f"from {date_range.lower()}"
        with st.spinner("Searching..."):
            response = send_message(query)
            st.session_state.messages.append({
                "role": "user",
                "content": query,
                "timestamp": datetime.now()
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.get("response", "No response"),
                "timestamp": datetime.now()
            })
            st.rerun()
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        clear_chat()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("This AI assistant can:")
    st.markdown("- Search by filename, type, and content")
    st.markdown("- Filter by date (created/modified)")
    st.markdown("- Understand conversational context")
    st.markdown("- Handle follow-up questions")
    
    # Show backend status
    st.markdown("---")
    st.markdown("### 🔌 Connection Status")
    try:
        health_check = requests.get(f"{BACKEND_URL}/", timeout=5)
        if health_check.status_code == 200:
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Error")
    except:
        st.error("❌ Backend Disconnected")

# Main chat area
chat_container = st.container()

with chat_container:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")
    
    # Chat input
    if prompt := st.chat_input("Ask me about your Google Drive files..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now()
        })
        
        # Get response
        with st.spinner("Searching your Google Drive..."):
            response = send_message(prompt)
        
        # Add assistant response
        st.session_state.messages.append({
            "role": "assistant",
            "content": response.get("response", "Sorry, I couldn't process that request."),
            "timestamp": datetime.now()
        })
        
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<center>Powered by FastAPI, LangChain, Google Drive API, and Gemini</center>",
    unsafe_allow_html=True
)
