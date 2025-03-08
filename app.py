import streamlit as st
import wikipediaapi
import requests
import json
import re
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# -----------------------------
# Streamlit page configuration
st.set_page_config(page_title="தமிழ் தகவல் உதவியாளர்", page_icon="📚", layout="wide")

# -----------------------------
# Initialize Wikipedia API for Tamil with a proper User-Agent
wiki_ta = wikipediaapi.Wikipedia(
    language='ta',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent='TamilAIAssistant/1.0 (contact@tamilai.com)'
)

# Also initialize English Wikipedia (for fallback translation)
wiki_en = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent='TamilAIAssistant/1.0 (contact@tamilai.com)'
)

# -----------------------------
# System Instructions for Gemini AI (தமிழில்)
SYSTEM_INSTRUCTIONS = """
நீங்கள் ஒரு தமிழ் தகவல் மேலாண்மை உதவியாளர். உங்கள் பணி பயனருக்கு துல்லியமான, நம்பகமான மற்றும் சீரான தகவல்களை வழங்குவதாகும்.

முக்கிய விதிமுறைகள்:
if the user give greetings, then you should give greetings
if the user ask for information, then you should give information

1. எல்லா பதில்களையும் தமிழில் மட்டுமே வழங்கவும்.
2. முதலில் விக்கிப்பீடியா தேடல் செய்யவும். 
3. விக்கிப்பீடியாவில் தேவையான தகவல் கிடைக்காவிட்டால் அல்லது தகவல் குறைவாக இருந்தால், கூகுள் தேடலைக் கொண்டு தேவையான முழுமையான தகவலை பெறவும்.
4. தேடல்களில் கிடைத்த தகவலை மட்டும் பயன்படுத்தி, தவறான அல்லது கற்பனையான (hallucinated) தகவலை வழங்க வேண்டாம்.
5. தமிழ் இலக்கியம், வரலாறு, பண்பாடு, சங்க இலக்கியம் மற்றும் பழந்தமிழ் இலக்கியம் தொடர்பான கேள்விகளுக்கு விரிவான விளக்கம் வழங்கவும்.
6. பதிலை உருவாக்கும் போது, முதலில் கிடைத்த தகவலை (விக்கிப்பீடியா/கூகுள்) நன்கு சிந்தித்து, அவற்றை அடிப்படையாகக் கொண்டு, தெளிவான தலைப்பு, விளக்கம் மற்றும் தகவல் ஆதாரத்தை (உதாரணமாக: "விக்கிப்பீடியா" அல்லது "கூகுள் தேடல்") குறிப்பிடவும்.
7. "தெரியவில்லை" என்ற நிலை ஏற்பட்டால், "இந்தக் கேள்விக்கு எனக்கு துல்லியமான பதில் தெரியவில்லை" என பதில் தரவும்.
"""

# -----------------------------
# Function to fetch Wikipedia content (Tamil preferred)
def get_wikipedia_content(query):
    try:
        # முதலில் நேரடி (exact match) தேடல்
        page = wiki_ta.page(query)
        if page.exists():
            summary = page.summary.strip()
            if len(summary) > 100:
                return summary[0:1500]  # சுருக்கம், character limit
        # கண்டறிய தவறினால், சில தமிழ்த்தொகுப்பு (categories) சேர்த்து முயற்சி செய்க
        tamil_categories = ['தமிழ்', 'இலக்கியம்', 'வரலாறு', 'பண்பாடு', 'கவிதை', 'சங்க இலக்கியம்']
        for category in tamil_categories:
            combined_query = f"{query} {category}"
            page = wiki_ta.page(combined_query)
            if page.exists():
                summary = page.summary.strip()
                if len(summary) > 100:
                    return summary[0:1500]
        # fallback: ஆங்கில விக்கிப்பீடியா மூலம்
        eng_page = wiki_en.page(query)
        if eng_page.exists():
            summary = eng_page.summary.strip()
            if len(summary) > 100:
                return f"[தமிழ் விக்கிப்பீடியாவில் தகவல் கிடைக்கவில்லை. ஆங்கில விக்கிப்பீடியா தகவல்:]\n{summary[0:1000]}"
        return None
    except Exception as e:
        st.error(f"Wikipedia error: {str(e)}")
        return None

# -----------------------------
# Function to fetch Google Search content using Google Custom Search API
def get_google_content(query):
    try:
        if not st.session_state.google_api_key or not st.session_state.google_cx:
            st.warning("கூகுள் தேடல் API விசைகள் அமைக்கப்படவில்லை.")
            return None
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": st.session_state.google_api_key,
            "cx": st.session_state.google_cx,
            "lr": "lang_ta"  # தமிழ் மொழி முதல்
        }
        response = requests.get(url, params=params)
        data = response.json()
        if "items" in data:
            snippets = [item.get("snippet", "") for item in data["items"]]
            combined = "\n".join(snippets).strip()
            if combined:
                return combined[0:1500]
        return None
    except Exception as e:
        st.error(f"Google Search error: {str(e)}")
        return None

# -----------------------------
# Setup Gemini API (using st.cache_resource to reuse the configuration)
@st.cache_resource
def setup_genai():
    try:
        genai.configure(api_key=st.session_state.api_key)
        return True
    except Exception as e:
        st.error(f"API initialization error: {str(e)}")
        return False

# -----------------------------
# Generate response using Gemini AI with robust decision making
def generate_response(query):
    try:
        # முதலில் விக்கிப்பீடியா தேடல்
        wiki_content = get_wikipedia_content(query)
        google_content = None
        
        # விக்கிப்பீடியா தகவல் இல்லாவிட்டால் அல்லது தகவல் குறைவாக இருந்தால், கூகுள் தேடலையும் செய்யவும்.
        if not wiki_content or (wiki_content and len(wiki_content) < 300):
            google_content = get_google_content(query)
        
        # Build the full prompt for Gemini API
        full_prompt = SYSTEM_INSTRUCTIONS + "\n\n"
        full_prompt += f"கேள்வி: {query}\n\n"
        if wiki_content:
            full_prompt += f"விக்கிப்பீடியா தகவல்:\n{wiki_content}\n\n"
        if google_content:
            full_prompt += f"கூகுள் தேடல் தகவல்:\n{google_content}\n\n"
        full_prompt += "மேற்கண்ட தகவல்களை (இருப்பின்) பயன்படுத்தி, துல்லியமான, நம்பகமான மற்றும் தெளிவான தமிழ் பதிலை உருவாக்கவும்."
        
        # Safety settings for Gemini API
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Get Gemini model instance (adjust model_name and generation_config as needed)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 5600,
            },
            safety_settings=safety_settings
        )
        
        # Generate the content
        response = model.generate_content(full_prompt)
        response_text = response.text
        
        # தீர்மானம்: எந்த தேடல் ஆதாரம் பயன்படுத்தப்பட்டது என்பதை குறிப்பு
        if wiki_content and not google_content:
            source_used = "விக்கிப்பீடியா"
        elif google_content and not wiki_content:
            source_used = "கூகுள் தேடல்"
        elif wiki_content and google_content:
            source_used = "விக்கிப்பீடியா மற்றும் கூகுள் தேடல்"
        else:
            source_used = "தகவல் ஆதாரம் கிடைக்கவில்லை"
            
        return response_text, source_used, full_prompt
        
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return "பதில் உருவாக்குவதில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.", None, None

# -----------------------------
# Streamlit UI (Chat Interface)
st.title("📚 தமிழ் தகவல் உதவியாளர்")
st.markdown("தமிழ் வரலாறு, இலக்கியம், பண்பாடு பற்றிய உங்கள் கேள்விகளுக்கு துல்லியமான பதில்களைப் பெறுங்கள்")

# Sidebar for API keys and application info
with st.sidebar:
    st.header("⚙️ அமைப்புகள்")
    
    # Initialize session state variables if they don't exist
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'google_api_key' not in st.session_state:
        st.session_state.google_api_key = ""
    if 'google_cx' not in st.session_state:
        st.session_state.google_cx = ""
    
    # Gemini API key input
    api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    if api_key:
        st.session_state.api_key = api_key
        
    # Google API key input
    google_api_key = st.text_input("Google API Key", value=st.session_state.google_api_key, type="password")
    if google_api_key:
        st.session_state.google_api_key = google_api_key
        
    # Google CX input
    google_cx = st.text_input("Google CX (Custom Search Engine ID)", value=st.session_state.google_cx, type="password")
    if google_cx:
        st.session_state.google_cx = google_cx
    
    # Check if all required keys are provided
    if api_key and google_api_key and google_cx:
        st.success("அனைத்து API விசைகளும் சேமிக்கப்பட்டன!")
    else:
        required_keys = []
        if not api_key:
            required_keys.append("Gemini API Key")
        if not google_api_key:
            required_keys.append("Google API Key")
        if not google_cx:
            required_keys.append("Google CX")
        
        if required_keys:
            st.warning(f"இந்த செயலியை முழுமையாக பயன்படுத்த பின்வரும் விசைகள் தேவை: {', '.join(required_keys)}")
    
    st.markdown("---")
    st.markdown("""
    ### பயன்பாடு பற்றி
    இந்த செயலி, விக்கிப்பீடியா மற்றும் (தேவைப்பட்டால்) கூகுள் தேடலைப் பயன்படுத்தி, 
    தமிழ் இலக்கியம், வரலாறு, பண்பாடு மற்றும் சங்க இலக்கியம் தொடர்பான துல்லியமான தகவல்களை வழங்குகிறது.
    
    உதாரண கேள்விகள்:
    - திருக்குறள் பற்றிய தகவல்
    - சங்க இலக்கிய காலம்
    - தமிழ் மன்னர்கள் வரலாறு
    - பல்லவர் காலத்து கட்டிடக்கலை
    """)

# Initialize chat session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "source_type" in message and message["source_type"]:
            st.caption(f"தகவல் ஆதாரம்: {message['source_type']}")

# User input
if query := st.chat_input("உங்கள் கேள்வியை தமிழில் கேளுங்கள்..."):
    if 'api_key' not in st.session_state or not st.session_state.api_key:
        st.error("Gemini API key தேவை. தயவுசெய்து sidebar-இல் சேர்க்கவும்.")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
            
        # Show a spinner while processing
        with st.chat_message("assistant"):
            with st.spinner("பதில் தயாராகிறது..."):
                if setup_genai():
                    response, source_used, full_prompt = generate_response(query)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "source_type": source_used,
                        "sources": f"**Prompt used:**\n```\n{full_prompt}\n```" if full_prompt else ""
                    })
                    st.markdown(response)
