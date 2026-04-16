# ================================================================
# CONFIGURATION API ATLAS
# ================================================================

# L'URL fournie par Ngrok sur Google Colab (sans le slash final)
# Exemple : "https://xxxx-xx-xx-xxx-xx.ngrok-free.app"
API_BASE_URL = "https://adolfo-pointless-gilbert.ngrok-free.dev"  # ← Colle ton URL ngrok ici

# Ton Token de sécurité (doit être IDENTIQUE à API_SECRET_KEY dans server.py)
API_KEY = "7f3a1c2b9d4e5a6b8c"  # ← Colle ton token ici

# URL de téléchargement du modèle pré-entraîné
# Pointe vers la route /download_pretrained du serveur ATLAS
PRETRAINED_MODEL_URL = API_BASE_URL + "/download_pretrained"

# Routes de l'API
ROUTES = {
    "train":             "/train",
    "finetune":          "/fine_tuning",
    "infer":             "/infer",
    "upload_chunk":      "/upload_chunk",
    "download_chunk":    "/download_chunk",
    "pretrained":        "/download_pretrained",   # ← nouvelle route
}