from ollama import chat
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <- allows all origins
    allow_credentials=False,
    allow_methods=["*"],   # <- allows all HTTP methods
    allow_headers=["*"],   # <- allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI on Ubuntu!"}

@app.get("/ai-generator/")
def read_item(query: str = 'Hello!'):
    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': query}],
    )
    return {"query": query, "content": response.message.content}