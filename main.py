import os
import json
import time
import requests
import anthropic
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram.constants import ChatAction
from datetime import datetime

AK = os.environ.get(“ANTHROPIC_KEY”, “”)
TT = os.environ.get(“TELEGRAM_TOKEN”, “”)
LK = os.environ.get(“LEONARDO_KEY”, “”)
SK = os.environ.get(“SERPER_KEY”, “”)
UID = int(os.environ.get(“ALLOWED_USER_ID”, “0”))
MODEL = “claude-sonnet-4-20250514”

SYSTEM = (
“Tu es l’agent IA autonome de Cedric, entrepreneur en Sarthe (France). “
“Projets: Luna Vega (influenceuse IA @luna.vega.off), Ecurie Del Luna (equestre Cre-sur-Loir), Personnel. “
“Luna: cheveux noirs ondules, peau olive, yeux marrons, boucles dorees. Leonardo FLUX Dev 832x1248. “
“Reponds en francais. Sois autonome, enchaine les outils sans confirmation.”
)

TOOLS = [
{
“name”: “web_search”,
“description”: “Recherche Google en temps reel”,
“input_schema”: {
“type”: “object”,
“properties”: {“query”: {“type”: “string”}},
“required”: [“query”]
}
},
{
“name”: “generate_image”,
“description”: “Genere une image Leonardo AI et l envoie sur Telegram”,
“input_schema”: {
“type”: “object”,
“properties”: {
“prompt”: {“type”: “string”},
“width”: {“type”: “integer”, “default”: 832},
“height”: {“type”: “integer”, “default”: 1248}
},
“required”: [“prompt”]
}
},
{
“name”: “send_status”,
“description”: “Envoie un message de progression a Cedric”,
“input_schema”: {
“type”: “object”,
“properties”: {“message”: {“type”: “string”}},
“required”: [“message”]
}
},
{
“name”: “get_datetime”,
“description”: “Date et heure actuelles en France”,
“input_schema”: {“type”: “object”, “properties”: {}}
}
]

async def run_tool(name, inp, cid, bot):
if name == “web_search”:
try:
r = requests.post(
“https://google.serper.dev/search”,
headers={“X-API-KEY”: SK, “Content-Type”: “application/json”},
json={“q”: inp[“query”], “num”: 5, “hl”: “fr”},
timeout=10
)
items = r.json().get(“organic”, [])[:5]
return “\n\n”.join([
“- “ + x.get(“title”, “”) + “\n” + x.get(“snippet”, “”)
for x in items
])
except Exception as e:
return “Erreur recherche: “ + str(e)

```
elif name == "generate_image":
    try:
        r = requests.post(
            "https://cloud.leonardo.ai/api/rest/v1/generations",
            headers={"Authorization": "Bearer " + LK, "Content-Type": "application/json"},
            json={
                "prompt": inp["prompt"],
                "modelId": "ac614f96-1082-45bf-be9d-757f2d31c174",
                "width": inp.get("width", 832),
                "height": inp.get("height", 1248),
                "num_images": 1
            },
            timeout=15
        )
        gid = r.json().get("sdGenerationJob", {}).get("generationId")
        if not gid:
            return "Erreur Leonardo: pas de generationId"
        await bot.send_chat_action(chat_id=cid, action=ChatAction.UPLOAD_PHOTO)
        for _ in range(12):
            time.sleep(5)
            c = requests.get(
                "https://cloud.leonardo.ai/api/rest/v1/generations/" + gid,
                headers={"Authorization": "Bearer " + LK},
                timeout=10
            )
            imgs = c.json().get("generations_by_pk", {}).get("generated_images", [])
            if imgs and imgs[0].get("url"):
                await bot.send_photo(
                    chat_id=cid,
                    photo=imgs[0]["url"],
                    caption="Image generee: " + inp["prompt"][:80]
                )
                return "Image envoyee OK"
        return "Timeout Leonardo"
    except Exception as e:
        return "Erreur image: " + str(e)

elif name == "send_status":
    await bot.send_message(chat_id=cid, text="Agent: " + inp["message"])
    return "OK"

elif name == "get_datetime":
    n = datetime.now()
    days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    return days[n.weekday()] + " " + n.strftime("%d/%m/%Y %H:%M")

return "Outil inconnu: " + name
```

async def run_agent(task, cid, bot):
client = anthropic.Anthropic(api_key=AK)
msgs = [{“role”: “user”, “content”: task}]
await bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)
for _ in range(10):
resp = client.messages.create(
model=MODEL,
max_tokens=2048,
system=SYSTEM,
tools=TOOLS,
messages=msgs
)
if resp.stop_reason == “end_turn”:
txt = “”.join(b.text for b in resp.content if hasattr(b, “text”))
if txt:
await bot.send_message(chat_id=cid, text=txt[:4000])
return
elif resp.stop_reason == “tool_use”:
msgs.append({“role”: “assistant”, “content”: resp.content})
results = []
for b in resp.content:
if b.type == “tool_use”:
await bot.send_chat_action(chat_id=cid, action=ChatAction.TYPING)
res = await run_tool(b.name, b.input, cid, bot)
results.append({
“type”: “tool_result”,
“tool_use_id”: b.id,
“content”: res
})
msgs.append({“role”: “user”, “content”: results})
else:
break

async def on_message(update, context):
if UID and update.effective_user.id != UID:
await update.message.reply_text(“Acces non autorise”)
return
try:
await run_agent(update.message.text, update.effective_chat.id, context.bot)
except Exception as e:
await update.message.reply_text(“Erreur: “ + str(e)[:200])

async def on_start(update, context):
await update.message.reply_text(
“Agent IA Cedric actif!\n\n”
“Envoie n’importe quelle tache.\n\n”
“Exemples:\n”
“- Genere une image Luna Vega plage\n”
“- Recherche tendances Instagram 2026\n”
“- Plan de contenu cette semaine”
)

def main():
print(“Agent demarre”)
app = Application.builder().token(TT).build()
app.add_handler(CommandHandler(“start”, on_start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
app.run_polling()

if **name** == “**main**”:
main()
