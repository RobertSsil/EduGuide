import os
import json
import numpy as np
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pypdf import PdfReader

# --- 1. CONFIGURAÇÃO INICIAL E ESTRUTURA RAG ---

load_dotenv() # Carrega a variável GEMINI_API_KEY do arquivo .env

# Inicialização do Cliente Gemini
client = genai.Client()

# Estrutura de Armazenamento RAG (simples, em memória)
document_chunks = [] # Lista de strings dos chunks do PDF
document_embeddings = None # Array NumPy com os embeddings dos chunks

def load_and_process_pdf(file_path: str):
    """Extrai texto do PDF e prepara os chunks para embedding."""
    global document_chunks
    
    # 1.1. Extração de Texto
    reader = PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    # 1.2. Simples Chunking (divisão por sentenças ou linhas para este exemplo)
    # Para um projeto maior, use langchain-text-splitters
    # Aqui, dividimos por linhas para manter o exemplo simples
    document_chunks = [chunk.strip() for chunk in full_text.split('\n') if chunk.strip()]
    print(f"PDF processado. Total de chunks: {len(document_chunks)}")
    return document_chunks

# NOVO CÓDIGO para a função create_and_store_embeddings
def create_and_store_embeddings():
    """Gera e armazena os embeddings para todos os chunks, usando loteamento (batching)."""
    global document_embeddings
    
    if not document_chunks:
        print("Erro: Nenhum chunk para embeddar.")
        return

    print("Gerando embeddings (isso pode levar alguns segundos)...")
    
    # Lista para armazenar todos os embeddings gerados
    all_embeddings = []
    
    # Defina o tamanho máximo do lote (Batch Size)
    BATCH_SIZE = 100 
    
    # Itera sobre os chunks, pulando de 100 em 100
    for i in range(0, len(document_chunks), BATCH_SIZE):
        batch = document_chunks[i:i + BATCH_SIZE]
        print(f"Processando lote {i//BATCH_SIZE + 1}: {len(batch)} chunks...")
        
        try:
            # Chama a API com o lote (batch) de no máximo 100
            response = client.models.embed_content(
                model='text-embedding-004',
                contents=batch 
            )
            # Adiciona os embeddings do lote à lista principal
            all_embeddings.extend(response['embedding'])
        except Exception as e:
            print(f"Erro ao processar o lote {i//BATCH_SIZE + 1}: {e}")
            return # Interrompe a execução em caso de erro

    # Converte a lista de todos os embeddings em um array NumPy
    document_embeddings = np.array(all_embeddings)
    print("Embeddings gerados e armazenados com sucesso.")
    print(f"Total de embeddings armazenados: {document_embeddings.shape[0]}")

def find_relevant_chunks(query: str, top_k: int = 3) -> str:
    """Busca os chunks mais relevantes para a query."""
    if document_embeddings is None:
        return "Erro: O banco de dados de embeddings não foi inicializado."

    # 3.1. Embeddar a Query
    query_embedding = client.models.embed_content(
        model='text-embedding-004',
        contents=query
    )['embedding']
    query_embedding = np.array(query_embedding)

    # 3.2. Calcular Similaridade do Cosseno
    # Produto escalar para similaridade, pois os vetores Gemini são normalizados
    similarities = np.dot(document_embeddings, query_embedding)

    # 3.3. Obter Índices dos top_k chunks
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]

    # 3.4. Montar o Contexto
    context = "\n---\n".join([document_chunks[i] for i in top_k_indices])
    return context

# --- 2. SERVIDOR FASTAPI E ENDPOINT ---

app = FastAPI()

# Permite que o frontend React acesse o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Troque "*" pelo URL do seu React em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo Pydantic para validar o corpo da requisição
class ChatQuery(BaseModel):
    query: str

@app.post("/chat")
def chat_with_gemini(data: ChatQuery):
    """Endpoint principal para conversação com o chatbot RAG."""
    user_query = data.query

    # 1. Encontrar contexto relevante no PDF
    context = find_relevant_chunks(user_query)

    # 2. Montar o Prompt para o Gemini
    system_instruction = (
        "Você é um chatbot educacional e oficial da UERN, focado em responder "
        "dúvidas sobre o calendário acadêmico e estrutura com base no contexto. "
        "Responda à pergunta do usuário **APENAS** com base no CONTEXTO fornecido. "
        "Não invente informações. Se a resposta não estiver no CONTEXTO, diga 'Desculpe, "
        "não encontrei esta informação específica no meu banco de dados sobre a UERN.'."
    )
    
    full_prompt = (
        f"CONTEXTO:\n---\n{context}\n---\n"
        f"PERGUNTA DO USUÁRIO: {user_query}"
    )

    # 3. Chamar a API Gemini
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        return {"response": response.text}
    except Exception as e:
        return {"response": f"Ocorreu um erro ao gerar a resposta: {str(e)}"}

# --- 3. INICIALIZAÇÃO DO BANCO DE DADOS (APÓS DEFINIR AS FUNÇÕES) ---

# Carrega o PDF e os embeddings na inicialização do servidor
pdf_file_path = "DADOS (1).pdf"
if os.path.exists(pdf_file_path):
    load_and_process_pdf(pdf_file_path)
    create_and_store_embeddings()
else:
    print(f"AVISO: Arquivo '{pdf_file_path}' não encontrado. O chatbot não terá contexto.")

# Execução: uvicorn server:app --reload