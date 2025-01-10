# # tools and agent
# import os 
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_openai import ChatOpenAI
# from pymongo import MongoClient
from config.setting import api_key, youtube_api_key, mongo_uri
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser


from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import urllib.parse

# # Initialize MongoDB Client
# client = MongoClient(mongo_uri)
# db = client['learning_app']
# lessons_collection = db['lessons']


def search_youtube(youtube_query: str) -> str:
    """Search YouTube for a video based on a youtube_query"""
    search_query_encoded = urllib.parse.quote(youtube_query)
    url = (
        f"https://www.googleapis.com/youtube/v3/search?key={youtube_api_key}"
        f"&q={search_query_encoded}&videoDuration=medium&videoEmbeddable=true"
        f"&type=video&maxResults=5&videoCaption=closedCaption"
    )

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"YouTube search failed: {e}")
        return None

    data = response.json()

    if not data.get("items") or len(data["items"]) == 0:
        print("YouTube search failed")
        return None

    return f"Youtube video ID: {data['items'][0]['id']['videoId']}"


def get_youtube_description(video_id: str) -> str:
    """Get the description of a YouTube video by its video ID."""
    url = f"https://www.googleapis.com/youtube/v3/videos?key={youtube_api_key}&part=snippet&id={video_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return f"Youtube video description: {data['items'][0]['snippet']['description']}"
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return "No description found"    
    

def get_transcript(video_id: str) -> str:
    """Get the transcript of a YouTube video by its video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        transcript = ' '.join([line['text'] for line in transcript_list])
        return transcript.replace('\n', ' ')
    except (TranscriptsDisabled, NoTranscriptFound) as error:
        print('failed to fetch transcript, fetching description instead')
        return get_youtube_description(video_id)
    
    
def summarize_video_transcript(transcript_video: str) -> str:
    """Summarize a YouTube video transcript. Use video transcript as input not video_id"""
    llm = ChatOpenAI(api_key=api_key, model='gpt-4o', temperature=0)

    template_prompt = """You are an AI capable of summarizing a YouTube transcript. Make sure you return the summary, you can't return blank. IF you cannot summarize the transcript, return the first 150 words of the transcript. Summarize in 150 words or less and do not talk of the sponsors or anything unrelated to the main topic, also do not introduce what the summary is about. IF you cannot summarize the transcript, return the first 150 words of the transcript
    
    Transcript: {transcript}

    using tools get_transcript for get the transcript

    """

    prompt = ChatPromptTemplate.from_template(template_prompt)

    parser = StrOutputParser()

    chain = prompt | llm | parser

    response = chain.invoke({
        'transcript': transcript_video
    })

    return response


def generate_question(transcript_video: str) -> dict:
    """Generate a question from a YouTube video transcript."""

    llm = ChatOpenAI(api_key=api_key, model='gpt-4o', temperature=0)

    template_prompt = """
    You are an advanced AI that generates challenging multiple-choice questions designed to assess **Higher Order Thinking Skills (HOTS)**. These questions should focus on application, analysis, evaluation, or creation, rather than simple recall or understanding.
    
    Instructions:
    1. Each question must challenge the user's ability to think critically or apply concepts creatively.
    2. The correct answer must not exceed 15 words and should appear in a randomized position.
    3. Provide four options, including one correct answer and three plausible distractors.
    4. Include an explanation for the correct answer to clarify the reasoning.

    Generate one hard MCQ question based on the following context/transcript video: {transcript}.

    Return the result in JSON format like the example below, ensuring the correct answer is randomly shuffled:
    {{
      "concept_check": [
        {{
            "question": "What is the capital of France?",
            "answer": {{
            "option1": "Paris",
            "option2": "Berlin",
            "option3": "Rome",
            "option4": "Madrid",
            "true_answer": "Paris"
            }}
        }},
        {{
            "question": "Which programming language is primarily used for data analysis?",
            "answer": {{
            "option1": "JavaScript",
            "option2": "Java",
            "option3": "C++",
            "option4": "Python",
            "true_answer": "Python"
            }}
        }}
    ]
    }}
    Shuffle the answer order each time. Generate 1 - 3 Questions.
    """

    prompt = ChatPromptTemplate.from_template(template_prompt)

    parser = JsonOutputParser()

    chain = prompt | llm | parser

    response = chain.invoke({
        "transcript": transcript_video
    })

    return response


def get_transcript(video_id: str) -> str:
    """Get the transcript of a YouTube video by its video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        transcript = ' '.join([line['text'] for line in transcript_list])
        return transcript.replace('\n', ' ')
    except (TranscriptsDisabled, NoTranscriptFound) as error:
        print(f'Failed to fetch transcript for video ID {video_id}, fetching description instead')
        return 'Transcript not available'

 
def parsing_youtube_id(url: str) -> str:
    """Parsing youtube video id from youtube url"""
    try:
        # Mengatasi beberapa variasi URL YouTube
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]  # Mengambil ID dari parameter URL
        elif "youtu.be" in url:
            return url.split("/")[-1]  # Mengambil ID dari URL pendek YouTube
        else:
            raise ValueError("URL format is not supported")
    except Exception as e:
        print(f"Error parsing YouTube ID from URL: {url}. Error: {e}")
        return None


# test function
if __name__ == '__main__':
    search = search_youtube('python programming')
    print(search)
    transcript = get_transcript('8e_Uzi58hQc')
    print(transcript)

