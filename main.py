from telethon import TelegramClient, events
import requests
import re
import os
from datetime import datetime

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
canal = os.getenv("CANAL")  # exemplo: @promocoesdodiacanal

spreadsheet_id = os.getenv("PLANILHA_ID")
access_token = os.getenv("GOOGLE_ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

def limpar_texto(texto):
    return re.sub(r'[^\w\s\-.,:;!?]', '', texto)

def extrair_nome_produto(mensagem):
    linhas = mensagem.split('\n')
    candidatos = [limpar_texto(l).strip() for l in linhas if len(l.split()) > 2 and "http" not in l and "R$" not in l]
    return max(candidatos, key=len) if candidatos else ""

def extrair_dados(event):
    texto = event.message.message or ""
    produto = extrair_nome_produto(texto)
    preco = re.search(r'R?\$ ?\d+(?:[.,]\d{2})?', texto)
    link = re.search(r'(https?://[^\s]+)', texto)
    cupom = re.search(r'[Cc]upom[:\- ]+([A-Z0-9]{4,20})', texto)
    foto = f"https://t.me/{event.chat.username}/{event.message.id}" if event.message.photo else ""
    agora = datetime.now()
    return [
        texto,
        produto,
        preco.group() if preco else "",
        link.group() if link else "",
        cupom.group(1) if cupom else "",
        foto,
        agora.strftime("%d/%m/%Y"),
        agora.strftime("%H:%M")
    ]

def enviar_para_planilha(valores):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:append?valueInputOption=USER_ENTERED"
    body = { "values": [valores] }
    response = requests.post(url, headers=headers, json=body)
    print("Resposta Google Sheets:", response.status_code, response.text)

client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(chats=canal))
async def handler(event):
    dados = extrair_dados(event)
    print("Novo post:", dados)
    enviar_para_planilha(dados)

print("Bot rodando e monitorando canal...")
client.run_until_disconnected()
