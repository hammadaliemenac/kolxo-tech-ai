import language_tool_python
from sentence_transformers import SentenceTransformer


tool = language_tool_python.LanguageTool('en-US')
model = SentenceTransformer('all-MiniLM-L6-v2')
