"""Fabrique la page NOTATION.html pour noter les réponses plus facilement qu'avec le fichier CSV.

    python -m evaluation.make_scoring_page

La page affiche une question à la fois (question, réponse attendue, réponse du chatbot, passages
cités) avec des boutons pour les deux notes. Elle ne note RIEN toute seule : les notes sont celles
que tu choisis. Elle s'enregistre dans le navigateur et se termine par un bouton qui télécharge
le fichier mes_notes.csv, que `python -m evaluation.merge_notes` recopie dans results.csv.
"""

import csv
import json

from src import config, embeddings, vectorstore

RESULTS_FILE = config.EVAL_DIR / "results.csv"
OUTPUT_FILE = config.EVAL_DIR / "NOTATION.html"
PASSAGE_CHARS = 900   # longueur maximale du texte affiché pour chaque page citée


def read_csv(path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


PASSAGES_PER_PAGE = 2   # nombre de passages montrés pour chaque page citée
POOL_SIZE = 400         # on regarde les 400 passages les plus proches de la question pour retrouver ceux d'une page


def cited_passages(question: str, sources: str, collection) -> list[dict]:
    """Retrouve les passages précis que le chatbot a reçus pour chaque page citée.

    results.csv ne garde que « document + page ». Une page contient plusieurs passages : montrer son
    début serait trompeur. On refait donc la recherche de la question et, pour chaque page citée,
    on garde les passages de CETTE page les plus proches de la question (ceux que le chatbot a reçus).
    """
    pool = vectorstore.search(collection, embeddings.embed_query(question), top_k=POOL_SIZE)
    passages, seen = [], set()
    for source in filter(None, sources.split(";")):
        name, _, page = source.rpartition(" p.")
        if (name, page) in seen or not page.isdigit():
            continue
        seen.add((name, page))
        on_page = [c for c in pool if c["file"] == name and int(c["page"]) == int(page)][:PASSAGES_PER_PAGE]
        for chunk in on_page or [{"text": "(passage introuvable dans les résultats de la recherche)", "score": 0}]:
            passages.append({"title": f"{name}, page {page}", "text": chunk["text"][:PASSAGE_CHARS]})
    return passages


def load_previous_notes(path) -> dict[str, dict]:
    """Reprend des notes déjà saisies (mes_notes.csv) pour ne pas les perdre quand la page est régénérée."""
    if not path.exists():
        return {}
    return {
        row["id"]: {"exactitude": row["note_exactitude"], "fidelite": row["note_fidelite"], "commentaire": row["commentaire"]}
        for row in read_csv(path)
    }


def build_data() -> list[dict]:
    results = read_csv(RESULTS_FILE)
    extracts = {q["id"]: q["extrait_source"] for q in read_csv(config.EVAL_DIR / "questions.csv")}
    collection = vectorstore.get_collection()
    previous = load_previous_notes(config.EVAL_DIR / "mes_notes.csv")
    return [
        {
            "id": row["id"],
            "type": row["type"],
            "question": row["question"],
            "expected": row["reponse_attendue"],
            "answer": row["reponse_systeme"],
            "extract": extracts.get(row["id"], ""),
            "passages": cited_passages(row["question"], row["sources_citees"], collection),
            "refused": row["type"] == "hors_corpus",
            "previous": previous.get(row["id"]),
        }
        for row in results
    ]


PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Notation des réponses</title>
<style>
  :root { --bg:#f6f5f2; --card:#fff; --ink:#1c1b19; --muted:#6b675f; --line:#dedad2; --green:#0b7a4b; --red:#b3261e; --amber:#8a5a00; --soft:#f0eee9; }
  @media (prefers-color-scheme: dark) { :root { --bg:#161513; --card:#201f1c; --ink:#efece6; --muted:#a39e94; --line:#3a3833; --green:#4fc08d; --red:#f08a82; --amber:#e0b04a; --soft:#2a2925; } }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 system-ui,Segoe UI,Roboto,sans-serif; }
  main { max-width:860px; margin:0 auto; padding:16px; }
  header.top { position:sticky; top:0; background:var(--bg); padding:12px 0; border-bottom:1px solid var(--line); z-index:5; }
  h1 { font-size:1.15rem; margin:0 0 6px; }
  .bar { height:8px; background:var(--soft); border-radius:99px; overflow:hidden; }
  .bar > div { height:100%; background:var(--green); width:0; transition:width .2s; }
  .meta { display:flex; gap:12px; flex-wrap:wrap; align-items:center; justify-content:space-between; margin-top:8px; color:var(--muted); font-size:.9rem; }
  button { font:inherit; cursor:pointer; border:1px solid var(--line); background:var(--card); color:var(--ink); border-radius:10px; padding:8px 14px; }
  button:hover { border-color:var(--green); }
  button.primary { background:var(--green); color:#fff; border-color:var(--green); font-weight:600; }
  .help { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 16px; margin:16px 0; }
  .help summary { cursor:pointer; font-weight:600; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; margin:16px 0; }
  .card.done { border-color:var(--green); }
  .tag { display:inline-block; font-size:.75rem; padding:2px 8px; border-radius:99px; background:var(--soft); color:var(--muted); margin-right:6px; }
  h2 { font-size:1.05rem; margin:8px 0 12px; }
  .box { border-radius:10px; padding:10px 12px; margin:10px 0; white-space:pre-wrap; background:var(--soft); }
  .box .label { display:block; font-size:.75rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); margin-bottom:4px; }
  .box.expected { border-left:4px solid var(--green); }
  .box.answer { border-left:4px solid var(--amber); }
  details.passage { margin:6px 0; font-size:.92rem; }
  details.passage summary { cursor:pointer; color:var(--muted); }
  .scores { display:grid; gap:10px; margin-top:14px; }
  .group .q { font-weight:600; margin-bottom:6px; }
  .opts { display:flex; flex-wrap:wrap; gap:8px; }
  .opts label { display:flex; gap:6px; align-items:center; border:1px solid var(--line); border-radius:10px; padding:8px 12px; cursor:pointer; background:var(--card); }
  .opts input { accent-color:var(--green); }
  .opts label:has(input:checked) { border-color:var(--green); background:var(--soft); font-weight:600; }
  textarea { width:100%; min-height:56px; font:inherit; color:var(--ink); background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 10px; }
  .note { color:var(--muted); font-size:.88rem; }
  footer { text-align:center; padding:24px 0 48px; }
  #status { margin-top:10px; color:var(--muted); }
</style>
</head>
<body>
<main>
  <header class="top">
    <h1>Notation des réponses du chatbot</h1>
    <div class="bar"><div id="bar"></div></div>
    <div class="meta">
      <span id="count"></span>
      <span><label><input type="checkbox" id="onlyTodo"> Afficher seulement les questions non terminées</label></span>
    </div>
  </header>

  <details class="help" open>
    <summary>Comment ça marche (30 secondes)</summary>
    <p>Pour chaque question, compare la <b>réponse du chatbot</b> (cadre orange) avec la <b>réponse attendue</b> (cadre vert), puis clique sur deux notes.
    Tes choix sont enregistrés automatiquement dans ce navigateur : tu peux fermer la page et revenir plus tard.</p>
    <ul>
      <li><b>Exactitude</b> : la réponse est-elle juste ? <b>2</b> = juste et complète, <b>1</b> = en partie juste, <b>0</b> = fausse ou refus à tort.</li>
      <li><b>Fidélité</b> : le chatbot invente-t-il quelque chose ? <b>1</b> = tout vient des textes cités, <b>0</b> = au moins un détail inventé. Un refus poli compte <b>1</b>.</li>
      <li>Pour les questions hors sujet (le chatbot doit refuser), seule la fidélité est demandée.</li>
      <li>Si une réponse est fausse ou partielle, écris la cause dans « Commentaire » (mauvais document, passage mal découpé, invention, arabe mal extrait, question et réponse dans deux langues différentes).</li>
    </ul>
    <p class="note">Les passages cités sont les extraits que le chatbot a reçus pour chaque page citée : ouvre-les pour vérifier la fidélité. Si un passage te semble sans rapport avec la question, dis-le dans « Commentaire ».</p>
  </details>

  <div id="cards"></div>

  <footer>
    <button class="primary" id="download">Télécharger mes notes (mes_notes.csv)</button>
    <div id="status"></div>
    <p class="note">Ensuite : mets le fichier dans le dossier <code>backend/evaluation</code> et dis-le moi (ou lance <code>python -m evaluation.merge_notes</code>).</p>
  </footer>
</main>

<script>
const DATA = __DATA__;
const KEY = "notation_rag_maroc_v1";
let saved = {};
try { saved = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { saved = {}; }

function persist() { try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {} }
// Si le navigateur n'a rien gardé pour une question, on reprend les notes déjà saisies (mes_notes.csv)
function entry(id) {
  if (!saved[id]) {
    const item = DATA.find(d => d.id === id);
    saved[id] = Object.assign({ exactitude: "", fidelite: "", commentaire: "" }, item && item.previous ? item.previous : {});
  }
  return saved[id];
}
function isDone(item) {
  const e = entry(item.id);
  return e.fidelite !== "" && (item.refused || e.exactitude !== "");
}

function radios(item, field, options) {
  return options.map(([value, label]) => {
    const checked = String(entry(item.id)[field]) === String(value) ? "checked" : "";
    return `<label><input type="radio" name="${field}-${item.id}" data-id="${item.id}" data-field="${field}" value="${value}" ${checked}> ${label}</label>`;
  }).join("");
}

function escapeHtml(text) {
  return text.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function render() {
  const onlyTodo = document.getElementById("onlyTodo").checked;
  const html = DATA.filter(item => !onlyTodo || !isDone(item)).map(item => {
    const passages = item.passages.map(p =>
      `<details class="passage"><summary>${escapeHtml(p.title)}</summary><div dir="auto" style="white-space:pre-wrap">${escapeHtml(p.text)}</div></details>`).join("");
    const exactitude = item.refused ? "" : `
      <div class="group"><div class="q">Exactitude : la réponse est-elle juste ?</div>
        <div class="opts">${radios(item, "exactitude", [[2, "2 · Juste et complète"], [1, "1 · En partie juste"], [0, "0 · Fausse ou refus à tort"]])}</div></div>`;
    return `
    <section class="card ${isDone(item) ? "done" : ""}" id="q${item.id}">
      <span class="tag">Question ${item.id} / ${DATA.length}</span><span class="tag">${escapeHtml(item.type)}</span>
      <h2 dir="auto">${escapeHtml(item.question)}</h2>
      <div class="box expected" dir="auto"><span class="label">Réponse attendue (d'après un vrai passage)</span>${escapeHtml(item.expected)}</div>
      <div class="box answer" dir="auto"><span class="label">Réponse du chatbot</span>${escapeHtml(item.answer)}</div>
      ${passages ? `<div class="note">Passages cités par le chatbot :</div>${passages}` : `<div class="note">Aucune source citée (refus).</div>`}
      <div class="scores">
        ${exactitude}
        <div class="group"><div class="q">Fidélité : le chatbot invente-t-il quelque chose ?</div>
          <div class="opts">${radios(item, "fidelite", [[1, "1 · Rien d'inventé"], [0, "0 · Au moins une invention"]])}</div></div>
        <div class="group"><div class="q">Commentaire (facultatif)</div>
          <textarea data-id="${item.id}" data-field="commentaire" placeholder="Ex. : mauvais document retrouvé, arabe mal extrait…">${escapeHtml(entry(item.id).commentaire)}</textarea></div>
      </div>
    </section>`;
  }).join("");
  document.getElementById("cards").innerHTML = html || '<p class="card">Tout est noté. Tu peux télécharger tes notes en bas de page.</p>';
  updateProgress();
}

function updateProgress() {
  const done = DATA.filter(isDone).length;
  document.getElementById("count").textContent = `${done} / ${DATA.length} questions notées`;
  document.getElementById("bar").style.width = (100 * done / DATA.length) + "%";
}

document.addEventListener("change", event => {
  const t = event.target;
  if (!t.dataset || !t.dataset.field) return;
  entry(t.dataset.id)[t.dataset.field] = t.value;
  persist();
  const item = DATA.find(d => d.id === t.dataset.id);
  const card = document.getElementById("q" + t.dataset.id);
  if (card) card.classList.toggle("done", isDone(item));
  updateProgress();
});
document.addEventListener("input", event => {
  const t = event.target;
  if (t.tagName === "TEXTAREA") { entry(t.dataset.id).commentaire = t.value; persist(); }
});
document.getElementById("onlyTodo").addEventListener("change", render);

document.getElementById("download").addEventListener("click", () => {
  const quote = v => '"' + String(v).replace(/"/g, '""') + '"';
  const lines = ["id,note_exactitude,note_fidelite,commentaire"].concat(DATA.map(item => {
    const e = entry(item.id);
    return [item.id, item.refused ? "" : e.exactitude, e.fidelite, quote(e.commentaire)].join(",");
  }));
  const blob = new Blob(["\\ufeff" + lines.join("\\n") + "\\n"], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "mes_notes.csv";
  link.click();
  const missing = DATA.length - DATA.filter(isDone).length;
  document.getElementById("status").textContent = missing
    ? `Fichier téléchargé, mais il reste ${missing} question(s) sans note complète.`
    : "Fichier téléchargé : toutes les questions sont notées.";
});

render();
</script>
</body>
</html>
"""


def main() -> None:
    data = build_data()
    # « </ » est échappé pour qu'un texte ne puisse pas fermer la balise <script> par accident
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    OUTPUT_FILE.write_text(PAGE.replace("__DATA__", payload), encoding="utf-8")
    print(f"Page écrite : {OUTPUT_FILE} ({len(data)} questions)")


if __name__ == "__main__":
    main()
