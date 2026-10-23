# Interface de l'assistant civique marocain

Application React (Vite + Tailwind CSS). Elle ne contient aucune logique d'IA : elle envoie la question à l'API (`POST /chat`) et affiche la réponse avec ses sources.

```bash
copy .env.example .env     # puis adapter VITE_API_URL si besoin
npm install
npm run dev                # http://localhost:5173
npm run build              # version de production dans dist/
```

- `src/api.js` : appel à l'API et gestion des erreurs
- `src/translations.js` : tous les textes en français et en arabe
- `src/components/` : un composant par élément de l'écran (en-tête, accueil, conversation, bulles, sources, saisie, avertissement)

Déploiement (Vercel ou Netlify) : relier le dépôt GitHub, choisir le dossier `frontend`, puis définir la variable `VITE_API_URL` avec l'adresse publique du backend.
