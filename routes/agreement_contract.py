from fastapi import APIRouter
from ollama import chat
from pydantic import BaseModel

router = APIRouter()

class AgreementRequest(BaseModel):
    query: str

@router.post("/generate-agreement")
def generate_agreement(request: AgreementRequest):
    prompt = f"Generate a legal agreement based on the following query: {request.query} . Return only the final agreement without any explanations."
    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': prompt}],
    )
    return {"query": request.query, "content": response.message.content}
