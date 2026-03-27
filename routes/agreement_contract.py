from fastapi import APIRouter
from ollama import chat, generate
from pydantic import BaseModel

router = APIRouter()

class AgreementRequest(BaseModel):
    query: str

@router.post("/generate-agreement")
def generate_agreement(request: AgreementRequest):
    prompt = f"Generate a legal agreement based on the following query: {request.query} . Return only the final agreement without any explanations."
    response = generate(
        model='llama3',
        prompt=prompt
    )
    return {"query": request.query, "content": response.response}


class ContractRequest(BaseModel):
    party_a: str
    party_b: str
    contract_type: str
    query: str

@router.post("/generate-contract")   
def generate_contract(request: ContractRequest):
    prompt = f"""Generate a legal contract based on the following details:
        Party A: {request.party_a}
        Party B: {request.party_b}
        Contract Type: {request.contract_type}
        Description: {request.query}
        Return only the final contract without any explanations."""

    response = generate(
        model='llama3',
        prompt=prompt
    )
    return {"query": request.query, "content": response.response}
