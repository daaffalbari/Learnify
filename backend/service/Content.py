import sys
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import (
    search_youtube,
    get_youtube_description,
    get_transcript,
    summarize_video_transcript,
    generate_question
)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool

from typing import Dict, List
import json 
from config.setting import api_key



LANGCHAIN_TRACING_V2=os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT= os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT= os.getenv("LANGCHAIN_PROJECT")


class YouTubeContentGenerator:
    def __init__(self):
        # Initialize tools
        self.tools = self._create_tools()
        
        # Setup LLM and Agent
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-4o", temperature=0)
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools)


    def _create_tools(self) -> List[Tool]:
        """Create tools for the agent"""
        return [
            Tool(
                name="search_youtube",
                func=search_youtube,
                description="Search YouTube for a video based on a youtube_search_query"
            ),
            Tool(
                name="get_youtube_description",
                func=get_youtube_description,
                description="Get the description of a YouTube video by its video ID"
            ),
            Tool(
                name="get_transcript",
                func=get_transcript,
                description="Get the transcript of a YouTube video by its video ID"
            ),
            Tool(
                name="summarize_video_transcript",
                func=summarize_video_transcript,
                description="Summarize a YouTube video transcript using video transcript as input not video_id"
            ),
            Tool(
                name="generate_question",
                func=generate_question,
                description="Generate a question from a YouTube video transcript"
            )
        ]

    def _create_agent(self):
        """Create the agent with main prompt and tools"""
        main_prompt = """You are a helpful assistant that can help to generate course content. 
        Generate a question from a video transcript, summarize a video transcript from get_transcript, 
        search a video on YouTube and get the description of a video.
        
        To get the information about that content, You can use the following tools:
        1. tool_search_youtube
        2. tool_get_youtube_description
        3. tool_get_transcript
        4. tool_summarize_video_transcript
        5. tool_generate_question

        Output must be like this:
        {{
        "chapter_title": "",
        "summary": "",
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
        ],
        "youtube_link": "https://www.youtube.com/watch?v=<add_youtube_id_here>"
        }}
        
        """ 

        prompt = ChatPromptTemplate.from_messages([
            ("system", main_prompt),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])

        return create_openai_tools_agent(self.llm, tools=self.tools, prompt=prompt)

    def generate_course_content(self, title:str, youtube_query: str) -> Dict:
        """
        Generate course content based on a YouTube search query.
        
        :param youtube_search_query: Query to search YouTube
        :return: Dictionary containing generated course content

        """
        try:
            response = self.agent_executor.invoke({
                'input': f"buatkan content course dengan judul {title} dan youtube_search_query: {youtube_query}"
            })
            return self.generate_to_json_output(response)
        except Exception as e:
            print(f"Error generating course content: {str(e)}")
            return {'error': str(e)}
    

    def generate_to_json_output(self, response):
        cleaned_output = response['output'].strip().lstrip("```json").rstrip("```").strip()

        try:
            return json.loads(cleaned_output)
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            print(f"Raw Output: {cleaned_output}")
            return {"error": "Invalid JSON format", "raw_output": cleaned_output}
        
    def save_generated_content(self, content: Dict):
        with open("generated_content.json", "w") as f:
            json.dump(content, f, indent=4)
        print("Generated content saved to generated_content.json")
        
        
    

if __name__ == "__main__":
    content_generator = YouTubeContentGenerator()
    course_content = content_generator.generate_course_content("Generative AI", "Generative AI")
    print(course_content)
    print(type(course_content))
        




