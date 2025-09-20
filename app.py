import streamlit as st
import wikipediaapi
import requests
import json
import re
import time
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# -----------------------------
# Streamlit page configuration
st.set_page_config(
    page_title="தமிழ் தகவல் உதவியாளர்", 
    page_icon="🪷", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Custom CSS for better UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 1rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
    }
    
    /* Sidebar styling */
    .sidebar-info {
        background-color: rgba(102, 126, 234, 0.1);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-active {
        background-color: #4ade80;
        animation: pulse 2s infinite;
    }
    
    .status-inactive {
        background-color: #f87171;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(74, 222, 128, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
        }
    }
    
    /* Source badge styling */
    .source-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin-top: 10px;
    }
    
    /* Quick action buttons */
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        border: none;
        cursor: pointer;
        margin: 5px;
        transition: transform 0.3s;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-2px);
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-flex;
        align-items: center;
    }
    
    .loading-dots span {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #667eea;
        margin: 0 3px;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .loading-dots span:nth-child(1) {
        animation-delay: -0.32s;
    }
    
    .loading-dots span:nth-child(2) {
        animation-delay: -0.16s;
    }
    
    @keyframes bounce {
        0%, 80%, 100% {
            transform: scale(0);
        }
        40% {
            transform: scale(1);
        }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Load API keys from Streamlit secrets
@st.cache_data
def load_api_keys():
    """Load API keys from Streamlit secrets"""
    try:
        return {
            'gemini_api_key': st.secrets.get("GEMINI_API_KEY", ""),
            'google_api_key': st.secrets.get("GOOGLE_API_KEY", ""),
            'google_cx': st.secrets.get("GOOGLE_CX", "")
        }
    except Exception as e:
        st.error(f"API விசைகளை ஏற்றுவதில் பிழை: {str(e)}")
        return {
            'gemini_api_key': "",
            'google_api_key': "",
            'google_cx': ""
        }

# Load keys at startup
API_KEYS = load_api_keys()

# -----------------------------
# Initialize Wikipedia API for Tamil with a proper User-Agent
@st.cache_resource
def get_wiki_instances():
    """Initialize Wikipedia API instances"""
    wiki_ta = wikipediaapi.Wikipedia(
        language='ta',
        extract_format=wikipediaapi.ExtractFormat.WIKI,
        user_agent='TamilAIAssistant/2.0 (streamlit.app)'
    )
    
    wiki_en = wikipediaapi.Wikipedia(
        language='en',
        extract_format=wikipediaapi.ExtractFormat.WIKI,
        user_agent='TamilAIAssistant/2.0 (streamlit.app)'
    )
    
    return wiki_ta, wiki_en

wiki_ta, wiki_en = get_wiki_instances()

# -----------------------------
# System Instructions for Gemini AI (Enhanced)
SYSTEM_INSTRUCTIONS = """
நீங்கள் ஒரு மேம்பட்ட தமிழ் தகவல் மேலாண்மை உதவியாளர். உங்கள் பணி பயனருக்கு துல்லியமான, நம்பகமான மற்றும் விரிவான தகவல்களை வழங்குவதாகும்.

முக்கிய விதிமுறைகள்:

1. **மொழி**: எல்லா பதில்களையும் தூய தமிழில் மட்டுமே வழங்கவும். தேவைப்பட்டால் அடைப்புக்குறிக்குள் ஆங்கில சொற்களை குறிப்பிடலாம்.

2. **தேடல் வரிசை**:
   - முதலில் விக்கிப்பீடியா தேடல் செய்யவும்
   - தகவல் போதுமானதாக இல்லாவிட்டால் கூகுள் தேடல் செய்யவும்
   - இரண்டு ஆதாரங்களையும் ஒப்பிட்டு சிறந்த தகவலை தேர்வு செய்யவும்

3. **பதில் அமைப்பு**:
   - தெளிவான தலைப்பு
   - விரிவான விளக்கம்
   - முக்கிய அம்சங்கள் (bullet points)
   - தகவல் ஆதாரம்

4. **சிறப்பு கவனம்**:
   - தமிழ் இலக்கியம், வரலாறு, பண்பாடு தொடர்பான கேள்விகளுக்கு விரிவான விளக்கம்
   - சங்க இலக்கியம், பக்தி இலக்கியம், நவீன இலக்கியம் போன்றவற்றிற்கு காலக்கிரம விளக்கம்
   - தமிழ் மன்னர்கள், போர்கள், வரலாற்று நிகழ்வுகளுக்கு தேதி மற்றும் இடம் குறிப்பிடவும்

5. **வாழ்த்துகள் மற்றும் உரையாடல்**:
   - பயனர் வணக்கம் சொன்னால் அன்புடன் பதில் வணக்கம் சொல்லவும்
   - உரையாடலை இனிமையாகவும் மரியாதையுடனும் நடத்தவும்

6. **துல்லியம்**:
   - கிடைத்த தகவலை மட்டும் பயன்படுத்தவும்
   - கற்பனை தகவலை (hallucination) தவிர்க்கவும்
   - தெரியாத விஷயங்களுக்கு "துல்லியமான தகவல் கிடைக்கவில்லை" என குறிப்பிடவும்

7. **முக்கிய தலைப்புகள்**:
   - திருக்குறள் மற்றும் திருவள்ளுவர்
   - சங்க இலக்கியம் (எட்டுத்தொகை, பத்துப்பாட்டு)
   - சிலப்பதிகாரம், மணிமேகலை போன்ற காப்பியங்கள்
   - பக்தி இலக்கிய ஆழ்வார்கள், நாயன்மார்கள்
   - தமிழ் மன்னர்கள் (சோழர், பாண்டியர், பல்லவர், சேரர்)
   - தமிழ் பண்பாடு மற்றும் பாரம்பரியம்
"""

# -----------------------------
# Enhanced Wikipedia search with better error handling
def get_wikipedia_content(query):
    """Fetch Wikipedia content with enhanced search strategies"""
    try:
        # Strategy 1: Direct search in Tamil
        page = wiki_ta.page(query)
        if page.exists():
            summary = page.summary.strip()
            if len(summary) > 100:
                return {
                    'content': summary[:2000],
                    'title': page.title,
                    'url': page.fullurl,
                    'language': 'தமிழ்'
                }
        
        # Strategy 2: Search with Tamil keywords
        tamil_keywords = ['தமிழ்', 'இலக்கியம்', 'வரலாறு', 'பண்பாடு', 'கவிதை', 'சங்க இலக்கியம்']
        for keyword in tamil_keywords:
            combined_query = f"{query} {keyword}"
            page = wiki_ta.page(combined_query)
            if page.exists():
                summary = page.summary.strip()
                if len(summary) > 100:
                    return {
                        'content': summary[:2000],
                        'title': page.title,
                        'url': page.fullurl,
                        'language': 'தமிழ்'
                    }
        
        # Strategy 3: English Wikipedia as fallback
        eng_page = wiki_en.page(query)
        if eng_page.exists():
            summary = eng_page.summary.strip()
            if len(summary) > 100:
                return {
                    'content': f"[தமிழ் விக்கிப்பீடியாவில் இல்லை. ஆங்கில விக்கிப்பீடியா:]\n{summary[:1500]}",
                    'title': eng_page.title,
                    'url': eng_page.fullurl,
                    'language': 'ஆங்கிலம்'
                }
        
        return None
        
    except Exception as e:
        st.error(f"விக்கிப்பீடியா பிழை: {str(e)}")
        return None

# -----------------------------
# Enhanced Google Search with rate limiting
def get_google_content(query):
    """Fetch Google Search content with enhanced error handling"""
    try:
        if not API_KEYS['google_api_key'] or not API_KEYS['google_cx']:
            return None
            
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query + " தமிழ்",  # Add Tamil to prioritize Tamil results
            "key": API_KEYS['google_api_key'],
            "cx": API_KEYS['google_cx'],
            "lr": "lang_ta",  # Tamil language preference
            "num": 5  # Get top 5 results
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "items" in data:
            results = []
            for item in data["items"][:3]:  # Use top 3 results
                result = {
                    'title': item.get("title", ""),
                    'snippet': item.get("snippet", ""),
                    'link': item.get("link", "")
                }
                results.append(result)
            
            combined = "\n\n".join([f"**{r['title']}**\n{r['snippet']}" for r in results])
            return combined[:2000] if combined else None
        
        return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"கூகுள் தேடல் பிழை: {str(e)}")
        return None
    except Exception as e:
        st.error(f"எதிர்பாராத பிழை: {str(e)}")
        return None

# -----------------------------
# Setup Gemini API with caching
@st.cache_resource
def setup_genai():
    """Initialize Gemini AI configuration"""
    try:
        if not API_KEYS['gemini_api_key']:
            return False
        genai.configure(api_key=API_KEYS['gemini_api_key'])
        return True
    except Exception as e:
        st.error(f"Gemini API துவக்க பிழை: {str(e)}")
        return False

# -----------------------------
# Enhanced response generation with better context
def generate_response(query):
    """Generate response using Gemini AI with enhanced context and error handling"""
    try:
        # Fetch content from both sources
        wiki_data = get_wikipedia_content(query)
        google_content = get_google_content(query) if not wiki_data or len(wiki_data.get('content', '')) < 300 else None
        
        # Build enhanced prompt
        full_prompt = SYSTEM_INSTRUCTIONS + "\n\n"
        full_prompt += f"பயனர் கேள்வி: {query}\n\n"
        
        if wiki_data:
            full_prompt += f"விக்கிப்பீடியா தகவல் ({wiki_data['language']}):\n"
            full_prompt += f"தலைப்பு: {wiki_data['title']}\n"
            full_prompt += f"{wiki_data['content']}\n\n"
        
        if google_content:
            full_prompt += f"கூகுள் தேடல் தகவல்:\n{google_content}\n\n"
        
        full_prompt += """
        மேற்கண்ட தகவல்களை பயன்படுத்தி:
        1. தெளிவான மற்றும் விரிவான பதிலை தமிழில் வழங்கவும்
        2. முக்கிய அம்சங்களை புள்ளிகளாக (bullet points) குறிப்பிடவும்
        3. தகவல் ஆதாரத்தை குறிப்பிடவும்
        4. பயனருக்கு பயனுள்ள கூடுதல் தகவல்களையும் சேர்க்கவும்
        """
        
        # Safety settings
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 3000,
            },
            safety_settings=safety_settings
        )
        
        # Generate response
        response = model.generate_content(full_prompt)
        response_text = response.text
        
        # Determine sources used
        sources = []
        if wiki_data:
            sources.append(f"விக்கிப்பீடியா ({wiki_data['language']})")
        if google_content:
            sources.append("கூகுள் தேடல்")
        
        source_used = " மற்றும் ".join(sources) if sources else "தகவல் ஆதாரம் இல்லை"
        
        # Add wiki URL if available
        wiki_url = wiki_data['url'] if wiki_data else None
        
        return response_text, source_used, wiki_url
        
    except Exception as e:
        error_msg = f"பதில் உருவாக்குவதில் பிழை: {str(e)}"
        st.error(error_msg)
        return "மன்னிக்கவும், பதில் உருவாக்குவதில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.", None, None

# -----------------------------
# Quick action examples
def get_quick_actions():
    """Return quick action examples"""
    return [
        "திருக்குறள் பற்றி",
        "சங்க இலக்கியம்",
        "சோழர் வரலாறு",
        "தமிழ் எழுத்துகள்",
        "சிலப்பதிகாரம்",
        "பல்லவர் கட்டிடக்கலை"
    ]

# -----------------------------
# Main UI
# Custom header
st.markdown("""
<div class="header-container">
    <div class="header-title">🪷 தமிழ் தகவல் உதவியாளர்</div>
    <div class="header-subtitle">தமிழ் வரலாறு, இலக்கியம், பண்பாடு பற்றிய துல்லியமான தகவல்கள்</div>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📊 பயன்பாட்டு நிலை")
    
    # Check API status
    api_status = all([API_KEYS['gemini_api_key'], API_KEYS['google_api_key'], API_KEYS['google_cx']])
    
    if api_status:
        st.markdown("""
        <div style="display: flex; align-items: center;">
            <span class="status-indicator status-active"></span>
            <span style="color: #4ade80;">அனைத்து சேவைகளும் செயலில் உள்ளன</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; align-items: center;">
            <span class="status-indicator status-inactive"></span>
            <span style="color: #f87171;">API விசைகள் கிடைக்கவில்லை</span>
        </div>
        """, unsafe_allow_html=True)
        
        missing_keys = []
        if not API_KEYS['gemini_api_key']:
            missing_keys.append("Gemini API")
        if not API_KEYS['google_api_key']:
            missing_keys.append("Google Search API")
        if not API_KEYS['google_cx']:
            missing_keys.append("Google CX")
        
        if missing_keys:
            st.error(f"இல்லாத விசைகள்: {', '.join(missing_keys)}")
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📈 புள்ளிவிவரங்கள்")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("மொத்த கேள்விகள்", len(st.session_state.get('messages', [])) // 2)
    with col2:
        st.metric("அமர்வு நேரம்", f"{int((time.time() - st.session_state.get('start_time', time.time())) / 60)} நிமிடங்கள்")
    
    st.markdown("---")
    
    # About section
    with st.expander("ℹ️ பயன்பாட்டு தகவல்"):
        st.markdown("""
        ### முக்கிய அம்சங்கள்:
        - 🔍 விக்கிப்பீடியா தேடல் (தமிழ் & ஆங்கிலம்)
        - 🌐 கூகுள் தேடல் ஒருங்கிணைப்பு
        - 🤖 Gemini AI பயன்பாடு
        - 💬 இயற்கையான உரையாடல்
        - 📚 விரிவான தமிழ் இலக்கிய தகவல்
        
        ### சிறப்பு தலைப்புகள்:
        - சங்க இலக்கியம்
        - திருக்குறள்
        - தமிழ் வரலாறு
        - கோயில் கட்டிடக்கலை
        - பண்பாட்டு மரபுகள்
        """)
    
    # Clear chat button
    if st.button("🔄 புதிய உரையாடல் தொடங்கு", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.start_time = time.time()

if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()

# Quick actions (only show if no messages)
if len(st.session_state.messages) == 0:
    st.markdown("### 🚀 விரைவு தொடக்கம்")
    st.markdown("கீழ்க்கண்ட பொத்தான்களை அழுத்தி உடனடியாக தகவல் பெறுங்கள்:")
    
    cols = st.columns(3)
    for i, action in enumerate(get_quick_actions()):
        with cols[i % 3]:
            if st.button(action, key=f"quick_{i}", use_container_width=True):
                st.session_state.quick_query = action

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
        st.markdown(message["content"])
        if "source_type" in message and message["source_type"]:
            st.markdown(f'<span class="source-badge">📚 {message["source_type"]}</span>', unsafe_allow_html=True)
        if "wiki_url" in message and message.get("wiki_url"):
            st.markdown(f"[🔗 விக்கிப்பீடியா பக்கம்]({message['wiki_url']})")

# Handle quick query
if 'quick_query' in st.session_state:
    query = st.session_state.quick_query
    del st.session_state.quick_query
    st.session_state.messages.append({"role": "user", "content": query})
    st.rerun()

# User input
if query := st.chat_input("உங்கள் கேள்வியை தமிழில் கேளுங்கள்... (எ.கா: திருக்குறள் பற்றி சொல்லுங்கள்)"):
    if not API_KEYS['gemini_api_key']:
        st.error("⚠️ Gemini API key கிடைக்கவில்லை. Streamlit secrets-ல் சரிபார்க்கவும்.")
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(query)
        
        # Generate and display assistant response
        with st.chat_message("assistant", avatar="🤖"):
            # Show custom loading animation
            loading_placeholder = st.empty()
            loading_placeholder.markdown("""
            <div class="loading-dots">
                பதில் தயாராகிறது
                <span></span>
                <span></span>
                <span></span>
            </div>
            """, unsafe_allow_html=True)
            
            # Setup Gemini and generate response
            if setup_genai():
                response, source_used, wiki_url = generate_response(query)
                
                # Clear loading animation
                loading_placeholder.empty()
                
                # Display response
                st.markdown(response)
                
                if source_used:
                    st.markdown(f'<span class="source-badge">📚 {source_used}</span>', unsafe_allow_html=True)
                
                if wiki_url:
                    st.markdown(f"[🔗 விக்கிப்பீடியா பக்கம்]({wiki_url})")
                
                # Save to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "source_type": source_used,
                    "wiki_url": wiki_url
                })
            else:
                loading_placeholder.empty()
                st.error("API அமைப்பில் பிழை. மீண்டும் முயற்சிக்கவும்.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    🪷 தமிழ் மொழி மற்றும் பண்பாட்டை காக்க உருவாக்கப்பட்டது | 
    Powered by Gemini AI & Wikipedia
</div>
""", unsafe_allow_html=True)
