import streamlit as st
from google import genai
from google.genai import types
import os

# Page Configuration
st.set_page_config(page_title="AI Video Insights & Discussion Bot", page_icon="🤖", layout="wide")

st.title("🤖 Project Discussion & Video AI Bot")
st.caption("यहाँ कोई भी सवाल सीधे चैट में पूछें।")

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration & Source")

# Retrieve API Key from Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask anything about general topics..."):
    if not api_key:
        st.error("कृपया पहले अपनी Gemini API Key सेट करें।")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            try:
                # नए SDK (google-genai) का सही तरीका
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model='gemini-2.5-flash-8b',
                    contents=prompt,
                )
                full_response = response.text
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Error during generation: {str(e)}"
                message_placeholder.error(full_response)
                
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.sidebar.button("🧹 Clear Chat History"):
    st.session_state.messages = []
    st.rerun()
