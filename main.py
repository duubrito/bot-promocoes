from telethon import TelegramClient, events
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import os
from datetime import datetime

# --- VARIÁVEIS DE AMBIENTE ---
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
canal = os.getenv("CANAL")  # exemplo: 'https://t.me/seucanal'
nome_planilha = os.getenv("PLANILHA")  # exemplo: 'PromocoesTelegram'

# --- GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client_sheets = gspread.authorize(creds)
sheet = client_sheets.open(nome_planilha).sheet1

# --- FUNÇÕES DE EXTRAÇÃO ---
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

    foto = ""
    if event.message.photo:
        foto = f"https://t.me/{event.chat.username}/{event.message.id}"

    agora = datetime.now()
    return {
        "mensagem": texto,
        "produto": produto,
        "preco": preco.group() if preco else "",
        "link": link.group() if link else "",
        "cupom": cupom.group(1) if cupom else "",
        "foto": foto,
        "data": agora.strftime("%d/%m/%Y"),
        "hora": agora.strftime("%H:%M")
    }

# --- INICIAR CLIENTE ---
client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(chats=canal))
async def handler(event):
    dados = extrair_dados(event)
    print("Novo post:", dados)
    sheet.append_row([
        dados["mensagem"],
        dados["produto"],
        dados["preco"],
        dados["link"],
        dados["cupom"],
        dados["foto"],
        dados["data"],
        dados["hora"]
    ])

print("Bot rodando e monitorando seu canal...")
client.run_until_disconnected()
