# whatsapp-bot-fastapi

Template oficial **Bot WhatsApp + FastAPI** para [BlueSpark Cloud](https://cloud.bluesparkmz.com).

## BlueSpark Cloud

1. Cria um serviço **Bot WhatsApp** no teu projeto.
2. No serviço → **Config** → **Criar repo e enviar código** (ou liga este repo manualmente com GitHub).
3. Variáveis no painel (não commits `.env`):
   - `BLUESPARK_WHATSAPP_API_KEY` — token `bswa_…` do painel WhatsApp
   - `WEBHOOK_PUBLIC_URL` — preenchido pela plataforma
4. Painel **WhatsApp → Webhook** = `https://teu-subdominio.bluesparkmz.com/webhook/whatsapp`

Só precisas de **`main.py`** e **`requirements.txt`** no GitHub. O **Dockerfile é criado no servidor** BlueSpark Cloud no deploy — não commits Docker no teu repo.

## Personalizar

Edita `main.py` → função **`pick_reply`** (e o webhook se precisares).

```bash
git add main.py
git commit -m "Minhas respostas"
git push origin main
```

Push na **main** → BlueSpark redeploy automático.

## Local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set BLUESPARK_WHATSAPP_API_KEY=bswa_...
uvicorn main:app --reload --port 8000
```

## API BlueSpark

- `POST /api/whatsapp/dev/send-text` — header `X-API-Key`
- `POST /api/whatsapp/dev/send-media`

Ver painel WhatsApp → Automação (API).
