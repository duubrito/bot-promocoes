from telethon import TelegramClient, events
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re

# --- CONFIGURAÇÕES DO TELEGRAM ---
api_id = 27143574
api_hash = "62ab5efd67204a932d8d5ef92be9161a"
canal = "https://t.me/oqcomprei"

# --- CONFIGURAÇÕES DO GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client_sheets = gspread.authorize(creds)
sheet = client_sheets.open("PromocoesTelegram").sheet1

# --- FUNÇÃO PARA EXTRAIR DADOS DA MENSAGEM ---
def extrair_dados(mensagem):
    link = re.search(r'(https?://[^\s]+)', mensagem)
    preco = re.search(r'R?\$ ?\d+(?:[.,]\d{2})?', mensagem)
    produto = mensagem.split('\n')[0] if '\n' in mensagem else mensagem[:50]
    return {
        'mensagem': mensagem,
        'produto': produto,
        'preco': preco.group() if preco else '',
        'link': link.group() if link else ''
    }

# --- CLIENTE TELEGRAM ---
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage(chats=canal))
async def handler(event):
    texto = event.message.message
    if texto:
        dados = extrair_dados(texto)
        print("Nova mensagem recebida:", dados)
        try:
            sheet.append_row([dados['mensagem'], dados['produto'], dados['preco'], dados['link']])
            print("Mensagem salva na planilha.")
        except Exception as e:
            print("Erro ao salvar na planilha:", e)

print("Aguardando mensagens novas do canal...")
client.start()
client.run_until_disconnected()
