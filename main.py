import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Page Configuration
st.set_page_config(page_title="AI Video Insights & Discussion Bot", page_icon="🤖", layout="wide")

st.title("🤖 Project Discussion & Video AI Bot")
st.caption("साइडबार में यूट्यूब वीडियो का लिंक पेस्ट करें और प्रोसेस करने के बाद उससे कोई भी सवाल सीधे यहाँ चैट में पूछें।")

# Sidebar Configuration
st.sidebar.header("⚙️ Configuration & Source")

# Retrieve API Key from Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.sidebar.warning("Please configure your Gemini API Key to proceed.")

st.sidebar.markdown("---")
st.sidebar.header("📹 Load YouTube Content")
video_url = st.sidebar.text_input("YouTube Video URL:")

def extract_video_id(url):
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)|views|watch)\?v=|youtu\.be/)([\w-]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi', 'en'])
        transcript = " ".join([item['text'] for item in transcript_list])
        return transcript
    except Exception as e:
        return None

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show current video context status
if video_url:
    video_id = extract_video_id(video_url)
    if video_id:
        st.sidebar.image(f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg")
        
        if st.sidebar.button("🔄 Process & Sync Video Context"):
            with st.spinner("वीडियो की स्क्रिप्ट निकाली जा रही है..."):
                transcript = get_youtube_transcript(video_id)
                if transcript:
                    st.session_state.video_transcript = transcript
                    st.sidebar.success("स्क्रिप्ट सफलतापूर्वक सिंक हो गई!")
                else:
                    st.sidebar.error("इस वीडियो की स्क्रिप्ट नहीं मिल सकी। कृपया चेक करें कि वीडियो में कैप्शंस (Subtitles) ऑन हैं या नहीं।")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask anything about the video or general topics..."):
    if not api_key:
        st.error("कृपया पहले अपनी Gemini API Key सेट करें।")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Context Preparation
            context = ""
            if "video_transcript" in st.session_state:
                context = f"Here is the transcript of the video you are discussing: {st.session_state.video_transcript}\n\n"
            
            try:
                # Using stable gemini-1.5-flash model
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"{context}User Question: {prompt}")
                full_response = response.text
                message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"Error during generation: {str(e)}"
                message_placeholder.error(full_response)
                
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.sidebar.button("🧹 Clear Chat History"):
    st.session_state.messages = []
    if "video_transcript" in st.session_state:
        del st.session_state["video_transcript"]
    st.rerun()
