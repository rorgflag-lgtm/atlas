import os
import requests
import urllib3
from api_config import API_BASE_URL, API_KEY, ROUTES
from config import load_config, get_model_path
from utils import print_atlas, print_error, GOLD
from commands.channels import start_channels
from commands.transfer import upload_model

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _build_headers() -> dict:
    return {
        "Authorization":              f"Bearer {API_KEY}",
        "ngrok-skip-browser-warning": "true",
        "Content-Type":               "application/json",
    }


def _do_upload(model_file: str) -> str:
    """Upload le modèle par chunks, retourne l'upload_id."""
    return upload_model(
        model_file   = model_file,
        api_base_url = API_BASE_URL,
        headers      = _build_headers(),
        print_fn     = print_atlas,
    )


def run_infer(ai_name: str):
    config = load_config()

    if not config or config.get("ai_name") != ai_name:
        print_error(f"L'IA '{ai_name}' n'est pas configurée.")
        return

    if not API_BASE_URL:
        print_error("API_BASE_URL non configurée dans api_config.py")
        return

    if not API_KEY:
        print_error("API_KEY non configurée dans api_config.py")
        return

    model_path = get_model_path(ai_name)
    model_file = os.path.join(model_path, f"{ai_name}.bin")

    if not os.path.exists(model_file):
        print_error(f"Modèle introuvable pour '{ai_name}'.")
        print_atlas("Entraînez d'abord : python atlas.py /train <corpus>")
        return

    start_channels(config)

    api_url       = API_BASE_URL + ROUTES["infer"]
    _upload_id    = None      # sera rempli avant le 1er appel
    _weights_sent = False     # True quand le serveur a le modèle en cache

    print_atlas(f"{ai_name} est active.")
    print_atlas("Tapez 'exit' pour quitter.\n")

    def call_infer(user_input: str) -> str:
        nonlocal _upload_id, _weights_sent

        # ── Premier appel ou cache expiré : upload du modèle ──
        if not _weights_sent:
            try:
                _upload_id = _do_upload(model_file)
            except Exception as e:
                return f"[ERREUR UPLOAD] {e}"

        payload = {
            "ai_name": ai_name,
            "prompt":  user_input,
        }

        if not _weights_sent:
            payload["upload_id"] = _upload_id

        response = requests.post(
            api_url,
            json=payload,
            headers=_build_headers(),
            timeout=60,
            verify=False,
        )

        # Cache expiré côté serveur → ré-uploader les poids
        if response.status_code == 400:
            _weights_sent = False
            try:
                _upload_id = _do_upload(model_file)
            except Exception as e:
                return f"[ERREUR UPLOAD] {e}"

            payload["upload_id"] = _upload_id
            response = requests.post(
                api_url,
                json=payload,
                headers=_build_headers(),
                timeout=60,
                verify=False,
            )

        if response.status_code == 200:
            _weights_sent = True
            return response.json().get("reply", "...")
        elif response.status_code == 401:
            return "[ERREUR 401] Token invalide. Vérifiez API_KEY == API_SECRET_KEY"
        elif response.status_code == 429:
            return f"[QUOTA] {response.json().get('detail', 'Quota dépassé.')}"
        else:
            return f"[ERREUR {response.status_code}] {response.text}"

    while True:
        try:
            user_input = input(f"{GOLD}Vous : \033[0m").strip()
        except KeyboardInterrupt:
            print_atlas("\nSession terminée.")
            break

        if user_input.lower() in ["exit", "quit", "q"]:
            print_atlas("Session terminée.")
            break

        if not user_input:
            continue

        try:
            reply = call_infer(user_input)
            print(f"{GOLD}{ai_name} : \033[0m{reply}\n")
        except requests.exceptions.ConnectionError:
            print_error(
                "Connexion impossible.\n"
                "  → Vérifiez API_BASE_URL dans api_config.py\n"
                "  → L'URL ngrok a peut-être changé."
            )
        except requests.exceptions.Timeout:
            print_error("Timeout : l'IA met trop de temps à répondre.")
        except Exception as e:
            print_error(f"Erreur imprévue : {e}")