from ollama import chat



from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI on Ubuntu!"}

@app.get("/info/")
def read_info():
    return {"message": "This is the info endpoint for FastAPI on Ubuntu!"}

@app.get("/ai-generator/")
def read_item(query: str = 'Hello!'):
    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': query}],
    )
    return {"query": query, "content": response.message.content}