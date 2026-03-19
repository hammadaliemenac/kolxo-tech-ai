from fastapi import APIRouter
from pydantic import BaseModel
import math
from sklearn.cluster import KMeans
from utils import  model
router = APIRouter()

class ClusterKeywordsRequest(BaseModel):
    query: str

@router.post("/cluster-keywords/")
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