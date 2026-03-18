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

# Privacy Policy Generator Endpoint
class PrivacyPolicyRequest(BaseModel):
    policy_name: str = "Privacy Policy"
    content_language: str = "english"
    company_name: str = "Alharam"
    company_email: str = "hammadali.emenac@gmail.com"
    company_contact: str = "09874561233"
    company_domain: str = "alharamtravel.co.uk"
    data_protection_officer_contract: str = "on"
    company_services: str = "Tourism COmpany offers: international Tours"
    data_protection_measures: str = "yes"
    data_third_party: str = "yes"
    cookie_policy_url: str = "alharamtravel.co.uk/cookie-policy"
    data_transfer: str = "yes"
    age_restriction: str = "yes"
    data_communication: str = "yes"
    data_marketing: str = "yes"
    data_breach: str = "yes"
    data_policy: str = "yes"
    data_updates: str = "yes"

@app.post("/privacy-policy-generator/")
def read_item(request: PrivacyPolicyRequest):
    # Prepare the prompt for the OpenAI API
    prompt = f"Generate a privacy policy based on the following data:\n"
    prompt += f"Policy Name: {request.policy_name}\n"
    prompt += f"Content Language: {request.content_language}\n"
    prompt += f"Company Name: {request.company_name}\n"
    prompt += f"Company Email: {request.company_email}\n"
    prompt += f"Company Contact: {request.company_contact}\n"
    prompt += f"Company Domain: {request.company_domain}\n"
    prompt += f"Do you have a Data Protection Officer (DPO): {request.data_protection_officer_contract}\n"
    prompt += f"Services and products does company provide:  {request.company_services}\n"
    prompt += f"Are you using any data protection Measures: {request.data_protection_measures}\n"
    prompt += f"Do you share personal data with third-party service providers: {request.data_third_party}\n"
    prompt += f"Cookie Policy URL: {request.cookie_policy_url}\n"
    prompt += f"Do you transfer data to countries outside the EEA: {request.data_transfer}\n"
    prompt += f"Does your website have age requirements: {request.age_restriction}\n"
    prompt += f"Do you transfer data to countries outside the EEA for communication: {request.data_communication}\n"
    prompt += f"Do you transfer data to countries outside the EEA for marketing: {request.data_marketing}\n"
    prompt += f"Do you want to add a response time for data breach notifications: {request.data_breach}\n"
    prompt += f"Do you require opt-in for material changes: {request.data_policy}\n"
    prompt += f"Do you want to notify users of policy updates: {request.data_updates}\n"
    prompt += f"Please write the privacy policy in clear and formal {request.content_language} language, ensuring that it includes necessary data protection clauses and complies with relevant laws like GDPR and CCPA."

    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': prompt}],
    )
    return {"query": request.query, "content": response.message.content}

# AI Generator Endpoint
@app.get("/ai-generator/")
def read_item(query: str = 'Hello!'):
    response = chat(
        model='tinyllama',
        messages=[{'role': 'user', 'content': query}],
    )
    return {"query": query, "content": response.message.content}
