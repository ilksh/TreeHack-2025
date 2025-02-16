from youtube_transcript_api import YouTubeTranscriptApi
import requests
import datetime

API_KEY = "AIzaSyDfP9O8akh1SG9nbfdpfUTqNizFDtrPJvg"
SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
QUERY = "AAPL stock analysis OR Apple stock news #apple"

def search_for_videos():
    
    published_after = (datetime.datetime.utcnow() - datetime.timedelta(weeks=2)).isoformat("T") + "Z"

    params = {
        "part": "snippet",
        "q": QUERY,
        "type": "video",
        "order": "date",
        "publishedAfter": published_after,
        "maxResults": 10,
        "key": API_KEY
    }

    response = requests.get(SEARCH_URL, params=params)
    data = response.json()

    if "error" in data:
        print("Error:", data["error"]["message"])
    else:
        print("Recent videos about AAPL stock analysis:")
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"{title}\n{url}\n")

def collect_transcript():
    pass

if __name__ == "__main__":
    search_for_videos()