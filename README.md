# Tamil-AI - தமிழ் தகவல் உதவியாளர்

A Streamlit application that uses Wikipedia and Google Search to provide accurate and reliable information in Tamil language, powered by Gemini AI.

Try it out: [Tamil AI](https://tamil-ai.streamlit.app/)

## Overview

தமிழ் தகவல் உதவியாளர் (Tamil Information Assistant) is designed to provide comprehensive and accurate information about Tamil literature, history, culture, and more in the Tamil language. It leverages multiple sources to ensure reliable information:

1. **Tamil Wikipedia**: Primary source for information
2. **English Wikipedia**: Fallback when Tamil sources are insufficient
3. **Google Search**: Additional source when Wikipedia doesn't have adequate information

The application uses Gemini AI to process the retrieved information and generate coherent, contextually relevant responses in Tamil.

## Features

- **Bilingual Information Retrieval**: Primarily searches Tamil resources; falls back to English when necessary
- **Multi-source Integration**: Combines information from Wikipedia and Google Search
- **Pure Tamil Responses**: All responses are provided solely in Tamil
- **Category-enhanced Search**: Uses Tamil categories to improve search results
- **Visual Chat Interface**: Clean, user-friendly Streamlit chat interface
- **Source Attribution**: Clearly indicates which sources were used for each response

## Requirements

- Python 3.7+
- Streamlit
- wikipediaapi
- google-generativeai
- requests

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Tamil-AI.git
cd Tamil-AI

# Install required packages
pip install -r requirements.txt
```

## API Keys Required

To use this application, you'll need to provide three API keys in the web interface:

1. **Gemini API Key**: For accessing Google's Gemini AI models
   - Get it from: [Google AI Studio](https://makersuite.google.com/)

2. **Google API Key**: For accessing Google's Custom Search JSON API
   - Get it from: [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the "Custom Search API" service

3. **Google CX (Custom Search Engine ID)**: To specify your custom search engine
   - Create at: [Programmable Search Engine](https://programmablesearchengine.google.com/)
   - Configure it to search the entire web, with preference for Tamil content

## Usage

1. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser to the provided URL (typically http://localhost:8501)

3. Enter your API keys in the sidebar

4. Start asking questions in Tamil!

## Example Queries

- திருக்குறள் பற்றிய தகவல் (Information about Thirukkural)
- சங்க இலக்கிய காலம் (Sangam literature period)
- தமிழ் மன்னர்கள் வரலாறு (History of Tamil kings)
- பல்லவர் காலத்து கட்டிடக்கலை (Pallava period architecture)

## How It Works

1. The application receives a query in Tamil
2. It searches Tamil Wikipedia for relevant information
3. If information is insufficient or unavailable, it falls back to English Wikipedia
4. If Wikipedia sources are inadequate, it performs a Google Search
5. All gathered information is sent to Gemini AI with specific instructions
6. Gemini AI processes the information and generates a comprehensive response in Tamil
7. The response is displayed to the user along with source attribution

## Acknowledgements

- Wikipedia API for providing access to Wikipedia content
- Google for the Gemini AI and Custom Search API
- Streamlit for the web application framework
