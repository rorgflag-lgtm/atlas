#!/usr/bin/env python3
# ================================================================
# ATLAS OS - Interface principale (CLI)
# ================================================================

import sys
import os
import base64
import gzip

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from installer import check_and_install
check_and_install()

import requests
import urllib3
# Supprime le warning SSL affiché quand verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from colorama import Fore, Style
from utils import (
    print_atlas, print_error, print_success, print_section,
    print_header, print_info_block, print_command_block,
    ask, ask_choice, GOLD, RESET, BOLD,
)
from config import (
    load_config, save_config, get_model_path,
    MAX_EPOCHS, DAILY_QUOTA_H, DIMENSIONS, MODELS_DIR, CONFIG_FILE,
)
from api_config import PRETRAINED_MODEL_URL, API_BASE_URL, API_KEY, ROUTES
from commands.train    import run_train
from commands.finetune import run_finetune
from commands.infer    import run_infer
from commands.channels import configure_channels


# ──────────────────────────────────────────────────────────────
# TEXTES MULTILINGUES
# ──────────────────────────────────────────────────────────────

UI = {
    "en": {
        # Langue
        "lang_section":        "LANGUAGE / LANGUE",
        "lang_prompt":         "Choose your language / Choisissez votre langue",
        "lang_choices":        ["English", "Français"],

        # Dépendances / header déjà gérés dans installer.py

        # Wizard
        "welcome_section":     "WELCOME TO ATLAS OS",
        "welcome_body": [
            "ATLAS is an operating system for AI, designed to",
            "democratize artificial intelligence and make it",
            "fully available locally, on your device.",
            "",
            "Your data stays on your device.",
            "",
            "Current limitations (will be lifted soon):",
            "",
            "    - Usage quota    : 4 h / day",
            "    - Max epochs     : 200 per training",
            "    - Dimensions     : 32D, 64D, 128D",
        ],
        "press_enter":         "Press Enter to continue or type 'no' to quit",
        "quit_word":           "no",
        "goodbye":             "See you soon.",

        # Nom IA
        "ai_name_section":     "YOUR AI NAME",
        "ai_name_body":        ["What name would you like to give your AI?"],
        "ai_name_prompt":      "AI name",
        "ai_name_empty":       "The name cannot be empty.",

        # Type de modèle
        "model_type_section":  "MODEL TYPE",
        "model_type_prompt":   "How would you like to start?",
        "model_type_choices":  [
            "Create an AI from scratch",
            "Start with the pre-trained mini AI  (recommended)",
        ],

        # Téléchargement
        "download_section":    "DOWNLOADING PRE-TRAINED MODEL",
        "download_body_tpl": [
            "The pre-trained mini AI has:",
            "",
            "    - More than 1,000,000 parameters",
            "    - 128 dimensions",
            "    - Natural conversation ability",
            "",
            "The model will be downloaded from the ATLAS server",
            "and installed as '{ai_name}.bin'.",
        ],
        "download_connecting":  "Connecting to ATLAS server...",
        "download_detected":    "Model detected",
        "download_chunks":      "chunk(s) to download",
        "download_progress":    "Downloading",
        "download_assembling":  "Assembling model...",
        "download_saved":       "Model saved",
        "download_failed":      "Download failed. Switching to scratch mode.",
        "download_server_url":  "Downloading from",
        "download_refused":     "Server refused the request",
        "download_unreachable": "Cannot reach the server",
        "download_chunk_err":   "Error on chunk",
        "download_assemble_err":"Error during assembly",

        # Dimensions
        "dim_section":         "MODEL DIMENSIONS",
        "dim_body": [
            "More dimensions = more learning capacity.",
            "",
            "Available dimensions: 32D, 64D, 128D",
            "",
            "More dimensions will be available in future updates.",
        ],
        "dim_prompt":          "Choose the number of dimensions:",

        # Coût
        "cost_section":        "COST INFORMATION",
        "cost_body_tpl": [
            "No training or inference cost.",
            "",
            "A usage quota of {quota}h per day applies.",
        ],

        # Époques
        "epochs_section":      "NUMBER OF TRAINING EPOCHS",
        "epochs_body_tpl": [
            "Set the number of epochs (1 to {max}).",
            "",
            "Tips:",
            "",
            "    Too many epochs  ->  deterministic model (less creative)",
            "    Too few          ->  model may hallucinate",
            "    This number also depends on the amount of training data",
        ],
        "epochs_prompt_tpl":   "Number of epochs  (1 - {max})",
        "epochs_err_range":    "Enter a value between 1 and {max}.",
        "epochs_err_int":      "Enter a valid integer.",

        # Canaux
        "channels_section":    "COMMUNICATION CHANNELS",
        "channels_body": [
            "Connect a channel to control your AI remotely.",
            "",
            "From the channel you can:",
            "",
            "    - Chat with your AI",
            "    - Train it      :  /train <text>",
            "    - Fine-tune it  :  /finetuning input : ...  reply : ...",
            "",
            "Available channels: Telegram, WhatsApp, Discord",
            "",
            "More channels will be available in future updates.",
        ],
        "channels_connect":    "Connect a channel?  (yes / no)",
        "channels_yes":        ["yes", "y", "oui", "o"],

        # Fin de config
        "config_done_section": "CONFIGURATION COMPLETE",
        "config_done_tpl": [
            "Your AI '{ai_name}' is configured and ready.",
            "",
            "To launch your AI, type in your terminal:",
            "",
            "    python atlas.py init {ai_name}",
        ],

        # Statut
        "status_section":      "YOUR AI STATUS",
        "status_not_trained":  "(model not trained)",
        "status_finetuned":    "  (fine-tuned)",
        "status_fields": {
            "ai_name":    "AI Name          :",
            "model_type": "Model type       :",
            "dimensions": "Dimensions       :",
            "epochs":     "Epochs           :",
            "params":     "Parameters       :",
            "size":       "Model size       :",
            "vocab":      "Vocabulary       :",
            "quota":      "Daily quota      :",
            "channels":   "Active channels  :",
            "storage":    "Storage          :",
            "terminal":   "Terminal only",
        },

        # Commandes
        "commands_section":    "AVAILABLE COMMANDS",
        "cmd_init":            "Launch the AI and chat in the terminal",
        "cmd_train":           "Train the AI with a raw text corpus",
        "cmd_finetune":        "Fine-tune the AI  (input / reply format)",
        "cmd_status":          "Show this menu",
        "cmd_reset":           "Fully reconfigure the AI",

        # Corpus
        "corpus_section":      "CORPUS FORMAT",
        "corpus_train": [
            "Training  (/train)  —  Raw text:",
            "",
            "    Any continuous text is accepted.",
            "    Ex: The sky is blue. AI transforms the world.",
        ],
        "corpus_finetune": [
            "Fine-tuning  (/finetuning)  —  Structured format:",
            "",
            "    input : Hello, how are you?",
            "    reply : I am doing very well, thank you!",
            "",
            "    input : What is your role?",
            "    reply : I am an AI created with ATLAS.",
        ],

        # Canaux distants
        "remote_section":      "USAGE FROM YOUR CHANNELS",
        "remote_body": [
            "From Telegram, WhatsApp or Discord:",
            "",
            "    normal message              ->  Chat with the AI",
            "    /train <your text>          ->  Train the AI remotely",
            "    /finetuning input : ...     ->  Fine-tune the AI remotely",
        ],

        # Reset
        "reset_section":       "RESET",
        "reset_confirm":       "Confirm reset?  (yes / no)",
        "reset_yes":           ["yes", "y", "oui", "o"],
        "reset_deleted":       "Configuration deleted.",
        "reset_cancelled":     "Reset cancelled.",

        # Erreurs commandes
        "err_no_config":       "No AI configured. Run: python atlas.py",
        "err_usage_init":      "Usage: python atlas.py init <ai_name>",
        "err_usage_train":     "Usage: python atlas.py /train <corpus_file_path>",
        "err_corpus_hint":     "The corpus must be a plain text file (.txt)",
        "err_usage_finetune":  "Usage: python atlas.py /finetuning <file_path>",
        "err_finetune_fmt": [
            "Required format in the file:",
            "",
            "    input : your question",
            "    reply : the expected answer",
        ],
        "err_unknown_cmd":     "Unknown command: '{cmd}'",
        "err_available_cmds": [
            "Available commands:",
            "",
            "    init          ->  Launch the AI",
            "    /train        ->  Train the AI",
            "    /finetuning   ->  Fine-tune the AI",
            "    status        ->  Show status",
            "    reset         ->  Reconfigure",
        ],
    },

    # ── FRANÇAIS ────────────────────────────────────────────────
    "fr": {
        "lang_section":        "LANGUE / LANGUAGE",
        "lang_prompt":         "Choisissez votre langue / Choose your language",
        "lang_choices":        ["Français", "English"],

        "welcome_section":     "BIENVENUE DANS ATLAS OS",
        "welcome_body": [
            "ATLAS est un système d'exploitation pour IA conçu pour",
            "démocratiser l'intelligence artificielle et la rendre",
            "entièrement disponible en local, sur votre appareil.",
            "",
            "Vos données restent sur votre appareil.",
            "",
            "Limitations actuelles (seront levées prochainement) :",
            "",
            "    - Quota d'utilisation : 4h / jour",
            "    - Nombre d'époques    : 200 max/entraînement",
            "    - Dimensions          : 32D, 64D, 128D",
        ],
        "press_enter":         "Appuyez sur Entrée pour continuer ou tapez 'non' pour quitter",
        "quit_word":           "non",
        "goodbye":             "À bientôt.",

        "ai_name_section":     "NOM DE VOTRE IA",
        "ai_name_body":        ["Quel nom souhaitez-vous donner à votre IA ?"],
        "ai_name_prompt":      "Nom de l'IA",
        "ai_name_empty":       "Le nom ne peut pas être vide.",

        "model_type_section":  "TYPE DE MODÈLE",
        "model_type_prompt":   "Comment voulez-vous démarrer ?",
        "model_type_choices":  [
            "Créer une IA de zéro",
            "Démarrer avec la mini IA pré-entraînée  (recommandé)",
        ],

        "download_section":    "TÉLÉCHARGEMENT DU MODÈLE PRÉ-ENTRAÎNÉ",
        "download_body_tpl": [
            "La mini IA pré-entraînée possède :",
            "",
            "    - Plus de 1 000 000 de paramètres",
            "    - 128 dimensions",
            "    - Capacité de conversation naturelle",
            "",
            "Le modèle sera téléchargé depuis le serveur ATLAS",
            "et installé sous le nom '{ai_name}.bin'.",
        ],
        "download_connecting":  "Connexion au serveur ATLAS…",
        "download_detected":    "Modèle détecté",
        "download_chunks":      "chunk(s) à télécharger",
        "download_progress":    "Téléchargement",
        "download_assembling":  "Assemblage du modèle…",
        "download_saved":       "Modèle sauvegardé",
        "download_failed":      "Téléchargement échoué. Passage en mode création de zéro.",
        "download_server_url":  "Téléchargement depuis",
        "download_refused":     "Le serveur a refusé la demande",
        "download_unreachable": "Impossible de joindre le serveur",
        "download_chunk_err":   "Erreur chunk",
        "download_assemble_err":"Erreur lors de l'assemblage",

        "dim_section":         "DIMENSIONS DU MODÈLE",
        "dim_body": [
            "Plus de dimensions = plus de capacité d'apprentissage.",
            "",
            "Dimensions disponibles : 32D, 64D, 128D",
            "",
            "Plus de dimensions seront disponibles dans les prochaines mises à jour.",
        ],
        "dim_prompt":          "Choisissez le nombre de dimensions :",

        "cost_section":        "INFORMATION SUR LES COÛTS",
        "cost_body_tpl": [
            "Aucun coût d'entraînement ni d'inférence.",
            "",
            "Un quota d'utilisation de {quota}h par jour s'applique.",
        ],

        "epochs_section":      "NOMBRE D'ÉPOQUES D'ENTRAÎNEMENT",
        "epochs_body_tpl": [
            "Définissez le nombre d'époques (1 à {max}).",
            "",
            "Conseils :",
            "",
            "    Trop d'époques   ->  modèle déterministe (peu créatif)",
            "    Trop peu         ->  modèle peut divaguer",
            "    Ce nombre dépend aussi de la quantité de données d'entraînement",
        ],
        "epochs_prompt_tpl":   "Nombre d'époques  (1 - {max})",
        "epochs_err_range":    "Entrez une valeur entre 1 et {max}.",
        "epochs_err_int":      "Entrez un nombre entier valide.",

        "channels_section":    "CANAUX DE COMMUNICATION",
        "channels_body": [
            "Connectez un canal pour contrôler votre IA à distance.",
            "",
            "Depuis le canal vous pourrez :",
            "",
            "    - Converser avec votre IA",
            "    - L'entraîner   :  /train <texte>",
            "    - La fine-tuner :  /finetuning input : ...  reply : ...",
            "",
            "Canaux disponibles : Telegram, WhatsApp, Discord",
            "",
            "Plus de canaux seront disponibles dans les prochaines mises à jour.",
        ],
        "channels_connect":    "Connecter un canal ?  (oui / non)",
        "channels_yes":        ["oui", "o", "yes", "y"],

        "config_done_section": "CONFIGURATION TERMINÉE",
        "config_done_tpl": [
            "Votre IA '{ai_name}' est configurée et prête.",
            "",
            "Pour lancer votre IA, tapez dans votre terminal :",
            "",
            "    python atlas.py init {ai_name}",
        ],

        "status_section":      "STATUT DE VOTRE IA",
        "status_not_trained":  "(modèle non entraîné)",
        "status_finetuned":    "  (fine-tuné)",
        "status_fields": {
            "ai_name":    "Nom de l'IA       :",
            "model_type": "Type de modèle    :",
            "dimensions": "Dimensions        :",
            "epochs":     "Époques           :",
            "params":     "Paramètres        :",
            "size":       "Taille du modèle  :",
            "vocab":      "Vocabulaire       :",
            "quota":      "Quota journalier  :",
            "channels":   "Canaux actifs     :",
            "storage":    "Stockage          :",
            "terminal":   "Terminal uniquement",
        },

        "commands_section":    "COMMANDES DISPONIBLES",
        "cmd_init":            "Lancer l'IA et converser dans le terminal",
        "cmd_train":           "Entraîner l'IA avec un corpus texte brut",
        "cmd_finetune":        "Fine-tuner l'IA  (format  input / reply)",
        "cmd_status":          "Afficher ce menu",
        "cmd_reset":           "Reconfigurer entièrement l'IA",

        "corpus_section":      "FORMAT DES CORPUS",
        "corpus_train": [
            "Entraînement  (/train)  —  Texte brut :",
            "",
            "    Tout texte continu est accepté.",
            "    Ex : Le ciel est bleu. L'IA transforme le monde.",
        ],
        "corpus_finetune": [
            "Fine-tuning  (/finetuning)  —  Format structuré :",
            "",
            "    input : Bonjour, comment vas-tu ?",
            "    reply : Je vais très bien, merci !",
            "",
            "    input : Quel est ton rôle ?",
            "    reply : Je suis une IA créée avec ATLAS.",
        ],

        "remote_section":      "UTILISATION DEPUIS VOS CANAUX",
        "remote_body": [
            "Depuis Telegram, WhatsApp ou Discord :",
            "",
            "    message normal              ->  Conversation avec l'IA",
            "    /train <votre texte>        ->  Entraîner l'IA à distance",
            "    /finetuning input : ...     ->  Fine-tuner l'IA à distance",
        ],

        "reset_section":       "RÉINITIALISATION",
        "reset_confirm":       "Confirmer la réinitialisation ?  (oui / non)",
        "reset_yes":           ["oui", "o", "yes", "y"],
        "reset_deleted":       "Configuration supprimée.",
        "reset_cancelled":     "Réinitialisation annulée.",

        "err_no_config":       "Aucune IA configurée. Lancez : python atlas.py",
        "err_usage_init":      "Usage : python atlas.py init <nom_ia>",
        "err_usage_train":     "Usage : python atlas.py /train <chemin_fichier_corpus>",
        "err_corpus_hint":     "Le corpus doit être un fichier texte brut (.txt)",
        "err_usage_finetune":  "Usage : python atlas.py /finetuning <chemin_fichier>",
        "err_finetune_fmt": [
            "Format requis dans le fichier :",
            "",
            "    input : votre question",
            "    reply : la réponse attendue",
        ],
        "err_unknown_cmd":     "Commande inconnue : '{cmd}'",
        "err_available_cmds": [
            "Commandes disponibles :",
            "",
            "    init          ->  Lancer l'IA",
            "    /train        ->  Entraîner l'IA",
            "    /finetuning   ->  Fine-tuner l'IA",
            "    status        ->  Voir le statut",
            "    reset         ->  Reconfigurer",
        ],
    },
}


def _L(config: dict, key: str):
    """Raccourci : retourne le texte dans la langue configurée."""
    lang = config.get("lang", "en")
    return UI[lang][key]


# ──────────────────────────────────────────────────────────────
# SÉLECTION DE LANGUE (première étape, avant tout)
# ──────────────────────────────────────────────────────────────

def choose_language(config: dict) -> dict:
    """
    Affiche un choix de langue si aucune langue n'est encore sauvegardée.
    Retourne le config mis à jour.
    """
    if "lang" in config:
        return config

    # On affiche en bilingue pour ce seul écran
    print_section("LANGUAGE / LANGUE")
    choice = ask_choice(
        "Choose your language / Choisissez votre langue",
        ["English", "Français"],
    )
    config["lang"] = "fr" if choice == "Français" else "en"
    save_config(config)
    return config


# ──────────────────────────────────────────────────────────────
# INFORMATIONS DU MODÈLE
# ──────────────────────────────────────────────────────────────

def get_model_info(ai_name: str) -> dict | None:
    try:
        import torch

        model_path = get_model_path(ai_name)
        candidates = [
            os.path.join(model_path, f"{ai_name}.bin"),
            os.path.join(MODELS_DIR, f"{ai_name}.bin"),
        ]

        if os.path.isdir(model_path):
            for fname in os.listdir(model_path):
                if fname.endswith(".bin"):
                    full = os.path.join(model_path, fname)
                    if full not in candidates:
                        candidates.append(full)

        model_file = next((p for p in candidates if os.path.exists(p)), None)
        if model_file is None:
            return None

        size_bytes = os.path.getsize(model_file)
        data       = torch.load(model_file, map_location="cpu", weights_only=False)
        param_count = sum(t.numel() for t in data["state_dict"].values())

        return {
            "param_count":  param_count,
            "size_bytes":   size_bytes,
            "dimensions":   data.get("d", "?"),
            "vocab_size":   data.get("vocab_size", "?"),
            "is_finetuned": data.get("is_finetuned", False),
        }

    except Exception:
        return None


def _fmt_params(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _fmt_size(n: int) -> str:
    if n >= 1_048_576:
        return f"{n / 1_048_576:.2f} Mo"
    return f"{n / 1024:.1f} Ko"


# ──────────────────────────────────────────────────────────────
# TÉLÉCHARGEMENT DU MODÈLE PRÉ-ENTRAÎNÉ
# ──────────────────────────────────────────────────────────────

def _download_pretrained_model(dest_path: str, lang: str) -> bool:
    L       = UI[lang]
    headers = {"Authorization": f"Bearer {API_KEY}"}

    # verify=False : contourne l'erreur SSL "certificate is not yet valid"
    # qui apparaît avec les tunnels ngrok à cause du décalage d'horloge
    # entre le moment d'émission du certificat et l'heure locale du client.
    SSL_VERIFY = False

    try:
        print_atlas(L["download_connecting"])
        resp = requests.get(
            PRETRAINED_MODEL_URL,
            headers=headers,
            timeout=60,
            verify=SSL_VERIFY,
        )
        if resp.status_code != 200:
            print_error(
                f"{L['download_refused']} ({resp.status_code}) : {resp.text[:200]}"
            )
            return False

        info         = resp.json()
        transfer_id  = info["transfer_id"]
        total_chunks = info["total_chunks"]
        size_bytes   = info.get("size_bytes", 0)

        print_atlas(
            f"{L['download_detected']} : {_fmt_size(size_bytes)}  "
            f"({total_chunks} {L['download_chunks']})"
        )

    except Exception as e:
        print_error(f"{L['download_unreachable']} : {e}")
        return False

    chunk_base_url = f"{API_BASE_URL}{ROUTES['download_chunk']}/{transfer_id}"
    b64_parts      = []

    for idx in range(total_chunks):
        try:
            r = requests.get(
                f"{chunk_base_url}/{idx}",
                headers=headers,
                timeout=120,
                verify=SSL_VERIFY,
            )
            if r.status_code != 200:
                print_error(
                    f"{L['download_chunk_err']} {idx}/{total_chunks - 1} "
                    f"({r.status_code}) : {r.text[:100]}"
                )
                return False

            b64_parts.append(r.json()["data"])
            pct = int((idx + 1) / total_chunks * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(
                f"\r  {L['download_progress']}  [{bar}] {pct:3d}%  "
                f"({idx + 1}/{total_chunks})",
                end="", flush=True,
            )

        except Exception as e:
            print()
            print_error(f"{L['download_chunk_err']} {idx} : {e}")
            return False

    print()

    try:
        print_atlas(L["download_assembling"])
        b64_full   = "".join(b64_parts)
        compressed = base64.b64decode(b64_full.encode("utf-8"))
        raw        = gzip.decompress(compressed)

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(raw)

        print_success(f"{L['download_saved']} : {dest_path}  ({_fmt_size(len(raw))})")
        return True

    except Exception as e:
        print_error(f"{L['download_assemble_err']} : {e}")
        return False


# ──────────────────────────────────────────────────────────────
# AFFICHAGE DU STATUT
# ──────────────────────────────────────────────────────────────

def show_status(config: dict):
    lang     = config.get("lang", "en")
    L        = UI[lang]
    F        = L["status_fields"]

    ai_name  = config.get("ai_name", "N/A")
    dims     = config.get("dimensions", "N/A")
    epochs   = config.get("epochs", "N/A")
    model_t  = config.get("model_type", "N/A")
    channels = config.get("channels", {})
    ch_list  = ", ".join(channels.keys()) if channels else F["terminal"]

    print_header()
    print_section(L["status_section"])

    model_info = get_model_info(ai_name)

    if model_info:
        ft_label   = L["status_finetuned"] if model_info["is_finetuned"] else ""
        param_line = f"{F['params']}  {_fmt_params(model_info['param_count'])}{ft_label}"
        size_line  = f"{F['size']}  {_fmt_size(model_info['size_bytes'])}"
        vocab_line = f"{F['vocab']}  {model_info['vocab_size']} tokens"
        dims_actual = model_info["dimensions"]
    else:
        nt = L["status_not_trained"]
        param_line  = f"{F['params']}  {nt}"
        size_line   = f"{F['size']}  {nt}"
        vocab_line  = f"{F['vocab']}  {nt}"
        dims_actual = dims

    print_info_block([
        f"{F['ai_name']}  {ai_name}",
        f"{F['model_type']}  {model_t}",
        f"{F['dimensions']}  {dims_actual}D",
        f"{F['epochs']}  {epochs}",
        "",
        param_line,
        size_line,
        vocab_line,
        "",
        f"{F['quota']}  {DAILY_QUOTA_H}h / jour",
        f"{F['channels']}  {ch_list}",
        f"{F['storage']}  {get_model_path(ai_name)}",
    ])

    print_section(L["commands_section"])
    print()
    print_command_block(f"python atlas.py init {ai_name}", L["cmd_init"])
    print_command_block("python atlas.py /train <fichier.txt>",    L["cmd_train"])
    print_command_block("python atlas.py /finetuning <fichier.txt>", L["cmd_finetune"])
    print_command_block("python atlas.py status", L["cmd_status"])
    print_command_block("python atlas.py reset",  L["cmd_reset"])

    print_section(L["corpus_section"])
    print_info_block(L["corpus_train"])
    print_info_block(L["corpus_finetune"])

    print_section(L["remote_section"])
    print_info_block(L["remote_body"])


# ──────────────────────────────────────────────────────────────
# ASSISTANT DE CONFIGURATION
# ──────────────────────────────────────────────────────────────

def setup_wizard(existing_config: dict = None):
    config = existing_config or {}

    # ── 0. Choix de langue (toujours en premier) ──────────────
    config = choose_language(config)
    lang   = config["lang"]
    L      = UI[lang]

    print_header()
    print_section(L["welcome_section"])
    print_info_block(L["welcome_body"])

    confirmation = ask(L["press_enter"])
    if confirmation.strip().lower() == L["quit_word"]:
        print_atlas(L["goodbye"])
        sys.exit(0)

    # ── 1. Nom de l'IA ────────────────────────────────────────
    print_section(L["ai_name_section"])
    print_info_block(L["ai_name_body"])

    while True:
        ai_name = ask(L["ai_name_prompt"]).strip()
        if ai_name:
            break
        print_error(L["ai_name_empty"])

    # ── 2. Type de modèle ─────────────────────────────────────
    print_section(L["model_type_section"])
    choice_model = ask_choice(L["model_type_prompt"], L["model_type_choices"])

    model_type = ""
    dimensions = 128
    epochs     = 50

    if L["model_type_choices"][1] in choice_model or "pre-trained" in choice_model.lower() or "pré-entraîn" in choice_model.lower():
        model_type = "pretrained"

        print_section(L["download_section"])
        body = [
            line.replace("{ai_name}", ai_name)
            for line in L["download_body_tpl"]
        ]
        print_info_block(body)
        print_atlas(f"{L['download_server_url']} : {PRETRAINED_MODEL_URL}")

        model_path = get_model_path(ai_name)
        model_file = os.path.join(model_path, f"{ai_name}.bin")

        success = _download_pretrained_model(model_file, lang)

        if success:
            dimensions = 128
        else:
            print_atlas(L["download_failed"])
            model_type = "scratch"

    if model_type != "pretrained":
        model_type = "scratch"

        # ── Dimensions ────────────────────────────────────────
        print_section(L["dim_section"])
        print_info_block(L["dim_body"])
        dim_choice = ask_choice(L["dim_prompt"], ["32", "64", "128"])
        dimensions = int(dim_choice)

        # ── Coût ──────────────────────────────────────────────
        print_section(L["cost_section"])
        cost_body = [
            line.replace("{quota}", str(DAILY_QUOTA_H))
            for line in L["cost_body_tpl"]
        ]
        print_info_block(cost_body)
        ask(L["press_enter"])

        # ── Époques ───────────────────────────────────────────
        print_section(L["epochs_section"])
        epochs_body = [
            line.replace("{max}", str(MAX_EPOCHS))
            for line in L["epochs_body_tpl"]
        ]
        print_info_block(epochs_body)

        while True:
            ep_input = ask(
                L["epochs_prompt_tpl"].replace("{max}", str(MAX_EPOCHS))
            ).strip()
            if ep_input.isdigit():
                ep_val = int(ep_input)
                if 1 <= ep_val <= MAX_EPOCHS:
                    epochs = ep_val
                    break
                else:
                    print_error(
                        L["epochs_err_range"].replace("{max}", str(MAX_EPOCHS))
                    )
            else:
                print_error(L["epochs_err_int"])

    # ── 3. Canaux ─────────────────────────────────────────────
    print_section(L["channels_section"])
    print_info_block(L["channels_body"])

    connect = ask(L["channels_connect"]).strip().lower()
    channels = {}
    if connect in L["channels_yes"]:
        channels = configure_channels(lang)

    # ── 4. Sauvegarde ─────────────────────────────────────────
    config.update({
        "ai_name":    ai_name,
        "model_type": model_type,
        "dimensions": dimensions,
        "epochs":     epochs,
        "channels":   channels,
    })
    save_config(config)

    # ── 5. Confirmation ───────────────────────────────────────
    print_section(L["config_done_section"])
    done_body = [
        line.replace("{ai_name}", ai_name)
        for line in L["config_done_tpl"]
    ]
    print_info_block(done_body)
    show_status(config)


# ──────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ──────────────────────────────────────────────────────────────

def main():
    args   = sys.argv[1:]
    config = load_config()

    # Si pas de langue encore choisie et pas de commande spéciale,
    # on laisse le wizard gérer le choix de langue.
    # Pour status/reset on s'assure qu'une langue existe.
    if config and "lang" not in config:
        config = choose_language(config)

    lang = config.get("lang", "en") if config else "en"
    L    = UI[lang]

    if not args:
        if not config:
            setup_wizard()
        else:
            show_status(config)
        return

    command = args[0].lower()

    if command == "init":
        if len(args) < 2:
            print_error(L["err_usage_init"])
            return
        run_infer(args[1])

    elif command == "/train":
        if len(args) < 2:
            print_error(L["err_usage_train"])
            print_atlas(L["err_corpus_hint"])
            return
        run_train(args[1])

    elif command == "/finetuning":
        if len(args) < 2:
            print_error(L["err_usage_finetune"])
            print_info_block(L["err_finetune_fmt"])
            return
        run_finetune(args[1])

    elif command == "status":
        if not config:
            print_error(L["err_no_config"])
        else:
            show_status(config)

    elif command == "reset":
        print_section(L["reset_section"])
        confirm = ask(L["reset_confirm"]).strip().lower()
        if confirm in L["reset_yes"]:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            print_success(L["reset_deleted"])
            setup_wizard()
        else:
            print_atlas(L["reset_cancelled"])

    else:
        print_error(L["err_unknown_cmd"].replace("{cmd}", args[0]))
        print_info_block(L["err_available_cmds"])


if __name__ == "__main__":
    main()