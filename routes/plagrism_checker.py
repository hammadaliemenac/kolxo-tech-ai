from fastapi import APIRouter
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from ddgs import DDGS
import textstat
import re
import asyncio
from utils import model, tool

router = APIRouter()

# -------------------------------
# 🔹 REQUEST MODEL
# -------------------------------
class PlagiarismCheckRequest(BaseModel):
    query: str


# -------------------------------
# 🔹 TEXT ANALYSIS
# -------------------------------
def sent_tokenize(text):
    return re.split(r'(?<=[.!?]) +', text)

def analyze_text(text):
    if not tool:
        return {
            "grammar_errors": 0,
            "spelling_errors": 0,
            "punctuation_errors": 0,
            "readability_score": 0,
            "conciseness_score": 0
        }

    matches = tool.check(text)
    grammar_errors = sum(1 for m in matches if m.rule_issue_type == 'grammar')
    spelling_errors = sum(1 for m in matches if m.rule_issue_type == 'misspelling')
    punctuation_errors = sum(1 for m in matches if m.rule_issue_type == 'typographical')

    readability_score = round(textstat.flesch_reading_ease(text))
    avg_words_per_sentence = len(text.split()) / max(1, len(sent_tokenize(text)))
    conciseness_score = max(0, 100 - avg_words_per_sentence)

    return {
        "grammar_errors": grammar_errors,
        "spelling_errors": spelling_errors,
        "punctuation_errors": punctuation_errors,
        "readability_score": readability_score,
        "conciseness_score": round(conciseness_score)
    }


# -------------------------------
# 🔹 HELPERS
# -------------------------------
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


async def search_web_async(query):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, search_web, query)

def search_web(query):
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                title = r.get('title', '')
                body = r.get('body', '')
                combined = clean_text(f"{title}. {body} || {query}")
                if len(combined) > 40:
                    results.append(combined)
    except Exception:
        return []
    return list(set(results))  # remove duplicates early


# -------------------------------
# 🔹 MAIN API
# -------------------------------
@router.post("/check-plagiarism/")
async def check_plagiarism(request: PlagiarismCheckRequest):
    text = request.query
    sentences = [s.strip() for s in sent_tokenize(text) if len(s.strip()) >= 15]

    output = []

    # Run all searches concurrently
    search_tasks = [search_web_async(sentence) for sentence in sentences]
    web_results_list = await asyncio.gather(*search_tasks)

    for sentence, web_results in zip(sentences, web_results_list):
        if not web_results:
            continue

        embeddings = model.encode([sentence] + web_results)
        scores = cosine_similarity([embeddings[0]], embeddings[1:])[0]
        max_score = float(max(scores))

        if max_score > 0.85:
            label = "High"
        elif max_score > 0.6:
            label = "Medium"
        else:
            label = "Low"

        output.append({
            "sentence": sentence,
            "score": round(max_score * 100),
            "level": label,
            "matches": [
                {"text": web_results[i], "similarity": round(scores[i] * 100, 2)}
                for i in range(len(web_results))
            ]
        })

    plagiarism_score = round(sum([r["score"] for r in output]) / len(output)) if output else 0
    text_analysis = analyze_text(text)

    return format_response_html(text, output, plagiarism_score, text_analysis)


# -------------------------------
# 🔹 HTML FORMATTER
# -------------------------------
def format_response_html(text, output, plagiarism_score, text_analysis):
    grammar = text_analysis.get("grammar_errors", 0)
    spelling = text_analysis.get("spelling_errors", 0)
    punctuation = text_analysis.get("punctuation_errors", 0)
    readability_score = text_analysis.get("readability_score", 0)
    conciseness_score = text_analysis.get("conciseness_score", 0)

    readability_issues = 0 if readability_score >= 50 else 5
    conciseness_issues = 0 if conciseness_score >= 80 else 5
    total_issues = grammar + punctuation + conciseness_issues

    def issue_html(name, count):
        if count == 0:
            return f'<div class="issue-content"><span>{name}</span><span class="true">✔</span></div>'
        else:
            return f'<div class="issue-content"><span>{name}</span><span class="error">{count}</span></div>'

    html = f"""
    <div class="d-flex align-items-center { 'issue-text' if plagiarism_score < 10 else 'success-text' }">
        <span class="issue-number">{plagiarism_score}%</span>
        <span>{ 'No plagiarism detected!' if plagiarism_score < 10 else 'Plagiarism detected!' }
            Found <strong>{total_issues}</strong> writing issue{'' if total_issues==1 else 's'}.
        </span>
    </div>
    <div class="row gx-3 mt-3">
        <div class="col-6">{issue_html("Grammar", grammar)}{issue_html("Spelling", spelling)}{issue_html("Punctuation", punctuation)}</div>
        <div class="col-6">{issue_html("Conciseness", conciseness_issues)}{issue_html("Readability", readability_issues)}{issue_html("Word choice", 0)}</div>
    </div>
    """
    return html