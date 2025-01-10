import sys
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import get_transcript, parsing_youtube_id

from langchain_core.documents import Document
from uuid import uuid4


from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from config.setting import api_key

from langgraph.graph import MessagesState, StateGraph
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition, END


LANGCHAIN_TRACING_V2=os.getenv("LANGCHAIN_TRACING_V2")
LANGCHAIN_ENDPOINT= os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_PROJECT= os.getenv("LANGCHAIN_PROJECT")

class RAG:
    def __init__(self):
        self.llm = ChatOpenAI(api_key=api_key, model='gpt-4o-mini', temperature=0)
        self.embeddings = OpenAIEmbeddings(api_key=api_key, model='text-embedding-3-large')
        self.documents 

    def create_document(self, data):
        documents = []

        for chapter in data['data']:
            video_id = parsing_youtube_id(chapter['youtube_query'])
            if video_id:
                # 2. Ambil transcript dari video YouTube
                transcript = get_transcript(video_id)
            else:
                transcript = 'Transcript not available'
            
            # 3. Buat dokumen dengan memasukkan data dari chapter
            document = Document(
                page_content=(
                    f'Ini adalah Pembejaran Tentang/Topik Tentang: {chapter["chapter_title"]} \n\n'
                    f'Ini adalah Summary/Ringkasan tentang topik tersebut: {chapter["summary"]} \n\n'
                    f'Ini adalah Concept Check/Quiz yang muncul tentang Topik tersebut: {chapter["concept_check"]} \n\n'
                    f'Ini adalah Youtube Link Tentang pembelajaran tentang topik tersebut: {chapter["youtube_link"]} \n\n'
                    f'Ini adalah Transcript Video dari Youtube tersebut: {transcript}'
                ),
                metadata={'source': f'{chapter["youtube_link"]}'}
            )
            documents.append(document)

            # Membuat UUID secara unik untuk setiap dokumen
        uuids = [str(uuid4()) for _ in range(len(documents))]

        return documents
    

    # def create_vector_store(self):
