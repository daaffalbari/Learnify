import os 
from dotenv import load_dotenv

_ = load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
youtube_api_key = os.getenv('YOUTUBE_API_KEY')

# MongoDB
mongo_uri = os.getenv('MONGO_URI')

port = os.getenv('PORT')