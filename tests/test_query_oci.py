import os
import sys

# Get the directory of this script (which will be the project root on OCI)
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Load env from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from app.services.rag_chain import answer_question

# Query with leading Spanish question mark
query = "¿Cómo registrar un cliente nuevo?"
print("Query:", query)

# Test cleaning query
clean_query = query.strip().strip("¿?¡!.,;\"'")
print("Cleaned Query for Search:", clean_query)

response = answer_question(query)

print("\n--- Answer ---")
print(response.answer)

print("\n--- Sources ---")
for idx, src in enumerate(response.sources, start=1):
    print(f"{idx}. {src.source} -- page: {src.page}")
