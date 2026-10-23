# Comment noter les réponses (à faire par toi)

Ouvre `results.csv` dans Excel ou LibreOffice (l'arabe s'affiche bien). Pour chaque ligne, lis :
`question`, `reponse_attendue` (ce que j'ai écrit à partir d'un vrai passage), `reponse_systeme` (ce que l'assistant a répondu) et `sources_citees`.

Remplis ensuite **deux colonnes** (les autres sont déjà calculées automatiquement) :

## `note_exactitude` : la réponse est-elle juste ? (0, 1 ou 2)

| Note | Quand | Exemple |
|---|---|---|
| **2** | Correcte et complète : elle contient l'information essentielle de la réponse attendue. | Attendu « 5 ans » → le système dit « cinq ans ». |
| **1** | Partielle : une partie est juste, ou il manque un élément important. | Attendu « arabe et amazighe » → le système ne cite que l'arabe. |
| **0** | Fausse, hors sujet, ou refus alors qu'une réponse existait. | Le système répond « je n'ai pas trouvé » à une question du corpus. |

Pour les questions `hors_corpus`, **ne remplis pas** `note_exactitude` : le refus est déjà mesuré dans `refus_correct`.

## `note_fidelite` : la réponse n'invente-t-elle rien ? (0 ou 1)

| Note | Quand |
|---|---|
| **1** | Tout ce que dit la réponse se trouve dans les sources citées (même si elle est incomplète). |
| **0** | La réponse contient au moins une information qui n'est dans aucune source (invention, chiffre ajouté, détail inventé). |

Pour vérifier, ouvre le passage dans `extrait_source` de `questions.csv`, ou le PDF à la page indiquée.
Pour un refus poli, mets **1** (il n'invente rien).

## Colonne `commentaire` (facultative mais très utile)

Écris la **cause** quand une réponse est fausse ou partielle. Les causes à distinguer (le PRD demande cette analyse) :
1. mauvais document retrouvé ;
2. bon document, mais passage mal découpé ;
3. le modèle a inventé ;
4. texte arabe mal extrait ;
5. question en une langue, réponse dans l'autre langue.

## Ensuite

```bash
cd backend
..\venv\Scripts\python.exe -m evaluation.run_eval --summary
```

Cette commande calcule toute seule : exactitude moyenne, fidélité en %, hit rate@5, refus correct, latence. **Seuls les chiffres que ce script affiche** doivent aller dans le README.

## Un conseil

Note **sans regarder** le score de la source ni la page attendue : juge seulement si la réponse est juste et si elle est fidèle au texte. Prends ton temps sur les 5 questions en arabe : si l'arabe de la réponse te paraît faux ou mal formulé, dis-le dans `commentaire`.
