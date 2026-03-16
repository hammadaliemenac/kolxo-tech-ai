import math
from ollama import chat
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Means and SentenceTransformer imports for potential future use in clustering keywords
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost/",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1/",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500"
]
# Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <- allows all origins
    allow_credentials=True,
    allow_methods=["*"],   # <- allows all HTTP methods
    allow_headers=["*"],   # <- allows all headers
)

@app.get("/")
def read_root():
    return {"message": "Hello FastAPI on Ubuntu!"}

# Define a Pydantic model for the request body
class QueryMetaTagsRequest(BaseModel):
    query: str
    meta_type: str
    
@app.post("/meta-tag-generator/")
def tag_generator(request: QueryMetaTagsRequest):
    if request.meta_type == 'meta_title':
        prompt = f"Generate a meta title for the following query: {request.query} . Maximum 70 characters & Return only the final meta title."
    elif request.meta_type == 'meta_description':
        prompt = f"Generate a meta description for the following query: {request.query} . Maximum 160 characters & Return only the final meta description."
    elif request.meta_type == 'meta_keywords':
        prompt = f"Generate meta keywords for the following query: {request.query} . Separate each keyword with a comma & Return only the final meta keywords."
    else:
        return {"error": "Invalid meta_type. Must be 'meta_title', 'meta_description', or 'meta_keywords'."}

    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': request.query}],
    )
    return {"query": request.query, "content": response.message.content}

# Define a Pydantic model for the request body


class ClusterKeywordsRequest(BaseModel):
    query: str

@app.post("/cluster-keywords/")
@app.post("/cluster-keywords/")
def cluster_keywords(request: ClusterKeywordsRequest):

    keywords = [k.strip() for k in request.query.split(",") if k.strip()]

    if len(keywords) == 0:
        return {"error": "No keywords provided"}

    embeddings = model.encode(keywords)

    # Auto cluster detection
    num_clusters = min(len(keywords), max(1, int(math.sqrt(len(keywords)))))

    kmeans = KMeans(n_clusters=num_clusters, random_state=42)

    labels = kmeans.fit_predict(embeddings).tolist()

    clusters = {}

    # create clusters
    for keyword, label in zip(keywords, labels):
        clusters.setdefault(int(label), []).append(keyword)

    # add cluster names
    named_clusters = []

    for cluster_id, kw_list in clusters.items():

        # choose shortest keyword as cluster name
        cluster_name = min(kw_list, key=len)

        named_clusters.append({
            "cluster_id": cluster_id,
            "cluster_name": cluster_name,
            "keywords": kw_list
        })

    return {
        "query": request.query,
        "clusters": named_clusters
    }

    
@app.get("/ai-generator/")
def read_item(query: str = 'Hello!'):
    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': query}],
    )
    return {"query": query, "content": response.message.content}