import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.documents import Document
from tools import parsing_youtube_id, get_transcript
from uuid import uuid4
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState, StateGraph
from service.Chapter import Chapter
from service.Content import YouTubeContentGenerator
from config.setting import api_key
from model.models import InputMaterial, InputChapter, ListQuestion, Input, ChatRequest
from multiprocessing import Process, Pool
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, TypedDict
from langchain import hub
from langchain.agents import tool
from langgraph.graph import END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
import json

app = FastAPI()

class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


@app.get('/')
def index():
    return {'message': 'API is Running'}


@app.post('/generate-chapter')
async def generate_chapter(req: InputChapter):
    try:
        chapter_generator = Chapter()
        query = f"Create a course for {req.title} and units '{', '.join(req.units)}'"
        course_structure = chapter_generator.create_chapters(query)
        return {'status': 'success', 'data': course_structure}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'error generating chapters: {str(e)}')
    

def generate_single_content(chapter_data):
    try:
        title = chapter_data['title']
        youtube_query = chapter_data['youtube_query']
        youtube_content_generator = YouTubeContentGenerator()
        return youtube_content_generator.generate_course_content(title, youtube_query)
    except Exception as e:
        return {"error": f"Failed to generate content for {title}: {str(e)}"}


generated_content_response = []

@app.post('/generate-content')
async def generate_content(req: list[dict]):
    global generated_content_response
    try:
        results = []
        with ProcessPoolExecutor() as executor:
            futures = {executor.submit(generate_single_content, chapter): index for index, chapter in enumerate(req)}
            results = [None] * len(req)
            for future in as_completed(futures):
                index = futures[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    results[index] = {"error": f"Error generating content for chapter {req[index]['title']}: {str(e)}"}

        generated_content_response = results
        with open("generated_content.json", "w") as f:
            json.dump(results, f, indent=4)

        return {"status": "success", "data": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")


# Initialize graph outside the endpoint
documents = []
with open("generated_content.json", "r") as f:
    response_content = json.load(f)
    for chapter in response_content:
        video_id = parsing_youtube_id(chapter['youtube_link'])
        transcript = get_transcript(video_id) if video_id else 'Transcript not available'
        document = Document(
            page_content=(
                f'Ini adalah Pembelajaran Tentang/Topik Tentang: {chapter["chapter_title"]} \n\n'
                f'Ini adalah Summary/Ringkasan tentang topik tersebut: {chapter["summary"]} \n\n'
                f'Ini adalah Concept Check/Quiz yang muncul tentang Topik tersebut: {chapter["concept_check"]} \n\n'
                f'Ini adalah Youtube Link Tentang pembelajaran tentang topik tersebut: {chapter["youtube_link"]} \n\n'
                f'Ini adalah Transcript Video dari Youtube tersebut: {transcript}'
            ),
            metadata={'source': f'{chapter["youtube_link"]}'}
        )
        documents.append(document)

embeddings = OpenAIEmbeddings(api_key=api_key, model='text-embedding-3-large')
llm = ChatOpenAI(api_key=api_key, model='gpt-4o-mini', temperature=0)
prompt = hub.pull('rlm/rag-prompt')
vector_store = Chroma.from_documents(
    documents=documents,
    collection_name='learnify_chatbot',
    embedding=embeddings,
)

# Define application steps
def retrieve(state: State):
    retrieved_docs = vector_store.similarity_search(state["question"])
    return {"context": retrieved_docs}

def generate(state: State):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response.content }

@tool(response_format="content_and_artifact")
def retrieve(query: str):
    """Retrieve information related to a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}") for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# Step 1: Generate an AIMessage that may include a tool-call to be sent.
def query_or_respond(state: MessagesState):
    """Generate tool call for retrieval or respond."""
    llm_with_tools = llm.bind_tools([retrieve])
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# Step 2: Execute the retrieval.
tools = ToolNode([retrieve])

# Step 3: Generate a response using the retrieved content.
def generate(state: MessagesState):
    """Generate answer."""
    # Get generated ToolMessages
    recent_tool_messages = []
    for message in reversed(state["messages"]):
        if message.type == "tool":
            recent_tool_messages.append(message)
        else:
            break
    tool_messages = recent_tool_messages[::-1]

    # Format into prompt
    docs_content = "\n\n".join(doc.content for doc in tool_messages)
    system_message_content = (
        "You are an assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        f"{docs_content}"
    )
    conversation_messages = [
        message
        for message in state["messages"]
        if message.type in ("human", "system")
        or (message.type == "ai" and not message.tool_calls)
    ]
    prompt = [SystemMessage(system_message_content)] + conversation_messages

    # Run
    response = llm.invoke(prompt)
    return {"messages": [response]}

graph_builder = StateGraph(MessagesState)
graph_builder.add_node(query_or_respond)
graph_builder.add_node(tools)
graph_builder.add_node(generate)

graph_builder.set_entry_point("query_or_respond")
graph_builder.add_conditional_edges(
    "query_or_respond",
    tools_condition,
    {END: END, "tools": "tools"},
)
graph_builder.add_edge("tools", "generate")
graph_builder.add_edge("generate", END)

memory = MemorySaver()

graph = graph_builder.compile(checkpointer=memory)

class ChatResponse(BaseModel):
    answer: str

@app.post('/chat')
async def chat(req: ChatRequest):
    try:
        input_message = req.message
        response = graph.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": input_message
                }
            ]
        }, config={"configurable": {"thread_id": "production-learnify"}})

        # return in json format
        return ChatResponse(answer=response['messages'][-1].content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")
