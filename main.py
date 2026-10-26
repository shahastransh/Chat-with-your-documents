# import os
# import shutil
# import traceback
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv

# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_groq import ChatGroq
# from langchain_chroma import Chroma
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_classic.chains import create_retrieval_chain
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# load_dotenv()

# if not os.getenv("GROQ_API_KEY"):
#     raise ValueError("GROQ_API_KEY is not set in the .env file or environment variables.")

# app = FastAPI(title="Chat With Your Document API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# VECTOR_STORE = None
# RETRIEVER = None

# os.makedirs("temp_docs", exist_ok=True)

# class ChatRequest(BaseModel):
#     query: str
#     model: str = "llama3-8b-8192"

# @app.post("/upload")
# async def upload_document(file: UploadFile = File(...)):
#     global VECTOR_STORE, RETRIEVER
    
#     file_location = f"temp_docs/{file.filename}"
#     with open(file_location, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
        
#     try:
#         if file.filename.endswith('.pdf'):
#             loader = PyPDFLoader(file_location)
#         elif file.filename.endswith('.docx'):
#             loader = Docx2txtLoader(file_location)
#         else:
#             raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported.")
            
#         documents = loader.load()
        
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200,
#             separators=["\n\n", "\n", " ", ""]
#         )
#         chunks = text_splitter.split_documents(documents)
        
#         # Define fallback sequence for embedding models
#         embedding_models_to_try = [
#             "sentence-transformers/all-MiniLM-L6-v2",
#             "BAAI/bge-small-en-v1.5",
#             "sentence-transformers/all-mpnet-base-v2"
#         ]
        
#         embedding_success = False
#         last_embed_error = None
        
#         for embed_model in embedding_models_to_try:
#             try:
#                 print(f"Attempting to embed with model: {embed_model}")
                
#                 embeddings = HuggingFaceEmbeddings(
#                     model_name=embed_model
#                 )
                
#                 VECTOR_STORE = Chroma.from_documents(
#                     documents=chunks,
#                     embedding=embeddings
#                 )
                
#                 RETRIEVER = VECTOR_STORE.as_retriever(search_kwargs={"k": 4})
#                 embedding_success = True
#                 print(f"Success with embedding model {embed_model}")
#                 break  # Exit loop if successful
                
#             except Exception as e:
#                 print(f"Embedding failed with {embed_model}: {str(e)}")
#                 last_embed_error = e
#                 continue
                
#         if not embedding_success:
#             raise HTTPException(
#                 status_code=500, 
#                 detail=f"All embedding models failed. Last error: {str(last_embed_error)}"
#             )
            
#         return {"message": f"Successfully processed {file.filename}", "chunks": len(chunks)}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         if os.path.exists(file_location):
#             os.remove(file_location)


# @app.post("/chat")
# async def chat_with_document(request: ChatRequest):
#     if not RETRIEVER:
#         raise HTTPException(status_code=400, detail="Please upload a document first.")
        
#     models_to_try = [
#         request.model,
#         "llama3-8b-8192",
#         "mixtral-8x7b-32768",
#         "gemma-7b-it"
#     ]
    
#     models_to_try = list(dict.fromkeys(models_to_try))
#     last_error = None

#     for model_name in models_to_try:
#         try:
#             print(f"Attempting to generate response with model: {model_name}")
            
#             llm = ChatGroq(
#                 model_name=model_name,
#                 temperature=0.1
#             )
            
#             system_prompt = (
#                 "You are an assistant for question-answering tasks. "
#                 "Use the following pieces of retrieved context to answer the question. "
#                 "If you don't know the answer, say that you don't know. "
#                 "Use three sentences maximum and keep the answer concise."
#                 "\n\n"
#                 "Context: {context}"
#             )
            
#             prompt = ChatPromptTemplate.from_messages([
#                 ("system", system_prompt),
#                 ("human", "{input}"),
#             ])
            
#             question_answer_chain = create_stuff_documents_chain(llm, prompt)
#             rag_chain = create_retrieval_chain(RETRIEVER, question_answer_chain)
            
#             response = rag_chain.invoke({"input": request.query})
            
#             print(f"Success with {model_name}")
#             return {
#                 "model_used": model_name,
#                 "answer": response["answer"],
#                 "sources": [doc.page_content for doc in response["context"]]
#             }
            
#         except Exception as e:
#             print(f"Failed with {model_name}: {str(e)}")
#             last_error = e
#             continue

#     print("ALL MODELS FAILED. Last error traceback:")
#     traceback.print_exc()
#     raise HTTPException(
#         status_code=500, 
#         detail=f"All models failed. Last error: {str(last_error)}"
#     )


# import os
# import shutil
# import traceback
# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from dotenv import load_dotenv

# from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_groq import ChatGroq
# from langchain_chroma import Chroma
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_classic.chains import create_retrieval_chain
# from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# load_dotenv()

# if not os.getenv("GROQ_API_KEY"):
#     raise ValueError("GROQ_API_KEY is not set in the .env file or environment variables.")
# if not os.getenv("GOOGLE_API_KEY"):
#     raise ValueError("GOOGLE_API_KEY is not set in the .env file or environment variables.")

# app = FastAPI(title="Chat With Your Document API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# VECTOR_STORE = None
# RETRIEVER = None

# os.makedirs("temp_docs", exist_ok=True)

# class ChatRequest(BaseModel):
#     query: str
#     model: str = "openai/gpt-oss-20b"

# @app.post("/upload")
# async def upload_document(file: UploadFile = File(...)):
#     global VECTOR_STORE, RETRIEVER
    
#     file_location = f"temp_docs/{file.filename}"
#     with open(file_location, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
        
#     try:
#         if file.filename.endswith('.pdf'):
#             loader = PyPDFLoader(file_location)
#         elif file.filename.endswith('.docx'):
#             loader = Docx2txtLoader(file_location)
#         else:
#             raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported.")
            
#         documents = loader.load()
        
#         text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=4000,
#             chunk_overlap=500,
#             separators=["\n\n", "\n", " ", ""]
#         )
#         chunks = text_splitter.split_documents(documents)
        
#         print("Attempting to embed with Google Generative AI")
#         embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")
        
#         VECTOR_STORE = Chroma.from_documents(
#             documents=chunks,
#             embedding=embeddings
#         )
        
#         RETRIEVER = VECTOR_STORE.as_retriever(search_kwargs={"k": 4})
#         print("Success with Google embedding model")
            
#         return {"message": f"Successfully processed {file.filename}", "chunks": len(chunks)}
        
#     except Exception as e:
#         print(f"Upload failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         if os.path.exists(file_location):
#             os.remove(file_location)


# @app.post("/chat")
# async def chat_with_document(request: ChatRequest):
#     if not RETRIEVER:
#         raise HTTPException(status_code=400, detail="Please upload a document first.")
        
#     models_to_try = [
#         request.model,
#         "openai/gpt-oss-20b",
#         "openai/gpt-oss-120b"
#     ]
    
#     models_to_try = list(dict.fromkeys(models_to_try))
#     last_error = None

#     for model_name in models_to_try:
#         try:
#             print(f"Attempting to generate response with model: {model_name}")
            
#             llm = ChatGroq(
#                 model_name=model_name,
#                 temperature=0.1
#             )
            
#             system_prompt = (
#                 "You are an assistant for question-answering tasks. "
#                 "Use the following pieces of retrieved context to answer the question. "
#                 "If you don't know the answer, say that you don't know. "
#                 "Use three sentences maximum and keep the answer concise."
#                 "\n\n"
#                 "Context: {context}"
#             )
            
#             prompt = ChatPromptTemplate.from_messages([
#                 ("system", system_prompt),
#                 ("human", "{input}"),
#             ])
            
#             question_answer_chain = create_stuff_documents_chain(llm, prompt)
#             rag_chain = create_retrieval_chain(RETRIEVER, question_answer_chain)
            
#             response = rag_chain.invoke({"input": request.query})
            
#             print(f"Success with {model_name}")
#             return {
#                 "model_used": model_name,
#                 "answer": response["answer"],
#                 "sources": [doc.page_content for doc in response["context"]]
#             }
            
#         except Exception as e:
#             print(f"Failed with {model_name}: {str(e)}")
#             last_error = e
#             continue

#     print("ALL MODELS FAILED. Last error traceback:")
#     traceback.print_exc()
#     raise HTTPException(
#         status_code=500, 
#         detail=f"All models failed. Last error: {str(last_error)}"
#     )



# 

# 


import os
import shutil
import time
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is not set.")
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY is not set.")

app = FastAPI(title="Chat With Your Document API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_STORE = None
RETRIEVER = None
IS_PROCESSING = False

os.makedirs("temp_docs", exist_ok=True)

class ChatRequest(BaseModel):
    query: str
    model: str = "openai/gpt-oss-20b"

def embed_in_background(chunks: list, batch_size: int, file_location: str, filename: str):
    global VECTOR_STORE, RETRIEVER, IS_PROCESSING
    IS_PROCESSING = True
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1} of {(len(chunks)//batch_size)+1}...")
            
            if VECTOR_STORE is None:
                VECTOR_STORE = Chroma.from_documents(documents=batch, embedding=embeddings)
            else:
                VECTOR_STORE.add_documents(documents=batch)
                
            RETRIEVER = VECTOR_STORE.as_retriever(search_kwargs={"k": 4})
            
            # Sleep only if there are more batches remaining
            if i + batch_size < len(chunks):
                print("Waiting 65 seconds for Google API free tier quota reset...")
                time.sleep(65)
                
        print(f"Finished processing {filename}")
    except Exception as e:
        print(f"Background processing failed: {str(e)}")
    finally:
        IS_PROCESSING = False
        if os.path.exists(file_location):
            os.remove(file_location)

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    global IS_PROCESSING
    if IS_PROCESSING:
        raise HTTPException(status_code=400, detail="A document is already processing. Please wait.")

    file_location = f"temp_docs/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Load immediately to evaluate document size
        loader = PyPDFLoader(file_location) if file.filename.endswith('.pdf') else Docx2txtLoader(file_location)
        documents = loader.load()
        
        # Dynamic chunking logic based on length
        num_pages = len(documents)
        if num_pages > 50:
            c_size, b_size = 2500, 8
        elif num_pages > 15:
            c_size, b_size = 1500, 15
        else:
            c_size, b_size = 1000, 25
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=c_size, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        
        total_batches = (len(chunks) // b_size) + (1 if len(chunks) % b_size != 0 else 0)
        
        # Calculate precise estimated seconds (65s wait between batches, plus ~5s API latency per batch)
        estimated_seconds = max(0, (total_batches - 1) * 65) + (total_batches * 5)
        
        background_tasks.add_task(embed_in_background, chunks, b_size, file_location, file.filename)
        
        return {
            "message": f"Upload accepted! Document length: {num_pages} pages.",
            "estimated_seconds": estimated_seconds
        }
        
    except Exception as e:
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_document(request: ChatRequest):
    if IS_PROCESSING:
        raise HTTPException(status_code=400, detail="Document is still processing in the background. Please wait.")
    if not RETRIEVER:
        raise HTTPException(status_code=400, detail="Please upload a document first.")
        
    models_to_try = [request.model, "openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    models_to_try = list(dict.fromkeys(models_to_try))
    last_error = None

    for model_name in models_to_try:
        try:
            llm = ChatGroq(model_name=model_name, temperature=0.1)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Use the following context to answer. Keep it concise.\n\nContext: {context}"),
                ("human", "{input}"),
            ])
            
            chain = create_retrieval_chain(RETRIEVER, create_stuff_documents_chain(llm, prompt))
            response = chain.invoke({"input": request.query})
            
            return {"model_used": model_name, "answer": response["answer"], "sources": [d.page_content for d in response["context"]]}
            
        except Exception as e:
            last_error = e
            continue

    raise HTTPException(status_code=500, detail=f"All models failed. Last error: {str(last_error)}")