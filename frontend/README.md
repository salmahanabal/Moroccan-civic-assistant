# Interface de l'assistant civique marocain

Application React (Vite + Tailwind CSS). Elle ne contient aucune logique d'IA : elle envoie la question à l'API (`POST /chat`) et affiche la réponse avec ses sources, en français ou en arabe (affichage de droite à gauche pour l'arabe).

- `src/api.js` : appel à l'API et gestion des erreurs
- `src/translations.js` : tous les textes en français et en arabe
- `src/components/` : un composant par élément de l'écran (en-tête, accueil, conversation, bulles, sources, saisie, avertissement). `SourceCard.jsx` affiche le passage cité avec la phrase qui répond surlignée.

Le projet complet est présenté dans le [README principal](../README.md).
