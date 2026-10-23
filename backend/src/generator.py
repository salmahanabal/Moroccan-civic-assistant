"""Appel du LLM (étape 3 de la requête, exigence FR-5).

C'est le SEUL fichier qui connaît le fournisseur du modèle (ici Gemini de Google).
Pour changer de fournisseur, on ajoute une fonction _call_xxx ci-dessous et on
change LLM_PROVIDER dans config.py : le reste du projet ne bouge pas.

On appelle directement l'API REST de Google avec la bibliothèque standard de Python
(urllib) : un délai maximum exact, une erreur immédiate si le quota du jour est épuisé,
et aucune dépendance en plus.
"""

import json
import urllib.error
import urllib.request

from src import config

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class LLMUnavailableError(Exception):
    """Le LLM n'a pas pu répondre (clé absente ou invalide, quota dépassé, panne...).

    L'API la transforme en erreur 503 avec un message lisible (jamais de trace technique).
    """


class _TryNextModel(Exception):
    """Échec temporaire d'un modèle (quota du jour épuisé, surcharge, délai dépassé) : on essaie le suivant."""


def _post_gemini(model: str, system_prompt: str, user_prompt: str) -> str:
    """Envoie la question à UN modèle Gemini et renvoie le texte de sa réponse."""
    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "maxOutputTokens": config.MAX_TOKENS,
            "thinkingConfig": {"thinkingLevel": config.LLM_THINKING_LEVEL},
        },
    }
    request = urllib.request.Request(
        GEMINI_URL.format(model=model),
        data=json.dumps(body).encode("utf-8"),
        # La clé voyage dans un en-tête (jamais dans l'adresse, qui pourrait finir dans des journaux)
        headers={"Content-Type": "application/json", "x-goog-api-key": config.LLM_API_KEY},
    )
    try:
        with urllib.request.urlopen(request, timeout=config.LLM_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        # 429 = quota épuisé ; 5xx = panne de Google ; 400 = paramètre refusé par CE modèle
        if error.code in (401, 403):
            raise LLMUnavailableError(f"Clé d'API refusée (code {error.code})") from error
        raise _TryNextModel(f"{model} : code {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:  # réseau coupé, délai dépassé...
        raise _TryNextModel(f"{model} : {type(error).__name__}") from error

    candidates = data.get("candidates") or []
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    # On ignore les éventuels passages de « réflexion » (marqués thought) : on garde la réponse
    text = "".join(part.get("text", "") for part in parts if not part.get("thought")).strip()
    if not text:
        raise _TryNextModel(f"{model} : réponse vide")
    return text


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Essaie les modèles de config.LLM_MODELS dans l'ordre et renvoie la première réponse obtenue."""
    if not config.LLM_API_KEY:
        raise LLMUnavailableError("Aucune clé d'API : remplissez LLM_API_KEY dans backend/.env")

    failures = []
    for model in config.LLM_MODELS:
        try:
            return _post_gemini(model, system_prompt, user_prompt)
        except _TryNextModel as failure:
            failures.append(str(failure))
    raise LLMUnavailableError("Aucun modèle n'a pu répondre : " + " ; ".join(failures))


# Un fournisseur = une fonction qui prend (prompt système, prompt utilisateur) et renvoie du texte
PROVIDERS = {"gemini": _call_gemini}


def generate_answer(system_prompt: str, user_prompt: str) -> str:
    """Génère la réponse avec le fournisseur choisi dans config.LLM_PROVIDER."""
    return PROVIDERS[config.LLM_PROVIDER](system_prompt, user_prompt)
