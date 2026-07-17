import streamlit as st
from google import genai
from youtube_transcript_api import YouTubeTranscriptApi
import os
import re

# 1. पेज की एडवांस सेटिंग्स
st.set_page_config(
    page_title="AI Video Insights & Discussion Bot",
    page_icon="🤖",
    layout="wide"
)

# 2. यूट्यूब वीडियो से ID अलग करने का हेल्पर फंक्शन
def extract_video_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 3. यूट्यूब API से स्क्रिप्ट (Transcript) फ़ेच करने का फंक्शन
def get_youtube_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.fetch_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript_list])
        return full_text
    except Exception as e:
        return None

# 4. साइडबार लेआउट (Configuration & Video Loader)
with st.sidebar:
    st.markdown("### ⚙️ Configuration & Source")
    
    # API Key इनपुट (अगर क्लाउड पर हो तो Secrets से उठाएगा, नहीं तो यहाँ डाल सकते हैं)
    api_key_env = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input("Enter Gemini API Key:", value=api_key_env, type="password", 
                            help="Leave blank if configured in environment/secrets.")
    
    st.markdown("---")
    st.markdown("### 📹 Load YouTube Content")
    yt_url = st.text_input("YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
    
    video_id = None
    if yt_url:
        video_id = extract_video_id(yt_url)
        if video_id:
            st.video(f"https://www.youtube.com/watch?v={video_id}")
            if st.button("📥 Process & Sync Video Context", use_container_width=True):
                with st.spinner("Fetching transcript and setting up context..."):
                    transcript = get_youtube_transcript(video_id)
                    if transcript:
                        st.session_state['transcript_context'] = transcript
                        st.success("वीडियो का पूरा डेटा सफ़लतापूर्वक लोड हो गया है!")
                    else:
                        st.error("इस वीडियो की स्क्रिप्ट नहीं मिल सकी। कृपया चेक करें कि वीडियो में कैप्शन्स (Subtitles) ऑन हैं या नहीं।")
        else:
            st.error("यूट्यूब लिंक का फॉर्मेट सही नहीं है।")

    st.markdown("---")
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state['messages'] = []
        st.rerun()

# 5. मुख्य स्क्रीन का हेडर और इंटरफेस
st.markdown("## 🤖 Project Discussion & Video AI Bot")
st.write("साइडबार में यूट्यूब वीडियो का लिंक पेस्ट करें और प्रोसेस करने के बाद उससे कोई भी सवाल सीधे यहाँ चैट में पूछें।")

# Gemini Client इनिशियलाइज करना
final_api_key = api_key if api_key else api_key_env
client = None
if final_api_key:
    try:
        client = genai.Client(api_key=final_api_key)
    except Exception as e:
        st.error(f"Gemini Client सेटअप फेल हुआ: {e}")
else:
    st.info("💡 चैट शुरू करने के लिए कृपया साइडबार में अपनी Gemini API Key डालें।")

# चैट और कॉन्टेक्स्ट की मेमोरी (Session States)
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'transcript_context' not in st.session_state:
    st.session_state['transcript_context'] = None

# पुरानी चैट हिस्ट्री स्क्रीन पर दिखाना
for message in st.session_state['messages']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# यूजर का नया इनपुट हैंडल करना
if prompt := st.chat_input("Ask anything about the video or general topics..."):
    if not client:
        st.warning("कृपया पहले अपनी Gemini API Key कॉन्फ़िगर करें।")
    else:
        # यूजर का मैसेज स्क्रीन पर डालना और सेव करना
        st.session_state['messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # RAG आर्किटेक्चर: अगर वीडियो का डेटा मौजूद है तो उसे प्रॉम्ट के साथ सिंक करना
        context_prompt = prompt
        if st.session_state['transcript_context']:
            context_prompt = f"Video Transcript Context:\n{st.session_state['transcript_context']}\n\nUser Question: {prompt}\n\nAnswer the user's question accurately based strictly on the provided video context text."

        # Gemini से रिस्पॉन्स जेनरेट करवाना
        with st.chat_message("assistant"):
            with st.spinner("Analyzing and thinking..."):
                try:
                    # सर की रिक्वायरमेंट के मुताबिक लेटेस्ट gemini-2.5-flash मॉडल
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=context_prompt,
                    )
                    ai_response = response.text
                    st.markdown(ai_response)
                    st.session_state['messages'].append({"role": "assistant", "content": ai_response})
                except Exception as e:
                    st.error(f"Error during generation: {e}")