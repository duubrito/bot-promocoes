import re
import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# --- Configurações Telegram ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
canal = "https://t.me/promocoesdodiacanal"

# --- Configuração do Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client_sheets = gspread.authorize(creds)
sheet = client_sheets.open("PromocoesTelegram").sheet1

def limpar_texto(texto):
    return re.sub(r'[^\w\s\-.,]', '', texto)

def extrair_nome_produto(mensagem):
    linhas = mensagem.split('\n')
    provaveis = []
    for linha in linhas:
        limpa = limpar_texto(linha).strip()
        if len(limpa.split()) > 2 and "http" not in limpa and "R$" not in limpa and "cupom" not in limpa.lower():
            provaveis.append(limpa)
    return max(provaveis, key=len) if provaveis else ""

def extrair_dados(mensagem, data_envio):
    link = re.search(r'(https?://[^\s]+)', mensagem)
    preco = re.search(r'R?\$ ?\d+(?:[.,]\d{2})?', mensagem)
    cupom = re.search(r'[Cc]upom[:\- ]+([A-Z0-9]{4,20})', mensagem)
    foto = ""  # Pode ser preenchido depois com o download da mídia, se quiser
    produto = extrair_nome_produto(mensagem)

    return {
        'mensagem': mensagem,
        'produto': produto,
        'preco': preco.group() if preco else '',
        'link': link.group() if link else '',
        'cupom': cupom.group(1) if cupom else '',
        'foto': foto,
        'data': data_envio.strftime("%Y-%m-%d"),
        'horario': data_envio.strftime("%H:%M:%S")
    }

client = TelegramClient('session_bot', api_id, api_hash)

@client.on(events.NewMessage(chats=canal))
async def handler(event):
    texto = event.message.message
    data_envio = event.message.date.astimezone()
    dados = extrair_dados(texto, data_envio)
    print("Nova mensagem recebida:", dados)
    sheet.append_row([
        dados['mensagem'],
        dados['produto'],
        dados['preco'],
        dados['link'],
        dados['cupom'],
        dados['foto'],
        dados['data'],
        dados['horario']
    ])

print("Bot rodando e aguardando mensagens...")
with client:
    client.run_until_disconnected()
