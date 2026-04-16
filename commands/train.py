import os
import time
import requests
import urllib3
from api_config import API_BASE_URL, API_KEY, ROUTES
from config import load_config, get_model_path
from utils import print_atlas, print_error, print_success
from commands.transfer import download_model

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Intervalle entre deux polls du job (secondes)
POLL_INTERVAL = 5


def _build_headers() -> dict:
    return {
        "Authorization":              f"Bearer {API_KEY}",
        "ngrok-skip-browser-warning": "true",
        "Content-Type":               "application/json",
    }


def _poll_job(job_id: str, label: str = "Entraînement") -> dict:
    """
    Attend la fin d'un job asynchrone côté serveur.
    Poll GET /job/{job_id} toutes les POLL_INTERVAL secondes.
    Retourne le dict 'result' quand status == 'done'.
    Lève une exception si status == 'error'.
    """
    url      = API_BASE_URL.rstrip("/") + f"/job/{job_id}"
    headers  = _build_headers()
    elapsed  = 0
    dots     = 0

    while True:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        dots    += 1

        try:
            resp = requests.get(url, headers=headers, timeout=30, verify=False)
        except requests.exceptions.Timeout:
            print_atlas(f"  ({elapsed}s) Poll timeout — nouvelle tentative...")
            continue
        except requests.exceptions.ConnectionError:
            print_error(
                "Connexion perdue pendant le polling.\n"
                "  → Vérifiez que ngrok est toujours actif."
            )
            raise

        if resp.status_code == 200:
            data   = resp.json()
            status = data.get("status")

            if status in ("pending", "running"):
                spinner = "." * (dots % 4 + 1)
                print_atlas(f"  {label} en cours{spinner} ({elapsed}s)")
                continue

            if status == "done":
                return data["result"]

        elif resp.status_code == 404:
            raise RuntimeError(f"job_id introuvable : {job_id}")
        else:
            # Le serveur a renvoyé l'erreur HTTP du job (ex. 429, 500)
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise RuntimeError(f"Erreur job ({resp.status_code}) : {detail}")


def run_train(data_path: str):
    config = load_config()

    if not config:
        print_error("Aucune IA configurée. Lancez d'abord : python atlas.py")
        return

    if not os.path.exists(data_path):
        print_error(f"Fichier introuvable : {data_path}")
        return

    if not API_BASE_URL:
        print_error("API_BASE_URL non configurée dans api_config.py")
        return

    if not API_KEY:
        print_error("API_KEY non configurée dans api_config.py")
        return

    ai_name    = config.get("ai_name")
    model_path = get_model_path(ai_name)
    api_url    = API_BASE_URL.rstrip("/") + ROUTES["train"]

    print_atlas(f"Démarrage de l'entraînement de {ai_name}...")
    print_atlas(f"Corpus  : {data_path}")
    print_atlas(f"Serveur : {api_url}")

    with open(data_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    if not raw_content.strip():
        print_error("Le fichier corpus est vide.")
        return

    corpus_lines = [line.strip() for line in raw_content.splitlines() if line.strip()]

    payload = {
        "ai_name":   ai_name,
        "corpus":    corpus_lines,
        "dimension": config.get("dimensions", 64),
        "epochs":    config.get("epochs", 100),
    }

    try:
        # ── Étape 1 : soumettre le job (retour immédiat) ──────────
        response = requests.post(
            api_url,
            json=payload,
            headers=_build_headers(),
            timeout=30,
            verify=False,
        )

        if response.status_code == 422:
            print_error(f"Données invalides (422) : {response.text}")
            return
        elif response.status_code == 401:
            print_error("Token refusé (401). Vérifiez que API_KEY == API_SECRET_KEY dans server.py")
            return
        elif response.status_code == 429:
            print_error(response.json().get("detail", "Quota journalier dépassé."))
            return
        elif response.status_code != 200:
            print_error(f"Erreur API ({response.status_code}) : {response.text}")
            return

        job_data = response.json()
        job_id   = job_data.get("job_id")

        if not job_id:
            print_error("Réponse serveur invalide : pas de job_id.")
            return

        print_atlas(f"Job soumis (id={job_id[:8]}…). En attente des résultats...")

        # ── Étape 2 : poll jusqu'à completion ─────────────────────
        result = _poll_job(job_id, label="Entraînement")

        # ── Étape 3 : télécharger le modèle chunk par chunk ───────
        download_id  = result.get("download_id")
        total_chunks = result.get("total_chunks", 0)

        if download_id and total_chunks > 0:
            try:
                raw_bytes = download_model(
                    download_id  = download_id,
                    total_chunks = total_chunks,
                    api_base_url = API_BASE_URL,
                    headers      = _build_headers(),
                    print_fn     = print_atlas,
                )
                os.makedirs(model_path, exist_ok=True)
                model_file = os.path.join(model_path, f"{ai_name}.bin")
                with open(model_file, "wb") as f:
                    f.write(raw_bytes)
                print_success(f"Modèle sauvegardé : {model_file}")

            except Exception as e:
                print_error(f"Erreur lors de la réception du modèle : {e}")
                return
        else:
            print_error("Réponse serveur invalide : pas de download_id.")
            return

        print_success("Entraînement terminé avec succès.")
        print_atlas(f"  Vocab       : {result.get('vocab_size', 'N/A')} tokens")
        print_atlas(f"  Loss init   : {result.get('loss_initial', 'N/A')}")
        print_atlas(f"  Loss finale : {result.get('loss_final', 'N/A')}")
        print_atlas(f"  Réduction   : {result.get('loss_reduction_pct', 'N/A')}%")
        print_atlas(f"  Durée       : {result.get('duration_seconds', 'N/A')}s")
        print_atlas(f"  Quota rest. : {round(result.get('quota_remaining_seconds', 0) / 3600, 2)}h")

    except requests.exceptions.ConnectionError:
        print_error(
            "Impossible de joindre le serveur.\n"
            "  → Vérifiez API_BASE_URL dans api_config.py\n"
            "  → L'URL ngrok a peut-être changé ou le serveur est éteint."
        )
    except requests.exceptions.Timeout:
        print_error("Timeout lors de la soumission du job.")
    except RuntimeError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Erreur imprévue : {e}")