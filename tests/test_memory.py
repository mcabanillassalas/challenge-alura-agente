import sys
import os
sys.path.append("d:/DevALURA/challenge-alura-agente/agente-alura-rag")

from dotenv import load_dotenv
load_dotenv("d:/DevALURA/challenge-alura-agente/agente-alura-rag/.env")

from app.services.rag_chain import answer_question
from app.schemas.ask import MessageItem

print("=== STARTING MULTI-TURN CONVERSATION TEST ===")

# Turn 1
q1 = "¿Cómo registrar un cliente nuevo?"
print(f"\nUser: {q1}")
r1 = answer_question(q1, chat_history=[])
print(f"Assistant: {r1.answer}")

# Save to history
history = [
    MessageItem(role="user", content=q1),
    MessageItem(role="assistant", content=r1.answer)
]

# Turn 2
q2 = "¿Cuáles son sus carpetas?"
print(f"\nUser: {q2}")
r2 = answer_question(q2, chat_history=history)
print(f"Assistant: {r2.answer}")

print("\n--- Sources Used in Turn 2 ---")
for idx, src in enumerate(r2.sources, start=1):
    print(f"{idx}. {src.source} -- page: {src.page}")
