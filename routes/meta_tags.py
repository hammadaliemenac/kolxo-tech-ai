from fastapi import APIRouter
from pydantic import BaseModel
from ollama import chat

router = APIRouter()

class QueryMetaTagsRequest(BaseModel):
    query: str
    meta_type: str

@router.post("/meta-tag-generator/")
def tag_generator(request: QueryMetaTagsRequest):
    if request.meta_type == 'meta_title':
        prompt = f"Generate a SEO based meta title for the following query: {request.query} . Maximum 70 characters & Return only the final meta title."
    elif request.meta_type == 'meta_description':
        prompt = f"Generate a SEO based meta description for the following query: {request.query} . Maximum 160 characters & Return only the final meta description."
    elif request.meta_type == 'meta_keywords':
        prompt = f"Generate SEO based meta keywords for the following query: {request.query} . Separate each keyword with a comma & Return only the final meta keywords."
    else:
        return {"error": "Invalid meta_type. Must be 'meta_title', 'meta_description', or 'meta_keywords'."}

    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': request.query}],
    )
    return {"query": request.query, "content": response.message.content}