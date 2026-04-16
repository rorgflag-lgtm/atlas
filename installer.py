# ============================================================
# ATLAS - Installateur automatique de dépendances
# ============================================================

import subprocess
import sys
import os

REQUIRED_PACKAGES = [
    ("colorama",  "colorama",         None),
    ("requests",  "requests",         None),
    ("telebot",   "pyTelegramBotAPI", None),
    ("discord",   "discord.py",       None),
    ("flask",     "flask",            None),
    ("twilio",    "twilio",           None),
    ("torch",     "torch",            None),
]

LABELS = {
    "fr": {
        "colorama":         "Couleurs dans le terminal Windows/Linux/Mac",
        "requests":         "Appels HTTP vers l'API ATLAS",
        "pyTelegramBotAPI": "Canal Telegram",
        "discord.py":       "Canal Discord",
        "flask":            "Serveur webhook WhatsApp",
        "twilio":           "Canal WhatsApp via Twilio",
        "torch":            "Moteur de calcul (PyTorch)",
        "checking":         "Vérification des dépendances ATLAS...",
        "installing":       "Installation en cours...",
        "installed":        "Installé avec succès.",
        "failed":           "Échec de l'installation.",
        "auto_installed":   "module(s) installé(s) automatiquement.",
        "manual":           "Modules non installés (à installer manuellement) :",
        "all_ok":           "Toutes les dépendances sont prêtes.",
        "unstable":         "Certains modules ont échoué. ATLAS peut être instable.",
    },
    "en": {
        "colorama":         "Terminal colors for Windows/Linux/Mac",
        "requests":         "HTTP calls to the ATLAS API",
        "pyTelegramBotAPI": "Telegram channel",
        "discord.py":       "Discord channel",
        "flask":            "WhatsApp webhook server",
        "twilio":           "WhatsApp channel via Twilio",
        "torch":            "Computation engine (PyTorch)",
        "checking":         "Checking ATLAS dependencies...",
        "installing":       "Installing...",
        "installed":        "Installed successfully.",
        "failed":           "Installation failed.",
        "auto_installed":   "module(s) installed automatically.",
        "manual":           "Modules not installed (install manually):",
        "all_ok":           "All dependencies are ready.",
        "unstable":         "Some modules failed. ATLAS may be unstable.",
    },
}


def _get_lang() -> str:
    """Lit la langue sauvegardée dans atlas_config.json (défaut : 'en')."""
    try:
        import json
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atlas_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                return json.load(f).get("lang", "en")
    except Exception:
        pass
    return "en"


def install_package(pip_name: str) -> bool:
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_and_install():
    lang = _get_lang()
    L    = LABELS[lang]

    print(f"\n  {L['checking']}\n")

    all_ok    = True
    installed = []
    failed    = []

    for import_name, pip_name, _ in REQUIRED_PACKAGES:
        desc = L.get(pip_name, "")
        try:
            __import__(import_name)
            print(f"  [OK]  {pip_name:<20} {desc}")

        except ImportError:
            print(f"  [--]  {pip_name:<20} {L['installing']}", end="", flush=True)
            success = install_package(pip_name)

            if success:
                print(f"\r  [OK]  {pip_name:<20} {L['installed']}")
                installed.append(pip_name)
            else:
                print(f"\r  [!!]  {pip_name:<20} {L['failed']}")
                failed.append(pip_name)
                all_ok = False

    print()

    if installed:
        print(f"  {len(installed)} {L['auto_installed']}")

    if failed:
        print(f"\n  {L['manual']}")
        for pkg in failed:
            print(f"    pip install {pkg}")
        print()

    if all_ok:
        print(f"  {L['all_ok']}\n")
    else:
        print(f"  {L['unstable']}\n")

    return all_ok