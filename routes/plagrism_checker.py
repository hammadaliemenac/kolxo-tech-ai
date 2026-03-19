from fastapi import APIRouter
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from duckduckgo_search import DDGS
import textstat
import math
import re
import asyncio
from utils import model, tool


def sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text)

router = APIRouter()

# -------------------------------
# 🔹 REQUEST MODEL
# -------------------------------
class PlagiarismCheckRequest(BaseModel):
    query: str


# -------------------------------
# 🔹 TEXT ANALYSIS
# -------------------------------
def analyze_text(text):
    matches = tool.check(text)

    grammar_errors = 0
    spelling_errors = 0
    punctuation_errors = 0

    for match in matches:
        if match.rule_issue_type == 'misspelling':
            spelling_errors += 1
        elif match.rule_issue_type == 'grammar':
            grammar_errors += 1
        elif match.rule_issue_type == 'typographical':
            punctuation_errors += 1

    readability_score = textstat.flesch_reading_ease(text)

    word_count = len(text.split())
    sentence_count = max(1, len(sent_tokenize(text)))
    avg_words_per_sentence = word_count / sentence_count

    conciseness_score = max(0, 100 - avg_words_per_sentence)

    return {
        "grammar_errors": grammar_errors,
        "spelling_errors": spelling_errors,
        "punctuation_errors": punctuation_errors,
        "readability_score": round(readability_score),
        "conciseness_score": round(conciseness_score)
    }


# -------------------------------
# 🔹 HELPERS
# -------------------------------
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def optimize_query(sentence):
    words = sentence.split()
    return " ".join(words[:8])  # limit query length


def multi_query(sentence):
    words = sentence.split()
    return [
        " ".join(words[:6]),
        " ".join(words[-6:]),
        sentence[:60]
    ]


# -------------------------------
# 🔹 SEARCH (ASYNC)
# -------------------------------
def search_web(query):
    results = []

    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, region='us-en', safesearch='Off', timelimit='y', max_results=5):
                title = r.get('title', '')
                body = r.get('body', '')

                combined = clean_text(f"{title}. {body} || {query}")

                if len(combined) > 40:
                    results.append(combined)

    except Exception:
        return []

    return results


async def search_all_queries(sentence):
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, search_web, sentence)]

    results = await asyncio.gather(*tasks)
    print(f"Search results for '{sentence}': {results}")  # Debugging log
    # flatten results
    flat = [item for sublist in results for item in sublist]
    return list(set(flat))  # remove duplicates


# -------------------------------
# 🔹 MAIN API
# -------------------------------
@router.post("/check-plagiarism/")
async def check_plagiarism(request: PlagiarismCheckRequest):
    text = request.query
    sentences = sent_tokenize(text)

    output = []

    for sentence in sentences:
        sentence = sentence.strip()

        if len(sentence) < 15:
            continue

        web_results = await search_all_queries(sentence)

        if not web_results:
            continue

        embeddings = model.encode([sentence] + web_results)
        scores = cosine_similarity([embeddings[0]], embeddings[1:])[0]

        max_score = float(max(scores))

        # 🔥 better scoring logic
        if max_score > 0.85:
            label = "High"
        elif max_score > 0.6:
            label = "Medium"
        else:
            label = "Low"

        output.append({
            "sentence": sentence,
            "score": round(max_score * 100, 2),
            "level": label,
            "matches": [
                {"text": web_results[i], "similarity": round(max_score * 100, 2)}
                for i in range(len(web_results))
            ]
        })

    # -------------------------------
    # 🔹 FINAL SCORE
    # -------------------------------
    plagiarism_score = (
        round(sum([r["score"] for r in output]) / len(output), 2)
        if output else 0
    )

    text_analysis = analyze_text(text)

    return {
        "query": text,
        "results": {
            "plagiarism_results": output,
            "plagiarism_score": plagiarism_score,
            **text_analysis
        }
    }