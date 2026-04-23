from fastapi import APIRouter
from pydantic import BaseModel
from ollama import generate

router = APIRouter()

class QueryPostGeneratorRequest(BaseModel):
    query: str
    post_type: str

PROMPTS = {
    "facebook": lambda query: f"""
You are an expert Social Media Manager specializing in Facebook content.

Task: Create a complete, engaging Facebook post.

Rules:
- Length: 150–300 words (optimal for Facebook engagement)
- Start with a strong hook or question to grab attention
- Use a conversational, friendly, and relatable tone
- Include 2–3 short paragraphs with line breaks for readability
- Add a clear Call-To-Action (CTA) at the end (e.g., "Comment below", "Share with a friend", "Click the link")
- Include 5–8 relevant hashtags at the end
- Use 2–4 relevant emojis naturally within the text
- No explanations, no labels, no prefixes
- Output ONLY the final post

Topic: {query}

Output:
""",

    "instagram": lambda query: f"""
You are an expert Social Media Manager specializing in Instagram content.

Task: Create a complete, engaging Instagram caption.

Rules:
- Length: 138–150 words (optimal for Instagram)
- Start with a punchy, attention-grabbing first line (visible before "more")
- Use an inspirational, aesthetic, or storytelling tone
- Include a clear Call-To-Action (e.g., "Save this post", "Tag a friend", "Drop a comment")
- Add a line break before hashtags
- Include 20–30 highly relevant hashtags grouped at the end
- Use 4–6 relevant emojis naturally in the caption
- No explanations, no labels, no prefixes
- Output ONLY the final caption

Topic: {query}

Output:
""",

    "twitter": lambda query: f"""
You are an expert Social Media Manager specializing in X (Twitter) content.

Task: Create a complete, engaging tweet thread (3–5 tweets).

Rules:
- Each tweet must be under 280 characters
- Number each tweet: 1/, 2/, 3/, etc.
- First tweet must be a strong hook that stops the scroll
- Use a bold, punchy, and direct tone
- Last tweet should include a CTA and 2–3 relevant hashtags
- Use 1–2 emojis per tweet
- No explanations, no labels, no prefixes
- Output ONLY the final tweet thread

Topic: {query}

Output:
""",

    "linkedin": lambda query: f"""
You are an expert Social Media Manager specializing in LinkedIn content.

Task: Create a complete, professional LinkedIn post.

Rules:
- Length: 200–250 words
- Start with a bold, thought-provoking hook (single line, no period)
- Use a professional yet human and authentic tone
- Structure: Hook → Personal insight or story → Key takeaway or lesson → CTA
- Add line breaks between each section for readability
- End with a reflective question to drive comments
- Include 5–7 professional, niche-relevant hashtags at the end
- Use 2–3 subtle emojis (✅, 💡, 🚀, etc.)
- No explanations, no labels, no prefixes
- Output ONLY the final post

Topic: {query}

Output:
""",

    "youtube": lambda query: f"""
You are an expert Social Media Manager specializing in YouTube content.

Task: Create a complete YouTube video description.

Rules:
- Length: 200–250 words
- First 2 lines must be compelling (shown before "Show more") — include primary keyword
- Include a brief overview of what the video covers (3–5 bullet points with ✅ or 🔹)
- Add a strong CTA section: Subscribe, Like, Comment, Share
- Include timestamps placeholder section: e.g., 00:00 - Intro
- Add social media links placeholder section
- End with 10–15 SEO-optimized hashtags
- No explanations, no labels, no prefixes
- Output ONLY the final description

Topic: {query}

Output:
""",

    "pinterest": lambda query: f"""
You are an expert Social Media Manager specializing in Pinterest content.

Task: Create a complete Pinterest post.

Rules:
- Length: 200–250 words
- First 2 lines must be compelling (shown before "Show more") — include primary keyword
- Include a brief overview of what the video covers (3–5 bullet points with ✅ or 🔹)
- Add a strong CTA section: Subscribe, Like, Comment, Share
- Include timestamps placeholder section: e.g., 00:00 - Intro
- Add social media links placeholder section
- End with 10–15 SEO-optimized hashtags
- No explanations, no labels, no prefixes
- Output ONLY the final description

Topic: {query}

Output:
""",
}

@router.post("/post-generator/")
def post_generator(request: QueryPostGeneratorRequest):
    post_type = request.post_type.lower()

    if post_type not in PROMPTS:
        return {
            "error": f"Invalid post_type '{request.post_type}'. Must be one of: {', '.join(PROMPTS.keys())}."
        }

    prompt = PROMPTS[post_type](request.query)

    response = generate(
        model='llama3',
        prompt=prompt
    )

    return {
        "query": request.query,
        "post_type": request.post_type,
        "content": response.response
    }