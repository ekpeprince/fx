import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter

def fetch_transcript(video_id):
    """
    Fetches the transcript for a given YouTube video ID.
    Returns the transcript as structured JSON.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        
        # Clean and structure the raw transcript
        structured_data = []
        for item in transcript:
            text = item.text.lower()
            # Simple keyword extraction for ICT terms
            has_fvg = "fair value gap" in text or "fvg" in text
            has_ob = "order block" in text or "ob" in text
            has_liq = "liquidity" in text
            has_kz = "killzone" in text or "kill zone" in text
            
            structured_data.append({
                "start": item.start,
                "duration": item.duration,
                "text": item.text,
                "ict_keywords": {
                    "fvg": has_fvg,
                    "order_block": has_ob,
                    "liquidity": has_liq,
                    "killzone": has_kz
                }
            })
            
        return json.dumps(structured_data, indent=2)
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

if __name__ == "__main__":
    # Test with a dummy video ID or a known ICT video ID
    # Example video ID (replace with actual test ID)
    test_video_id = "jNQXAC9IVRw" # Real dummy video ID
    result = fetch_transcript(test_video_id)
    if result:
        print("Transcript fetched and structured successfully.")
        # print(result[:500]) # Print first 500 characters of JSON
