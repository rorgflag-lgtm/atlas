import os
import time
import requests
import urllib3
from api_config import API_BASE_URL, API_KEY, ROUTES
from config import load_config, get_model_path
from utils import print_atlas, print_error, print_success
from commands.transfer import upload_model, download_model

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Intervalle entre deux polls du job (secondes)
POLL_INTERVAL = 5


def _build_headers() -> dict:
    return {
        "Authorization":              f"Bearer {API_KEY}",
        "ngrok-skip-browser-warning": "true",
        "Content-Type":               "application/json",
    }


def _parse_finetune_corpus(raw: str) -> list:
    corpus  = []
    current = []

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            if current:
                corpus.append("\n".join(current))
                current = []
        else:
            current.append(line)

    if current:
        corpus.append("\n".join(current))

    valid = [
        bloc for bloc in corpus
        if "input :" in bloc and "reply :" in bloc
    ]
    return valid


def _poll_job(job_id: str, label: str = "Fine-tuning") -> dict:
    """
    Attend la fin d'un job asynchrone côté serveur.
    Poll GET /job/{job_id} toutes les POLL_INTERVAL secondes.
    Retourne le dict 'result' quand status == 'done'.
    Lève une exception si status == 'error'.
    """
    url     = API_BASE_URL.rstrip("/") + f"/job/{job_id}"
    headers = _build_headers()
    elapsed = 0
    dots    = 0

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
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise RuntimeError(f"Erreur job ({resp.status_code}) : {detail}")


def run_finetune(data_path: str):
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
    model_file = os.path.join(model_path, f"{ai_name}.bin")
    api_url    = API_BASE_URL.rstrip("/") + ROUTES["finetune"]

    if not os.path.exists(model_file):
        print_error(f"Modèle introuvable : {model_file}")
        print_atlas("Entraînez d'abord : python atlas.py /train <corpus>")
        return

    print_atlas(f"Démarrage du fine-tuning de {ai_name}...")
    print_atlas(f"Données  : {data_path}")
    print_atlas(f"Serveur  : {api_url}")

    with open(data_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    if "input :" not in raw_content or "reply :" not in raw_content:
        print_error("Format invalide. Utilisez :\n  input : question\n  reply : réponse")
        return

    corpus = _parse_finetune_corpus(raw_content)

    if not corpus:
        print_error("Aucune paire input/reply valide trouvée.")
        return

    print_atlas(f"Paires détectées : {len(corpus)}")

    # ── Étape 1 : upload du modèle local vers le serveur par chunks ──
    try:
        upload_id = upload_model(
            model_file   = model_file,
            api_base_url = API_BASE_URL,
            headers      = _build_headers(),
            print_fn     = print_atlas,
        )
    except Exception as e:
        print_error(f"Échec de l'upload du modèle : {e}")
        return

    # ── Étape 2 : soumettre le job fine-tuning (retour immédiat) ──
    payload = {
        "ai_name":   ai_name,
        "upload_id": upload_id,
        "corpus":    corpus,
        "epochs":    config.get("epochs", 50),
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=_build_headers(),
            timeout=30,
            verify=False,
        )

        if response.status_code == 401:
            print_error("Token refusé (401). Vérifiez que API_KEY == API_SECRET_KEY dans server.py")
            return
        elif response.status_code == 429:
            print_error(response.json().get("detail", "Quota journalier dépassé."))
            return
        elif response.status_code == 422:
            print_error(f"Données invalides (422) : {response.text}")
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

        # ── Étape 3 : poll jusqu'à completion ─────────────────────
        result = _poll_job(job_id, label="Fine-tuning")

        # ── Étape 4 : télécharger le modèle mis à jour chunk par chunk ──
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
                with open(model_file, "wb") as f:
                    f.write(raw_bytes)
                print_success(f"Modèle mis à jour : {model_file}")

            except Exception as e:
                print_error(f"Erreur lors de la réception du modèle : {e}")
                return
        else:
            print_error("Réponse serveur invalide : pas de download_id.")
            return

        print_success("Fine-tuning terminé avec succès.")
        if result.get("vocab_extended"):
            print_atlas("  ✓ Vocabulaire étendu avec de nouveaux tokens.")
        print_atlas(f"  Loss initiale : {result.get('loss_initial', 'N/A')}")
        print_atlas(f"  Loss finale   : {result.get('loss_final', 'N/A')}")
        print_atlas(f"  Réduction     : {result.get('loss_reduction_pct', 'N/A')}%")
        print_atlas(f"  Durée         : {result.get('duration_seconds', 'N/A')}s")
        print_atlas(f"  Quota restant : {round(result.get('quota_remaining_seconds', 0) / 3600, 2)}h")

    except requests.exceptions.ConnectionError:
        print_error(
            "Impossible de joindre le serveur.\n"
            "  → Vérifiez API_BASE_URL dans api_config.py\n"
            "  → L'URL ngrok a peut-être changé."
        )
    except requests.exceptions.Timeout:
        print_error("Timeout lors de la soumission du job.")
    except RuntimeError as e:
        print_error(str(e))
    except Exception as e:
        print_error(f"Erreur imprévue : {e}")