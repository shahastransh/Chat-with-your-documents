import os
import shutil
import traceback
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# LangChain imports for free open-source models
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is not set in the .env file")

app = FastAPI(title="Chat With Your Document API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_STORE = None
RETRIEVER = None

# Create a temporary directory for uploaded files
os.makedirs("temp_docs", exist_ok=True)

class ChatRequest(BaseModel):
    query: str
    model: str = "openai/gpt-oss-20b"  # Updated to current 2026 active model

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    global VECTOR_STORE, RETRIEVER
    
    file_location = f"temp_docs/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 1. Load the document
        if file.filename.endswith('.pdf'):
            loader = PyPDFLoader(file_location)
        elif file.filename.endswith('.docx'):
            loader = Docx2txtLoader(file_location)
        else:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported.")
            
        documents = loader.load()
        
        # 2. Chunk the text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        
        # 3. Embed using FREE local HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # 4. Store in an IN-MEMORY ChromaDB
        VECTOR_STORE = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings
        )
        
        RETRIEVER = VECTOR_STORE.as_retriever(search_kwargs={"k": 4})
        
        return {"message": f"Successfully processed {file.filename}", "chunks": len(chunks)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary document
        if os.path.exists(file_location):
            os.remove(file_location)


@app.post("/chat")
async def chat_with_document(request: ChatRequest):
    if not RETRIEVER:
        raise HTTPException(status_code=400, detail="Please upload a document first.")
        
    # Define fallback sequence with current active Groq models
    models_to_try = [
        request.model,
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b"
    ]
    
    # Remove duplicates while preserving order
    models_to_try = list(dict.fromkeys(models_to_try))
    last_error = None

    for model_name in models_to_try:
        try:
            print(f"Attempting to generate response with model: {model_name}")
            
            llm = ChatGroq(
                model_name=model_name,
                temperature=0.1
            )
            
            system_prompt = (
                "You are an assistant for question-answering tasks. "
                "Use the following pieces of retrieved context to answer the question. "
                "If you don't know the answer, say that you don't know. "
                "Use three sentences maximum and keep the answer concise."
                "\n\n"
                "Context: {context}"
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])
            
            question_answer_chain = create_stuff_documents_chain(llm, prompt)
            rag_chain = create_retrieval_chain(RETRIEVER, question_answer_chain)
            
            response = rag_chain.invoke({"input": request.query})
            
            print(f"Success with {model_name}")
            return {
                "model_used": model_name,
                "answer": response["answer"],
                "sources": [doc.page_content for doc in response["context"]]
            }
            
        except Exception as e:
            print(f"Failed with {model_name}: {str(e)}")
            last_error = e
            continue  # Move to the next model in the list

    # If the loop finishes without returning, all models failed
    print("ALL MODELS FAILED. Last error traceback:")
    traceback.print_exc()
    raise HTTPException(
        status_code=500, 
        detail=f"All models failed. Last error: {str(last_error)}"
    )