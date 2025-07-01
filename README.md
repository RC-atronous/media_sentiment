Media Sentiment Analyzer is a FastAPI-based application that processes YouTube videos to extract and analyze their transcripts, identify important fragments, and highlight key sentiment-related keywords.

1. Clone the Repository

git clone https://github.com/your-username/media-sentiment-analyzer.git
cd media-sentiment-analyzer

2. Install Dependencies
Make sure you have Python 3.8+ installed. Then, install the required packages:
pip install -r requirements.txt

4. Run the Application
Use FastAPI's development server to start the backend:
fastapi dev main.py

The server will start locally at:
http://127.0.0.1:8000

📬 API Usage
Endpoint
POST /transcription_analyzer
Request Body
Send a raw JSON object containing the YouTube video link:
{
  "link": "https://www.youtube.com/watch?v=yibRuTl5AAg"
}

json
Copy
Edit
{
  "success": true,
  "details": {
    "hyperlink": "https://www.youtube.com/watch?v=yibRuTl5AAg",
    "transcript": "...", 
    "important frags": {
      "fragments": [
        "Cakes is one of the least expensive options",
        "Cakes has over 1,200 reviews with a 4.6 out of five star rating",
        "Flexispot has done it again being the least expensive option for an entry level four leg standing desk",
        ...
      ]
    },
    "keywords": {
      "keywords": [
        "motor system",
        "max weight capacity",
        "collision avoidance",
        "entry level",
        "L-shaped",
        "surface power",
        ...
      ]
    }
  }
}

What It Does
Transcription: Extracts the full transcript from a YouTube video.

Fragment Extraction: Highlights key takeaways and product comparisons.

Keyword Extraction: Identifies relevant terms related to sentiment, product specs, and user experience.

Tech Stack
FastAPI – Web framework for building the API

YouTube Transcript API – For extracting video transcriptions

SpaCy / NLP Pipelines – For analyzing and extracting meaningful fragments and keywords

