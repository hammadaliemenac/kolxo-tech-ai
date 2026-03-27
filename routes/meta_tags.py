from fastapi import APIRouter
from pydantic import BaseModel
from ollama import generate

router = APIRouter()

class QueryMetaTagsRequest(BaseModel):
    query: str
    meta_type: str

@router.post("/meta-tag-generator/")
def tag_generator(request: QueryMetaTagsRequest):
    if request.meta_type == 'meta_title':
        prompt = f"""
            You are an SEO assistant.

            Task: Generate a meta title.

            Rules:
            - Maximum 70 characters
            - No explanations
            - No quotes
            - No prefixes or labels
            - Output ONLY the final result

            Query: {request.query}

            Output:
            """

    elif request.meta_type == 'meta_description':
        prompt = f"""
            You are an SEO assistant.

            Task: Generate a meta description.

            Rules:
            - Maximum 160 characters
            - No explanations
            - No quotes
            - No prefixes or labels
            - Output ONLY the final result

            Query: {request.query}

            Output:
            """

    elif request.meta_type == 'meta_keywords':
        prompt = f"""
            You are an SEO assistant.

            Task: Generate meta keywords.

            Rules:
            - Comma-separated keywords
            - No explanations
            - No numbering
            - No quotes
            - Output ONLY the final result

            Query: {request.query}

            Output:
            """

    else:
        return {"error": "Invalid meta_type. Must be 'meta_title', 'meta_description', or 'meta_keywords'."}


    response = generate(
        model='llama3',
        prompt=prompt
    )
    return response
    # return {"query": request.query, "content": response.message.content}