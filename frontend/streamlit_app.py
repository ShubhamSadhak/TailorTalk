import streamlit as st
import requests
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Google Drive AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# API configuration
API_URL = "http://localhost:8000"

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
    .search-example {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .search-example:hover {
        background-color: #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "search_results" not in st.session_state:
    st.session_state.search_results = []

def send_message(message: str):
    """Send message to API and get response"""
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"query": message, "user_id": "streamlit_user"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "response": f"Error: {response.status_code}"}
    except Exception as e:
        return {"success": False, "response": f"Connection error: {str(e)}"}

def clear_chat():
    """Clear chat history"""
    st.session_state.messages = []
    st.session_state.search_results = []
    requests.post(f"{API_URL}/clear_memory", params={"user_id": "streamlit_user"})

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

# Display search statistics
if st.session_state.messages:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Conversations", len([m for m in st.session_state.messages if m["role"] == "user"]))
    
    with col2:
        st.metric("Last Search", st.session_state.messages[-1]["timestamp"].strftime("%H:%M:%S") if st.session_state.messages else "None")
    
    with col3:
        st.metric("Session Active", "✅ Yes")

# Footer
st.markdown("---")
st.markdown(
    "<center>Powered by FastAPI, LangChain, and Google Drive API</center>",
    unsafe_allow_html=True
)
