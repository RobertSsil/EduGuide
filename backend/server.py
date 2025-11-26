import os
import numpy as np
import time
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pypdf import PdfReader

# ---------------------------------------------------------
# CONFIGURAÇÃO INICIAL
# ---------------------------------------------------------

load_dotenv()
client = genai.Client()

document_chunks = []
document_embeddings = None


# ---------------------------------------------------------
# PROCESSAMENTO DO PDF
# ---------------------------------------------------------

def load_and_process_pdf(path: str):
    global document_chunks

    if not os.path.exists(path):
        print("PDF não encontrado:", path)
        return

    print("Carregando PDF:", path)

    reader = PdfReader(path)
    text = ""

    for page in reader.pages:
        extracted = page.extract_text() or ""
        text += extracted + "\n"

    chunks = [line.strip() for line in text.split("\n") if line.strip()]

    document_chunks = chunks
    print(f"PDF carregado: {len(chunks)} chunks")


def create_and_store_embeddings():
    global document_embeddings

    if not document_chunks:
        print("Nenhum chunk para embeddar.")
        return

    print("Gerando embeddings...")

    all_embeddings = []
    BATCH = 20
    RETRIES = 3

    for i in range(0, len(document_chunks), BATCH):
        batch = document_chunks[i:i + BATCH]
        print(f"Lote {i//BATCH + 1}: {len(batch)} itens")

        for attempt in range(RETRIES):
            try:
                response = client.models.embed_content(
                    model="text-embedding-004",
                    contents=batch
                )

                # o novo formato é: response.embeddings[x].values
                for emb in response.embeddings:
                    all_embeddings.append(emb.values)

                break

            except Exception as e:
                print(f"Tentativa {attempt + 1} falhou:", e)
                time.sleep(1)

                if attempt == RETRIES - 1:
                    dummy = [0.0] * 768
                    all_embeddings.extend([dummy] * len(batch))

    document_embeddings = np.array(all_embeddings)
    print(f"Embeddings gerados: {document_embeddings.shape[0]}")


# ---------------------------------------------------------
# BUSCA DE CONTEXTO
# ---------------------------------------------------------

def find_relevant_chunks(query: str, top_k: int = 3):
    if document_embeddings is None:
        return "Banco de embeddings não carregado."

    try:
        q = client.models.embed_content(
            model="text-embedding-004",
            contents=query
        )

        query_vector = np.array(q.embeddings[0].values)

    except Exception:
        return "Erro ao gerar embedding da pergunta."

    scores = np.dot(document_embeddings, query_vector)

    top_idx = np.argsort(scores)[-top_k:][::-1]

    return "\n---\n".join([document_chunks[i] for i in top_idx])


# ---------------------------------------------------------
# FASTAPI
# ---------------------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# modelo compatível COM O SEU FRONTEND
class ChatQuery(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
def chat_with_gemini(data: ChatQuery):
    user_msg = data.message

    context = find_relevant_chunks(user_msg)

    system_instruction = (
        "Você é um assistente acadêmico da UERN. "
        "Responda somente com base no CONTEXTO fornecido."
    )

    full_prompt = (
        f"CONTEXTO:\n---\n{context}\n---\n"
        f"PERGUNTA: {user_msg}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

        return {"response": response.text}

    except Exception as e:
        return {"response": f"Erro ao gerar resposta: {str(e)}"}


# ---------------------------------------------------------
# INICIALIZAÇÃO
# ---------------------------------------------------------

pdf_path = "DADOS (1).pdf"

if os.path.exists(pdf_path):
    load_and_process_pdf(pdf_path)
    create_and_store_embeddings()
else:
    print("PDF não encontrado. Chat sem contexto.")
