from fastapi import APIRouter
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from ddgs import DDGS
import textstat
import math
import re
import asyncio
from utils import model
import language_tool_python

tool = language_tool_python.LanguageTool('en-US')


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
    if not tool:
        print("Language tool not initialized")
        return {
            "grammar_errors": 0,
            "spelling_errors": 0,
            "punctuation_errors": 0,
            "readability_score": 0,
            "conciseness_score": 0
        }

    matches = tool.check(text)

    grammar_errors = 0
    spelling_errors = 0
    punctuation_errors = 0

    for match in matches:
        issue = str(match.rule_issue_type).lower()

        if 'misspelling' in issue:
            spelling_errors += 1
        elif 'grammar' in issue:
            grammar_errors += 1
        elif 'typographical' in issue:
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


# -------------------------------
# 🔹 SEARCH (ASYNC)
# -------------------------------
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

    return results


async def search_all_queries(sentence):
    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, search_web, sentence)]

    results = await asyncio.gather(*tasks)
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
            "score": round(max_score * 100),
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
        round(sum([r["score"] for r in output]) / len(output))
        if output else 0
    )

    text_analysis = analyze_text(text)

    return format_response_html(text, output, plagiarism_score, text_analysis)

def format_response_html(text, output, plagiarism_score, text_analysis):
    # Extract analysis
    grammar = text_analysis.get("grammar_errors", 0)
    spelling = text_analysis.get("spelling_errors", 0)
    punctuation = text_analysis.get("punctuation_errors", 0)
    readability_score = text_analysis.get("readability_score", 0)
    conciseness_score = text_analysis.get("conciseness_score", 0)

    # Determine issue counts for conciseness/readability
    readability_issues = readability_score
    conciseness_issues = conciseness_score

    # Total issues
    total_issues = grammar + punctuation + conciseness_issues

    # Helper to decide status HTML
    def issue_html(name, count):
        if count == 0:
            return f"""
            <div class="issue-content">
                <span>{name}</span>
                <span class="true">
                    ✔
                </span>
            </div>
            """
        else:
            return f"""
            <div class="issue-content">
                <span>{name}</span>
                <span class="error">{count}</span>
            </div>
            """
       

    # Build HTML
    html = f"""
    <div class="d-flex align-items-center justify-content-start { "issue-text" if plagiarism_score < 10 else "success-text" }">
        <span class="issue-number">{plagiarism_score}%</span>
        <span>
            { "No plagiarism detected! Your text looks original." if plagiarism_score < 10 
                else "Plagiarism detected! Some parts of your text may not be original." }
            We analyzed your text and found <strong>{total_issues}</strong> writing issue{'' if total_issues == 1 else 's'}.
        </span>
    </div>
    <div class="row gx-3 gx-sm-4 gx-xl-5 mt-3">
        <div class="col-6">
            {issue_html("Grammar", grammar)}
            {issue_html("Spelling", spelling)}
            {issue_html("Punctuation", punctuation)}
        </div>
        <div class="col-6">
            {issue_html("Conciseness", conciseness_issues)}
            {issue_html("Readability", readability_issues)}
            {issue_html("Word choice", 0)}
        </div>
    </div>
    """
    return html