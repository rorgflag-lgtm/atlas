# ============================================================
# ATLAS - Utilitaires d'affichage
# ============================================================

import os
import sys
from colorama import init, Fore, Style

init(autoreset=False)

GOLD  = "\033[38;5;214m"
RESET = Style.RESET_ALL
BOLD  = Style.BRIGHT
DIM   = Style.DIM
WHITE = Fore.WHITE

# ── Textes multilingues des utilitaires ──────────────────────
_UI = {
    "en": {
        "error_prefix":   "[ERROR]",
        "ok_prefix":      "[OK]",
        "choice_prompt":  "Your choice  >  ",
        "selected":       "Selected : ",
        "invalid_choice": "Invalid choice. Enter a number between 1 and {n}.",
        "subtitle_1":     "The Pillar of Artificial Intelligence",
        "subtitle_2":     "Neurosymbolic AI Operating System",
    },
    "fr": {
        "error_prefix":   "[ERREUR]",
        "ok_prefix":      "[OK]",
        "choice_prompt":  "Votre choix  >  ",
        "selected":       "Sélectionné : ",
        "invalid_choice": "Choix invalide. Entrez un numéro entre 1 et {n}.",
        "subtitle_1":     "Le Pilier de l'Intelligence Artificielle",
        "subtitle_2":     "Système d'Exploitation pour IA Neurosymbolique",
    },
}


def _get_lang() -> str:
    """Lit la langue depuis atlas_config.json (défaut : 'en')."""
    try:
        import json
        import os as _os
        cfg = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "atlas_config.json")
        if _os.path.exists(cfg):
            with open(cfg, "r", encoding="utf-8") as f:
                return json.load(f).get("lang", "en")
    except Exception:
        pass
    return "en"


def _L(key: str, **kwargs) -> str:
    lang = _get_lang()
    text = _UI.get(lang, _UI["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text


# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────

def print_header():
    """
    Header ATLAS au lancement.
    Les sous-titres s'adaptent à la langue configurée.
    """
    sub1 = _L("subtitle_1")
    sub2 = _L("subtitle_2")

    # Calcul du padding pour centrer dans une boîte de 62 chars intérieurs
    BOX = 62

    def pad_line(text: str) -> str:
        """Centre le texte dans la boîte et retourne la ligne complète."""
        spaces_total = BOX - len(text)
        left  = spaces_total // 2
        right = spaces_total - left
        return f"{GOLD}{BOLD}║{' ' * left}{WHITE}{text}{GOLD}{' ' * right}║{RESET}"

    print()
    print()
    print(f"{GOLD}{BOLD}╔{'═' * BOX}╗{RESET}")
    print(f"{GOLD}{BOLD}║{'':62}║{RESET}")
    print(f"{GOLD}{BOLD}║     █████╗ ████████╗██╗      █████╗ ███████╗   v1.0.0     ║{RESET}")
    print(f"{GOLD}{BOLD}║    ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝              ║{RESET}")
    print(f"{GOLD}{BOLD}║    ███████║   ██║   ██║     ███████║███████╗              ║{RESET}")
    print(f"{GOLD}{BOLD}║    ██╔══██║   ██║   ██║     ██╔══██║╚════██║              ║{RESET}")
    print(f"{GOLD}{BOLD}║    ██║  ██║   ██║   ███████╗██║  ██║███████║              ║{RESET}")
    print(f"{GOLD}{BOLD}║    ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝              ║{RESET}")
    print(f"{GOLD}{BOLD}║{'':62}║{RESET}")
    print(pad_line(sub1))
    print(f"{GOLD}{BOLD}║{'':62}║{RESET}")
    print(pad_line(sub2))
    print(f"{GOLD}{BOLD}║{'':62}║{RESET}")
    print(f"{GOLD}{BOLD}╚{'═' * BOX}╝{RESET}")
    print()
    print()


# ──────────────────────────────────────────────────────────────
# AFFICHAGE
# ──────────────────────────────────────────────────────────────

def print_atlas(message: str):
    """Message de contenu standard."""
    print(f"{WHITE}  {message}{RESET}")


def print_error(message: str):
    """Message d'erreur en rouge."""
    prefix = _L("error_prefix")
    print()
    print(f"{Fore.RED}{BOLD}  {prefix} {message}{RESET}")
    print()


def print_success(message: str):
    """Message de succès en vert."""
    prefix = _L("ok_prefix")
    print()
    print(f"{Fore.GREEN}{BOLD}  {prefix} {message}{RESET}")
    print()


def print_section(title: str):
    """Titre de section centré avec séparateurs."""
    width = 60
    print()
    print()
    print(f"{GOLD}{BOLD}{'=' * width}{RESET}")
    print(f"{GOLD}{BOLD}{title.center(width)}{RESET}")
    print(f"{GOLD}{BOLD}{'=' * width}{RESET}")
    print()


def print_info_block(lines: list):
    """Bloc d'informations en blanc."""
    print()
    for line in lines:
        if line == "":
            print()
        else:
            print(f"{WHITE}    {line}{RESET}")
    print()


def print_command_block(cmd: str, desc: str):
    """Commande en or + description en blanc."""
    print(f"  {GOLD}{BOLD}  {cmd}{RESET}")
    print(f"{WHITE}      {desc}{RESET}")
    print()


# ──────────────────────────────────────────────────────────────
# SAISIE UTILISATEUR
# ──────────────────────────────────────────────────────────────

def ask(prompt: str) -> str:
    """Prompt en or, saisie en blanc."""
    print()
    response = input(f"  {GOLD}{BOLD}{prompt}{RESET}  >  ")
    print()
    return response


def ask_choice(prompt: str, choices: list) -> str:
    """Choix numéroté avec validation."""
    print(f"  {GOLD}{BOLD}{prompt}{RESET}")
    print()

    for i, choice in enumerate(choices, 1):
        print(f"  {GOLD}{BOLD}  [{i}]{RESET}  {WHITE}{choice}{RESET}")

    print()

    while True:
        response = input(
            f"  {GOLD}  {_L('choice_prompt')}{RESET}"
        ).strip()

        if response.isdigit() and 1 <= int(response) <= len(choices):
            selected = choices[int(response) - 1]
            print()
            print(f"  {Fore.GREEN}{BOLD}  {_L('selected')}{WHITE}{selected}{RESET}")
            print()
            return selected

        if response in choices:
            print()
            print(f"  {Fore.GREEN}{BOLD}  {_L('selected')}{WHITE}{response}{RESET}")
            print()
            return response

        print_error(_L("invalid_choice", n=len(choices)))