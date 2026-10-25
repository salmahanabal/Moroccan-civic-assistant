# Recette de l'image Docker du backend (API FastAPI + modèle d'embeddings + index).
# Construire (depuis la racine du projet) : docker compose up --build

FROM python:3.11-slim

# Affichage immédiat des journaux ; pas de cache pip (image plus légère)
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/user/.cache/huggingface

# Utilisateur non administrateur (uid 1000) : exigé par certains hébergeurs, meilleur pour la sécurité.
# On crée aussi le dossier de l'application à son nom : ChromaDB doit pouvoir y écrire.
RUN useradd -m -u 1000 user \
    && mkdir -p /home/user/app \
    && chown user:user /home/user/app
WORKDIR /home/user/app

# 1) PyTorch en version « CPU seulement » : la version par défaut embarque des bibliothèques
#    pour cartes graphiques NVIDIA (plusieurs Go) qui ne servent à rien sur un hébergeur gratuit.
RUN pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu

# 2) Les autres bibliothèques (requirements.txt copié seul d'abord : si seul le code change,
#    Docker réutilise cette étape longue au lieu de tout réinstaller)
COPY --chown=user requirements.txt .
RUN pip install -r requirements.txt

USER user

# 3) On télécharge le modèle d'embeddings PENDANT la construction de l'image,
#    pour que le démarrage de l'API ne dépende pas d'un téléchargement.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"

# 4) Le code et l'index ChromaDB (construit en local avec « python -m src.build_index »,
#    jamais publié sur GitHub). Le fichier .env est exclu par .dockerignore.
COPY --chown=user . .

# Port par défaut 7860 (Hugging Face) ; Cloud Run et Render fournissent leur propre PORT
EXPOSE 7860
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
