import language_tool_python
from sentence_transformers import SentenceTransformer

try:
    tool = language_tool_python.LanguageTool('en-US')
except Exception as e:
    print("LanguageTool initialization failed:", e)
    tool = None
    
model = SentenceTransformer('all-MiniLM-L6-v2')
