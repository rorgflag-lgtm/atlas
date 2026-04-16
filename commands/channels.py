# ============================================================
# ATLAS - Gestion des canaux de communication
# ============================================================

import os
import threading
import requests
import urllib3
from api_config import API_BASE_URL, API_KEY, ROUTES
from config import get_model_path
from utils import print_atlas, print_error, print_success, ask, print_section
from commands.transfer import upload_model

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ──────────────────────────────────────────────────────────────
# TEXTES MULTILINGUES DES CANAUX
# ──────────────────────────────────────────────────────────────

CHANNEL_UI = {
    "en": {
        "section_title": "COMMUNICATION CHANNELS SETUP",
        "intro": [
            "You can connect one or more channels.",
            "From these channels you will be able to:",
            "  - Chat with your AI",
            "  - Train it with /train <your text>",
            "  - Fine-tune it with /finetuning input : ... reply : ...",
            "Type 'no' or press Enter to skip a channel.",
        ],
        "tg_section": "TELEGRAM",
        "tg_steps": [
            "How to get your Telegram Bot Token:",
            "",
            "  Step 1 : Open Telegram and search for @BotFather",
            "  Step 2 : Start a chat and send the command /newbot",
            "  Step 3 : Choose a display name for your bot  (e.g. My ATLAS Bot)",
            "  Step 4 : Choose a username ending in 'bot'  (e.g. myatlasbot)",
            "  Step 5 : BotFather will send you a token like:",
            "           110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw",
            "  Step 6 : Copy and paste that token below.",
            "",
            "  Your bot will be reachable at t.me/<username>",
        ],
        "tg_prompt": "Telegram Bot Token (or Enter to skip)",
        "tg_ok":     "Telegram configured.",
        "wa_section": "WHATSAPP (via Twilio)",
        "wa_steps": [
            "How to connect WhatsApp via Twilio:",
            "",
            "  Step 1 : Create a free account at https://www.twilio.com",
            "  Step 2 : In the Twilio Console, go to:",
            "           Messaging > Try it out > Send a WhatsApp message",
            "  Step 3 : Follow the Twilio sandbox instructions:",
            "           - Send the join code from your WhatsApp to the sandbox number",
            "  Step 4 : Copy your Account SID from the Console dashboard",
            "           (looks like: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)",
            "  Step 5 : Copy your Auth Token from the same dashboard",
            "  Step 6 : Note the Twilio sandbox number",
            "           (looks like: whatsapp:+14155238886)",
            "  Step 7 : After setup, expose port 5000 with:",
            "           ngrok http 5000",
            "           and set the webhook URL in Twilio to:",
            "           https://<your-ngrok-url>/whatsapp",
        ],
        "wa_sid_prompt":    "Twilio Account SID (or Enter to skip)",
        "wa_token_prompt":  "Twilio Auth Token",
        "wa_number_prompt": "Twilio WhatsApp number  (e.g. whatsapp:+14155238886)",
        "wa_ok":            "WhatsApp configured.",
        "dc_section": "DISCORD",
        "dc_steps": [
            "How to get your Discord Bot Token:",
            "",
            "  Step 1 : Go to https://discord.com/developers/applications",
            "  Step 2 : Click 'New Application' and give it a name",
            "  Step 3 : In the left menu, click 'Bot'",
            "  Step 4 : Click 'Add Bot' then confirm",
            "  Step 5 : Under 'TOKEN', click 'Reset Token' then 'Copy'",
            "           (looks like: MTA0...XXXX.Yy...ZZZ)",
            "  Step 6 : In 'Privileged Gateway Intents', enable:",
            "           - MESSAGE CONTENT INTENT",
            "  Step 7 : Go to 'OAuth2 > URL Generator':",
            "           - Scopes      : bot",
            "           - Permissions : Send Messages, Read Message History",
            "  Step 8 : Open the generated URL in your browser to invite the bot",
            "  Step 9 : Paste the token below.",
        ],
        "dc_prompt": "Discord Bot Token (or Enter to skip)",
        "dc_ok":     "Discord configured.",
        "no_channels": "No channel configured. Conversation in the terminal only.",
    },

    "fr": {
        "section_title": "CONFIGURATION DES CANAUX DE COMMUNICATION",
        "intro": [
            "Vous pouvez connecter un ou plusieurs canaux.",
            "Depuis ces canaux vous pourrez :",
            "  - Converser avec votre IA",
            "  - L'entraîner avec /train <votre texte>",
            "  - La fine-tuner avec /finetuning input : ... reply : ...",
            "Tapez 'non' ou appuyez sur Entrée pour ignorer un canal.",
        ],
        "tg_section": "TELEGRAM",
        "tg_steps": [
            "Comment obtenir votre Token de Bot Telegram :",
            "",
            "  Étape 1 : Ouvrez Telegram et recherchez @BotFather",
            "  Étape 2 : Démarrez une conversation et envoyez /newbot",
            "  Étape 3 : Choisissez un nom d'affichage pour votre bot  (ex : Mon Bot ATLAS)",
            "  Étape 4 : Choisissez un nom d'utilisateur terminant par 'bot'  (ex : monatlasbot)",
            "  Étape 5 : BotFather vous enverra un token comme :",
            "           110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw",
            "  Étape 6 : Copiez et collez ce token ci-dessous.",
            "",
            "  Votre bot sera accessible à t.me/<nom_utilisateur>",
        ],
        "tg_prompt": "Token du Bot Telegram (ou Entrée pour ignorer)",
        "tg_ok":     "Telegram configuré.",
        "wa_section": "WHATSAPP (via Twilio)",
        "wa_steps": [
            "Comment connecter WhatsApp via Twilio :",
            "",
            "  Étape 1 : Créez un compte gratuit sur https://www.twilio.com",
            "  Étape 2 : Dans la Console Twilio, allez dans :",
            "            Messaging > Try it out > Send a WhatsApp message",
            "  Étape 3 : Suivez les instructions du sandbox Twilio :",
            "            - Envoyez le code d'adhésion depuis votre WhatsApp au numéro sandbox",
            "  Étape 4 : Copiez votre Account SID depuis le tableau de bord",
            "            (ressemble à : ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)",
            "  Étape 5 : Copiez votre Auth Token depuis le même tableau de bord",
            "  Étape 6 : Notez le numéro sandbox Twilio",
            "            (ressemble à : whatsapp:+14155238886)",
            "  Étape 7 : Après la configuration, exposez le port 5000 avec :",
            "            ngrok http 5000",
            "            et définissez l'URL webhook dans Twilio vers :",
            "            https://<votre-url-ngrok>/whatsapp",
        ],
        "wa_sid_prompt":    "Twilio Account SID (ou Entrée pour ignorer)",
        "wa_token_prompt":  "Twilio Auth Token",
        "wa_number_prompt": "Numéro WhatsApp Twilio  (ex : whatsapp:+14155238886)",
        "wa_ok":            "WhatsApp configuré.",
        "dc_section": "DISCORD",
        "dc_steps": [
            "Comment obtenir votre Token de Bot Discord :",
            "",
            "  Étape 1 : Allez sur https://discord.com/developers/applications",
            "  Étape 2 : Cliquez sur 'New Application' et donnez-lui un nom",
            "  Étape 3 : Dans le menu de gauche, cliquez sur 'Bot'",
            "  Étape 4 : Cliquez sur 'Add Bot' puis confirmez",
            "  Étape 5 : Sous 'TOKEN', cliquez sur 'Reset Token' puis 'Copy'",
            "            (ressemble à : MTA0...XXXX.Yy...ZZZ)",
            "  Étape 6 : Dans 'Privileged Gateway Intents', activez :",
            "            - MESSAGE CONTENT INTENT",
            "  Étape 7 : Allez dans 'OAuth2 > URL Generator' :",
            "            - Scopes      : bot",
            "            - Permissions : Send Messages, Read Message History",
            "  Étape 8 : Ouvrez l'URL générée dans votre navigateur pour inviter le bot",
            "  Étape 9 : Collez le token ci-dessous.",
        ],
        "dc_prompt": "Token du Bot Discord (ou Entrée pour ignorer)",
        "dc_ok":     "Discord configuré.",
        "no_channels": "Aucun canal configuré. Conversation uniquement dans le terminal.",
    },
}


# ──────────────────────────────────────────────────────────────
# HEADERS COMMUNS
# ──────────────────────────────────────────────────────────────

def _build_headers():
    return {
        "Authorization":              f"Bearer {API_KEY}",
        "ngrok-skip-browser-warning": "true",
        "Content-Type":               "application/json",
    }


# ──────────────────────────────────────────────────────────────
# ÉTAT D'INFÉRENCE PAR IA - COPIE EXACTE DE INFER.PY
# ──────────────────────────────────────────────────────────────

_channel_states = {}
_channel_lock = threading.Lock()


def _get_channel_state(ai_name):
    """Récupère l'état pour un ai_name donné."""
    with _channel_lock:
        if ai_name not in _channel_states:
            _channel_states[ai_name] = {
                "upload_id": None,
                "weights_sent": False
            }
        return _channel_states[ai_name]


def _do_upload(ai_name):
    """Upload le modèle par chunks comme infer.py."""
    model_file = os.path.join(get_model_path(ai_name), f"{ai_name}.bin")
    if not os.path.exists(model_file):
        return None
    try:
        return upload_model(
            model_file=model_file,
            api_base_url=API_BASE_URL,
            headers=_build_headers(),
            print_fn=lambda _: None,
        )
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# ROUTEUR CENTRAL DES MESSAGES
# ──────────────────────────────────────────────────────────────

def route_message(text, ai_name, send_reply_func):
    if not API_BASE_URL:
        send_reply_func("Error: API_BASE_URL not configured in api_config.py")
        return

    text = text.strip()

    # ── /train ───────────────────────────────────────────────
    if text.lower().startswith("/train "):
        corpus_raw = text[7:].strip()
        if not corpus_raw:
            send_reply_func("Send text after /train to train your AI.")
            return

        corpus_lines = [l.strip() for l in corpus_raw.splitlines() if l.strip()]
        payload = {"ai_name": ai_name, "corpus": corpus_lines}

        try:
            response = requests.post(
                API_BASE_URL + ROUTES["train"],
                json=payload,
                headers=_build_headers(),
                timeout=300,
                verify=False,
            )
            if response.status_code == 200:
                result = response.json()
                with _channel_lock:
                    _channel_states[ai_name] = {"upload_id": None, "weights_sent": False}
                loss = result.get("loss_final", "N/A")
                send_reply_func(f"Training of {ai_name} complete.\nFinal loss: {loss}")
            elif response.status_code == 401:
                send_reply_func("Invalid token. Check API_KEY in api_config.py")
            elif response.status_code == 429:
                send_reply_func(response.json().get("detail", "Quota exceeded."))
            else:
                send_reply_func(f"Training error ({response.status_code}).")
        except requests.exceptions.ConnectionError:
            send_reply_func("Cannot reach the server. Ngrok URL expired?")
        except requests.exceptions.Timeout:
            send_reply_func("Timeout: training is taking too long.")
        except Exception as e:
            send_reply_func(f"Error: {e}")

    # ── /finetuning ──────────────────────────────────────────
    elif text.lower().startswith("/finetuning "):
        data = text[12:].strip()
        if not data:
            send_reply_func(
                "Send data after /finetuning.\n"
                "Format:\ninput : your question\nreply : expected answer"
            )
            return

        if "input :" not in data or "reply :" not in data:
            send_reply_func(
                "Invalid format. Use:\n"
                "input : your question\n"
                "reply : expected answer"
            )
            return

        state = _get_channel_state(ai_name)

        if not state["weights_sent"]:
            uid = _do_upload(ai_name)
            if uid is None:
                send_reply_func(
                    f"Model not found for '{ai_name}'.\n"
                    "Train first with /train <text>."
                )
                return
            state["upload_id"] = uid

        payload = {
            "ai_name":   ai_name,
            "upload_id": state["upload_id"],
            "corpus":    [data.strip()],
        }

        try:
            response = requests.post(
                API_BASE_URL + ROUTES["finetune"],
                json=payload,
                headers=_build_headers(),
                timeout=300,
                verify=False,
            )
            if response.status_code == 200:
                with _channel_lock:
                    _channel_states[ai_name] = {"upload_id": None, "weights_sent": False}
                send_reply_func(f"Fine-tuning of {ai_name} complete.")
            elif response.status_code == 401:
                send_reply_func("Invalid token. Check API_KEY in api_config.py")
            elif response.status_code == 429:
                send_reply_func(response.json().get("detail", "Quota exceeded."))
            else:
                with _channel_lock:
                    _channel_states[ai_name] = {"upload_id": None, "weights_sent": False}
                send_reply_func(f"Fine-tuning error ({response.status_code}). Please retry.")
        except requests.exceptions.ConnectionError:
            send_reply_func("Cannot reach the server. Ngrok URL expired?")
        except requests.exceptions.Timeout:
            send_reply_func("Timeout: fine-tuning is taking too long.")
        except Exception as e:
            send_reply_func(f"Error: {e}")

    # ── Inférence — COPIE EXACTE DE INFER.PY ─────────────────
    else:
        state = _get_channel_state(ai_name)

        # Premier appel ou cache expiré : upload du modèle
        if not state["weights_sent"]:
            try:
                upload_id = _do_upload(ai_name)
                if upload_id is None:
                    send_reply_func(
                        f"Model not found for '{ai_name}'.\n"
                        "Train first with /train <text>."
                    )
                    return
                state["upload_id"] = upload_id
            except Exception as e:
                send_reply_func(f"Upload error: {e}")
                return

        payload = {
            "ai_name": ai_name,
            "prompt":  text,
        }

        if not state["weights_sent"]:
            payload["upload_id"] = state["upload_id"]

        try:
            response = requests.post(
                API_BASE_URL + ROUTES["infer"],
                json=payload,
                headers=_build_headers(),
                timeout=60,
                verify=False,
            )

            # Cache expiré côté serveur → ré-uploader
            if response.status_code == 400:
                state["weights_sent"] = False
                try:
                    upload_id = _do_upload(ai_name)
                    if upload_id is None:
                        send_reply_func("Model upload failed. Please retry.")
                        return
                    state["upload_id"] = upload_id
                except Exception as e:
                    send_reply_func(f"Upload error: {e}")
                    return

                payload["upload_id"] = state["upload_id"]
                response = requests.post(
                    API_BASE_URL + ROUTES["infer"],
                    json=payload,
                    headers=_build_headers(),
                    timeout=60,
                    verify=False,
                )

            if response.status_code == 200:
                state["weights_sent"] = True
                send_reply_func(response.json().get("reply", "..."))
            elif response.status_code == 401:
                send_reply_func("Invalid token. Check API_KEY in api_config.py")
            elif response.status_code == 429:
                send_reply_func(response.json().get("detail", "Quota exceeded."))
            else:
                send_reply_func(f"Inference error ({response.status_code}).")

        except requests.exceptions.ConnectionError:
            send_reply_func("Cannot reach the server. Ngrok URL expired?")
        except requests.exceptions.Timeout:
            send_reply_func("Timeout: the AI is taking too long to respond.")
        except Exception as e:
            send_reply_func(f"Error: {e}")


# ──────────────────────────────────────────────────────────────
# CANAL TELEGRAM
# ──────────────────────────────────────────────────────────────

def start_telegram(token, ai_name):
    try:
        import telebot
    except ImportError:
        print_error("Module 'pyTelegramBotAPI' missing. Run: pip install pyTelegramBotAPI")
        return

    bot = telebot.TeleBot(token)
    print_success(f"Telegram active for {ai_name}.")

    @bot.message_handler(func=lambda message: True)
    def handle(message):
        route_message(message.text, ai_name, lambda t: bot.reply_to(message, t))

    bot.infinity_polling()


# ──────────────────────────────────────────────────────────────
# CANAL DISCORD
# ──────────────────────────────────────────────────────────────

def start_discord(token, ai_name):
    try:
        import discord
    except ImportError:
        print_error("Module 'discord.py' missing. Run: pip install discord.py")
        return

    import asyncio

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print_success(f"Discord active for {ai_name} ({client.user}).")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        def send_reply(text):
            asyncio.run_coroutine_threadsafe(
                message.channel.send(text), client.loop
            )

        threading.Thread(
            target=route_message,
            args=(message.content, ai_name, send_reply),
            daemon=True
        ).start()

    client.run(token)


# ──────────────────────────────────────────────────────────────
# CANAL WHATSAPP
# ──────────────────────────────────────────────────────────────

def start_whatsapp(account_sid, auth_token, number, ai_name):
    try:
        from flask import Flask, request
        from twilio.twiml.messaging_response import MessagingResponse
        from twilio.rest import Client as TwilioClient
    except ImportError:
        print_error("Missing modules. Run: pip install twilio flask")
        return

    app_flask = Flask(__name__)
    twilio_client = TwilioClient(account_sid, auth_token)

    @app_flask.route("/whatsapp", methods=["POST"])
    def whatsapp_webhook():
        incoming_msg = request.form.get("Body", "").strip()
        response = MessagingResponse()
        msg = response.message()
        route_message(incoming_msg, ai_name, lambda t: msg.body(t))
        return str(response)

    print_success(f"WhatsApp active for {ai_name} on port 5000.")
    print_atlas("Expose this port with: ngrok http 5000")
    app_flask.run(port=5000)


# ──────────────────────────────────────────────────────────────
# DÉMARRAGE DE TOUS LES CANAUX
# ──────────────────────────────────────────────────────────────

def start_channels(config):
    ai_name = config.get("ai_name")
    channels = config.get("channels", {})

    if not channels:
        print_atlas("No channel configured. Terminal conversation only.")
        return

    threads = []

    if "telegram" in channels:
        token = channels["telegram"].get("token")
        if token:
            t = threading.Thread(
                target=start_telegram, args=(token, ai_name), daemon=True
            )
            threads.append(t)
            t.start()

    if "discord" in channels:
        token = channels["discord"].get("token")
        if token:
            t = threading.Thread(
                target=start_discord, args=(token, ai_name), daemon=True
            )
            threads.append(t)
            t.start()

    if "whatsapp" in channels:
        wa = channels["whatsapp"]
        sid = wa.get("account_sid")
        tok = wa.get("auth_token")
        num = wa.get("number")
        if sid and tok and num:
            t = threading.Thread(
                target=start_whatsapp,
                args=(sid, tok, num, ai_name),
                daemon=True,
            )
            threads.append(t)
            t.start()

    return threads


# ──────────────────────────────────────────────────────────────
# CONFIGURATION GUIDÉE DES CANAUX
# ──────────────────────────────────────────────────────────────

def configure_channels(lang="en"):
    from utils import print_info_block
    L = CHANNEL_UI[lang]
    channels = {}

    print_section(L["section_title"])
    print_info_block(L["intro"])

    print_section(L["tg_section"])
    print_info_block(L["tg_steps"])
    tg_token = ask(L["tg_prompt"]).strip()
    if tg_token and tg_token.lower() not in ("no", "non", ""):
        channels["telegram"] = {"token": tg_token}
        print_success(L["tg_ok"])

    print_section(L["wa_section"])
    print_info_block(L["wa_steps"])
    wa_sid = ask(L["wa_sid_prompt"]).strip()
    if wa_sid and wa_sid.lower() not in ("no", "non", ""):
        wa_token = ask(L["wa_token_prompt"]).strip()
        wa_number = ask(L["wa_number_prompt"]).strip()
        channels["whatsapp"] = {
            "account_sid": wa_sid,
            "auth_token": wa_token,
            "number": wa_number,
        }
        print_success(L["wa_ok"])

    print_section(L["dc_section"])
    print_info_block(L["dc_steps"])
    dc_token = ask(L["dc_prompt"]).strip()
    if dc_token and dc_token.lower() not in ("no", "non", ""):
        channels["discord"] = {"token": dc_token}
        print_success(L["dc_ok"])

    if not channels:
        print_atlas(L["no_channels"])

    return channels