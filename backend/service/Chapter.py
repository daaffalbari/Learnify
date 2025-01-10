import os 
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from config.setting import api_key
from config.example_response import example_response

LANGCHAIN_TRACING_V2=os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT= os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT= os.getenv("LANGCHAIN_PROJECT")

class Chapter:
    """
    Kelas Chapter untuk membuat struktur kursus berdasarkan query yang diberikan. 
    """

    def __init__(self, model_name:str='gpt-4o', temperature:float=0):
        """
        Inisialisasi kelas Chapter dengan model language yang digunakan.

        Args:
            model_name (str): Nama model language yang akan digunakan.
            temperature (float): Tingkat kreativitas model.
        """
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(api_key=api_key, model=model_name, temperature=temperature)
        self.parser = JsonOutputParser()
        self.example_response = example_response


    def create_chapters(self, query:str) -> dict:
        """
        Membuat struktur kursus berdasarkan query yang diberikan.

        Args:
            query (str): Query untuk menghasilkan outline kursus.

        Returns:
            Dict: Struktur kursus dengan units dan chapters.
        """
        template_prompt = """
        You are an AI specialized in designing educational courses. Your role is to create a course consisting of up to 1 units, each containing a maximum of 3 chapters. For each chapter, you will suggest a detailed search query that can be used to find educational YouTube videos relevant to the topic. Only generate the educational content. 

        Here are your tasks:
        1. Generate a course title based on the provided course name.
        2. Divide the course into units with descriptive unit titles (maximum 5 units).
        3. Within each unit, create up to 3 detailed chapter titles.
        4. For every chapter, craft a YouTube search query tailored to finding informative educational videos on the topic.

        Here is the information you need to create the course:
        Query: {query}

        Output Format:
        {{
            "units": [
                {{
                    "title": "<Unit Title>",
                    "chapters": [
                        {{
                            "chapter_title": "<Chapter Title>",
                            "youtube_query": "<Search Query>"
                        }}
                    ]
                }}
            ]
        }}
        ---------------------------------------------------------------------------------
        Example Output:
        {example_response}
        """

        prompt = ChatPromptTemplate.from_template(template_prompt)

        chain = prompt | self.llm | self.parser

        response = chain.invoke({
            "query": query,
            "example_response": example_response
        })

        return response
    

# if __name__ == "__main__":
#     chapter_service = Chapter()
#     title = "Generative AI"
#     units = ['Beginner', 'Langchain', 'Real World Implementation']
#     query = f"Buatkan course dengan title '{title}' dan unit '{', '.join(units)}'"
#     course_structure = chapter_service.create_chapters(f"Buatkan course dengan title '{title}' dan unit '{', '.join(units)}'")
#     print(course_structure)