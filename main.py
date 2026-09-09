# Import the built-in os module to interact with the operating system (e.g., managing files, folders, and environment variables)
import os
# Import shutil for high-level file operations, such as copying data from uploaded file streams
import shutil
# Import traceback to extract and print detailed error logs if exceptions occur
import traceback
# Import essential components from FastAPI for building the web server, handling files, and raising HTTP errors
from fastapi import FastAPI, UploadFile, File, HTTPException
# Import CORS middleware to allow cross-origin requests (e.g., allowing a frontend app to talk to this API)
from fastapi.middleware.cors import CORSMiddleware
# Import BaseModel from Pydantic to strictly define and validate the data format of incoming requests
from pydantic import BaseModel
# Import load_dotenv to read key-value pairs from a .env file and set them as environment variables
from dotenv import load_dotenv

# LangChain imports
# Import specific LangChain loaders to read text out of PDF and Word (DOCX) documents
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
# Import the text splitter to divide large documents into smaller, overlapping chunks for better AI processing
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Import the Hugging Face embeddings wrapper to convert text chunks into numerical vectors
from langchain_huggingface import HuggingFaceEndpointEmbeddings
# Import ChatGroq to act as the interface for interacting with Groq's LLM models
from langchain_groq import ChatGroq
# Import Chroma to act as the local vector database where our embedded text chunks will be stored and searched
from langchain_chroma import Chroma
# Import ChatPromptTemplate to create structured, reusable instructions and prompts for the AI
from langchain_core.prompts import ChatPromptTemplate
# Import create_retrieval_chain to tie together the document searcher (retriever) and the answering logic
from langchain_classic.chains import create_retrieval_chain
# Import create_stuff_documents_chain to format and "stuff" the retrieved documents directly into the prompt context
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

# Execute load_dotenv to actually load the environment variables from the .env file into the script
load_dotenv()

# Verify that the Groq API key is present in the environment variables
if not os.getenv("GROQ_API_KEY"):
# If the key is missing, raise a critical error to stop the application from running
    raise ValueError("GROQ_API_KEY is not set in the .env file")
    
# Verify that the Hugging Face API token is present in the environment variables
if not os.getenv("HF_TOKEN"):
# If the token is missing, raise a critical error to stop the application from running
    raise ValueError("HF_TOKEN is not set. Please add it to your environment variables.")

# Initialize the FastAPI web server instance and give it a readable title
app = FastAPI(title="Chat With Your Document API")

# Add the CORS middleware to the FastAPI app to manage who can access the API
app.add_middleware(
# Specify the CORSMiddleware component
    CORSMiddleware,
# Allow connections from any domain (origins)
    allow_origins=["*"], 
# Allow cookies and other credentials to be included in the requests
    allow_credentials=True,
# Allow all standard HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
# Allow all types of HTTP headers in incoming requests
    allow_headers=["*"],
)

# Initialize a global variable that will later hold the Chroma vector database
VECTOR_STORE = None
# Initialize a global variable that will later hold the component responsible for finding relevant document chunks
RETRIEVER = None

# Create a temporary directory for uploaded files
# Create a folder named "temp_docs" to store incoming files; exist_ok=True prevents errors if the folder already exists
os.makedirs("temp_docs", exist_ok=True)

# Define the expected JSON body structure for incoming chat requests using Pydantic
class ChatRequest(BaseModel):
# Define a required 'query' field which is the question the user is asking
    query: str
# Define an optional 'model' field with a default fallback to an active 2026 Groq model
    model: str = "openai/gpt-oss-20b"  # Updated to current 2026 active model

# Define an API endpoint that triggers when a POST request is made to /upload
@app.post("/upload")
# Create an asynchronous handler function that expects a file upload
async def upload_document(file: UploadFile = File(...)):
# Explicitly state that we are modifying the global database and retriever variables
    global VECTOR_STORE, RETRIEVER
    
# Create the local path where the uploaded file will temporarily reside
    file_location = f"temp_docs/{file.filename}"
# Open the new local file in write-binary ("wb") mode
    with open(file_location, "wb") as buffer:
# Securely stream the contents of the uploaded file into the new local file buffer
        shutil.copyfileobj(file.file, buffer)
        
# Start a try-except-finally block to handle the document processing safely
    try:
        # 1. Load the document
# Check if the uploaded file's name indicates it's a PDF
        if file.filename.endswith('.pdf'):
# If it is a PDF, initialize LangChain's PDF loader for this file
            loader = PyPDFLoader(file_location)
# Check if the uploaded file's name indicates it's a Word document
        elif file.filename.endswith('.docx'):
# If it is a Word document, initialize LangChain's DOCX loader
            loader = Docx2txtLoader(file_location)
# Handle cases where the user uploaded an unsupported file format
        else:
# Throw a 400 Bad Request error back to the user
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files supported.")
            
# Instruct the loader to parse the file and extract its text into a list of Document objects
        documents = loader.load()
        
        # 2. Chunk the text
# Set up a tool to split long documents into smaller parts so the AI doesn't get overwhelmed
        text_splitter = RecursiveCharacterTextSplitter(
# Set the target max length for each chunk to 1000 characters
            chunk_size=1000,
# Tell the splitter to overlap chunks by 200 characters so context isn't lost at the borders
            chunk_overlap=200,
# Tell the splitter to try breaking at paragraphs, then new lines, then spaces to keep text natural
            separators=["\n\n", "\n", " ", ""]
# Close the RecursiveCharacterTextSplitter configuration
        )
# Apply the text splitter to the parsed documents, creating the final list of chunked documents
        chunks = text_splitter.split_documents(documents)
        
        # 3. Embed using the current Hugging Face Inference API format
# Set up the tool that will convert text chunks into searchable mathematical vectors (embeddings)
        embeddings = HuggingFaceEndpointEmbeddings(
# Specify the exact Hugging Face model to use for vectorizing the text
            model="sentence-transformers/all-MiniLM-L6-v2",
# Define what the Hugging Face model is doing (extracting features/embeddings)
            task="feature-extraction",
# Authenticate the connection using the Hugging Face token from environment variables
            huggingfacehub_api_token=os.getenv("HF_TOKEN")
# Close the embedding configuration
        )
        
        # 4. Store in an IN-MEMORY ChromaDB
# Process all the chunks, convert them to vectors, and store them in an in-memory Chroma database instance
        VECTOR_STORE = Chroma.from_documents(
# Pass the list of text chunks
            documents=chunks,
# Pass the configured embedding tool used to vectorize them
            embedding=embeddings
# Close the Chroma database initialization
        )
        
# Tell the vector store to act as a retriever that finds the top 4 ("k": 4) most relevant chunks for any query
        RETRIEVER = VECTOR_STORE.as_retriever(search_kwargs={"k": 4})
        
# Return a successful JSON response to the user with the file name and the amount of chunks created
        return {"message": f"Successfully processed {file.filename}", "chunks": len(chunks)}
        
# Catch any errors that happen during the parsing, splitting, embedding, or storing processes
    except Exception as e:
# Send a 500 Internal Server Error response containing the exact error message
        raise HTTPException(status_code=500, detail=str(e))
# Define a cleanup block that runs unconditionally, whether the upload succeeded or failed
    finally:
        # Clean up the temporary document
# Check if the temporary physical file still exists on the server
        if os.path.exists(file_location):
# Delete the temporary file to avoid cluttering the server's storage
            os.remove(file_location)


# Define an API endpoint that triggers when a POST request is made to /chat
@app.post("/chat")
# Create an asynchronous handler function that expects a valid ChatRequest body
async def chat_with_document(request: ChatRequest):
# Check if a document has been successfully processed into the RETRIEVER yet
    if not RETRIEVER:
# If not, throw a 400 Bad Request asking the user to upload a document first
        raise HTTPException(status_code=400, detail="Please upload a document first.")
        
    # Define fallback sequence with current active Groq models
# Create a list of LLM names to try, prioritizing the requested model and falling back to others if it fails
    models_to_try = [
# Add the specific model requested by the user's API call
        request.model,
# Add the first fallback model
        "openai/gpt-oss-20b",
# Add the second fallback model
        "openai/gpt-oss-120b",
# Add the third fallback model
        "qwen/qwen3-32b"
# Close the list of models
    ]
    
    # Remove duplicates while preserving order
# Convert the list to a dictionary (to naturally strip duplicates) and back to a list to keep order intact
    models_to_try = list(dict.fromkeys(models_to_try))
# Initialize a variable to track the most recent error message in case all models fail
    last_error = None

# Begin iterating over the list of LLMs we want to attempt to use
    for model_name in models_to_try:
# Start a try-except block so that if an LLM is offline or overloaded, the script doesn't completely crash
        try:
# Print a debug message to the server console tracking which model is currently being tested
            print(f"Attempting to generate response with model: {model_name}")
            
# Initialize the LangChain ChatGroq interface
            llm = ChatGroq(
# Specify the model name for this specific loop iteration
                model_name=model_name,
# Set the temperature to a low number (0.1) so the LLM responds factually instead of creatively
                temperature=0.1
# Close the ChatGroq initialization
            )
            
# Construct the system instructions telling the LLM how to behave
            system_prompt = (
# Define its role as an answering assistant
                "You are an assistant for question-answering tasks. "
# Instruct it to exclusively use the provided document context
                "Use the following pieces of retrieved context to answer the question. "
# Prevent hallucinations by telling it to admit when it doesn't know the answer
                "If you don't know the answer, say that you don't know. "
# Enforce a strict length limit to keep responses concise
                "Use three sentences maximum and keep the answer concise."
# Add line breaks for readability in the prompt string
                "\n\n"
# Inject the {context} variable placeholder where the retrieved text chunks will be inserted later
                "Context: {context}"
# Close the system_prompt string declaration
            )
            
# Create a formal PromptTemplate mapping the system prompt and the user's input
            prompt = ChatPromptTemplate.from_messages([
# Assign the system_prompt string to the "system" role
                ("system", system_prompt),
# Assign a placeholder {input} for the user's question to the "human" role
                ("human", "{input}"),
# Close the messages list definition
            ])
            
# Combine the configured LLM and the prompt template into a single processing chain
            question_answer_chain = create_stuff_documents_chain(llm, prompt)
# Wrap the answering chain in a retrieval chain that automatically fetches relevant documents from RETRIEVER first
            rag_chain = create_retrieval_chain(RETRIEVER, question_answer_chain)
            
# Trigger the complete RAG process by passing the user's question into the chain
            response = rag_chain.invoke({"input": request.query})
            
# If it succeeded, print a debug message confirming which model successfully answered
            print(f"Success with {model_name}")
# Return the final JSON payload containing the answer and source material to the user
            return {
# Return the name of the model that successfully answered
                "model_used": model_name,
# Return the raw text answer generated by the LLM
                "answer": response["answer"],
# Extract the actual text content from the Document objects to show the user which sources were referenced
                "sources": [doc.page_content for doc in response["context"]]
# Close the successful return dictionary
            }
            
# If the current LLM failed (e.g., API timeout or error), catch the exception
        except Exception as e:
# Print a debug message explaining why the specific model failed
            print(f"Failed with {model_name}: {str(e)}")
# Store the exception locally so we have a record of the last error if all models fail
            last_error = e
# Skip the rest of this loop iteration and try the next model in models_to_try
            continue  # Move to the next model in the list

    # If the loop finishes without returning, all models failed
# Print a critical debug message to the server console indicating no fallback models worked
    print("ALL MODELS FAILED. Last error traceback:")
# Use the traceback library to dump the full execution error log for debugging
    traceback.print_exc()
# Send a 500 Internal Server Error back to the user since we cannot answer their question
    raise HTTPException(
# Specify the 500 status code
        status_code=500, 
# Include the text of the last encountered error for debugging on the frontend
        detail=f"All models failed. Last error: {str(last_error)}"
# Close the HTTPException configuration
    )