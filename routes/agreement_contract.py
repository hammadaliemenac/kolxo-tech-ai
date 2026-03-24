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

@router.post("/generate-contract")
class ContractRequest(BaseModel):
    party_a: str
    party_b: str
    contract_type: str
    query: str
def generate_contract(request: ContractRequest):
    prompt = f"""Generate a legal contract based on the following details:
    Party A: {request.party_a}
    Party B: {request.party_b}
    Contract Type: {request.contract_type}
    Description: {request.query}
    Return only the final contract without any explanations."""
    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': prompt}],
    )
    return {"query": request.query, "content": response.message.content}
