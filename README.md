<div align="center">

# Moroccan Civic Assistant
### A bilingual (French / Arabic) RAG chatbot grounded in 35 official texts

<p>Ask about the Moroccan Constitution, elections, political parties and institutions, in French or Arabic. The assistant answers only from official documents, cites and highlights its sources, stays politically neutral, and says "I don't know" when the answer is not in the texts.</p>

<p>
  <a href="README.fr.md"><img src="https://img.shields.io/badge/Version_fran%C3%A7aise-6A1B9A?style=for-the-badge&logo=googletranslate&logoColor=white" alt="Version française"></a>
  <a href="backend/notebooks/01_analyse_exploratoire.ipynb"><img src="https://img.shields.io/badge/Exploratory_analysis-1565C0?style=for-the-badge&logo=jupyter&logoColor=white" alt="Exploratory analysis notebook"></a>
  <a href="https://github.com/salmahanabal/Moroccan-civic-assistant/actions/workflows/ci.yml"><img src="https://github.com/salmahanabal/Moroccan-civic-assistant/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

<p>
  <a href="#results"><img src="https://img.shields.io/badge/Final_test_hit_rate%405-86%25-2E7D32?style=for-the-badge" alt="Final test hit rate@5 86%"></a>
  <a href="#results"><img src="https://img.shields.io/badge/Wrongful_refusals-18%25_%E2%86%92_11%25-1565C0?style=for-the-badge" alt="Wrongful refusals 18% to 11%"></a>
  <a href="#results"><img src="https://img.shields.io/badge/Correct_refusals-23%2F23-2E7D32?style=for-the-badge" alt="Correct refusals 23/23"></a>
  <a href="#corpus"><img src="https://img.shields.io/badge/Official_documents-35-5E35B1?style=for-the-badge" alt="35 official documents"></a>
  <a href="#corpus"><img src="https://img.shields.io/badge/Languages-French_%2B_Arabic-6A1B9A?style=for-the-badge" alt="French and Arabic"></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS">
  <img src="https://img.shields.io/badge/ChromaDB-3F51B5?style=for-the-badge" alt="ChromaDB">
  <img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

</div>

---

## Table of contents

- [Overview](#overview)
- [Demo](#demo)
- [Highlights](#highlights)
- [How it works](#how-it-works)
- [Corpus](#corpus)
- [Results](#results)
- [Evaluation method](#evaluation-method)
- [Detailed evaluation](#detailed-evaluation)
- [Exploratory analysis](#exploratory-analysis)
- [The web interface](#the-web-interface)
- [API](#api)
- [Getting started](#getting-started)
- [Project structure](#project-structure)
- [Quality](#quality)
- [Limitations](#limitations)
- [Ideas for improvement](#ideas-for-improvement)
- [Tech stack](#tech-stack)
- [Privacy and disclaimer](#privacy-and-disclaimer)
- [Author](#author)

## Overview

Many young people cannot easily find what the law says about elections, parties or the Parliament: the texts are scattered across several official websites, written in legal language, and often available in one language only.

This project is a **retrieval-augmented generation (RAG)** system, built by hand without LangChain: it retrieves the passages of 35 official Moroccan texts that are closest to a question, then asks an LLM to answer **only** from those passages. Every answer cites its sources (document, page, the sentence that answers, link to the original). When the passages do not contain the answer, the assistant says so instead of inventing one, and it refuses to give political opinions.

The project also documents how well it works: three question sets, a hand-scored evaluation, an LLM judge validated with Cohen's kappa, an exploratory analysis of the embeddings, and a list of measured limits.

It is a portfolio repository: code, evaluation and documentation are public. To run it yourself, see [Getting started](#getting-started): the PDFs and the index are not published, so you rebuild them locally.

## Demo

![Demo: answer with sources, highlighted source, official document, Arabic, neutral refusal](docs/demo/demo_surlignage_natif.gif)

<sub>[Watch the video at real speed](docs/demo/demo_surlignage_natif.webm) (WebM, 5.4 MB). The project is not hosted online: the demo was recorded from a local run.</sub>

The demo shows a French question with numbered sources, a click that unfolds the source and highlights the sentence that answers (Article 47 of the Constitution), the link to the official site, the same in Arabic with a right-to-left interface, and a polite neutral refusal to an opinion question.

## Highlights

- **Verifiable sources.** Each answer shows the document, the page, an excerpt with the answering sentence highlighted, and a link to the original (PDFs open at the cited page).
- **Strict neutrality.** Opinion and voting-advice questions are refused before any LLM call (French and Arabic rules), and a strict prompt backs this up.
- **One multilingual index.** `BAAI/bge-m3` embeds French and Arabic in the same space, so a French question can find a law that exists only in Arabic. At least 2 of the 5 retrieved passages come from the other language.
- **Honest refusals.** A similarity threshold and a strict prompt make the assistant answer "not in my documents" rather than invent.
- **Multi-part questions.** A question about two topics is split into simple questions for retrieval, with a fallback if the LLM is slow.
- **Hand-written pipeline.** Extraction, cleaning (including Arabic ligature repair), chunking, embeddings, vector store, retrieval and generation are one readable function each.
- **Measured, not claimed.** Three question sets that cover all 35 documents, including a final test never used to tune the system.
- **Engineering basics.** FastAPI with validation and rate limiting, Docker image, GitHub Actions CI, 171 tests.

## How it works

```mermaid
flowchart LR
  subgraph Offline
    A["35 official PDFs"] --> B["Extraction (PyMuPDF)"] --> C["Cleaning (Arabic ligatures)"] --> D["Chunking 800 / 150"] --> E["Embeddings bge-m3"] --> F[("ChromaDB")]
  end
  subgraph Online
    Q["Question"] --> L["Language detection"] --> G["Guardrails: opinion, unsupported language"]
    G --> R["Split multi-part questions"]
    R --> S["Retrieval: 5 passages, at least 2 from the other language"]
    F -. read .-> S
    S --> T{"Score >= 0.50 ?"}
    T -- no --> X["Polite refusal"]
    T -- yes --> M["Gemini LLM (model fallback)"]
    M --> U["Cited sources + highlighted sentence"]
  end
```

**Offline (building the index).** PDFs are read page by page with PyMuPDF, cleaned (repeated headers removed, Arabic ligatures stored backwards by some PDFs repaired), cut into 800-character chunks with a 150-character overlap, embedded with `bge-m3` (1,024-dimension vectors) and stored in ChromaDB: 4,028 chunks from 1,293 pages.

**Online (one question).**

1. The language is detected and two cases are refused at once, without using any LLM quota: requests for a political opinion and unsupported languages (English).
2. If the question looks multi-part, an LLM splits it into up to 3 simple questions, **only for retrieval**. It never sees any passage, and the call is capped at 8 seconds.
3. Retrieval returns the 5 closest chunks, with a **guaranteed minimum of 2 from the other language**: if the best chunks are all in the question's language, the best chunks of the other language replace the last ones; if the other language is already well represented, nothing is capped.
4. If even the best chunk scores under 0.50, the assistant refuses without calling the LLM.
5. Otherwise Gemini receives the question, the numbered passages and strict rules (use only the passages, cite them, stay neutral, read passages in the other language, answer the part of the question that can be answered). A list of fallback models handles the free-tier daily quotas.
6. Only the passages actually cited are returned. For each one, the sentence sharing the most words and numbers with the answer is highlighted.

## Corpus

**35 official documents** (20 in French, 15 in Arabic) collected between 18 and 25 October 2026; 62 % of the chunks are French, 38 % Arabic.

| Theme | Documents (FR / AR) | Content |
|---|---|---|
| Constitution | 2 (1 / 1) | Constitution of 2011 |
| Elections | 8 (2 / 6) | organic laws on the two chambers and on local elections, electoral lists law and its amendment, decree on the electoral lists website |
| Political parties | 2 (0 / 2) | organic law 29-11, decree on public funding |
| Institutions | 11 (9 / 2) | organic laws on prefectures, communes, regions, the finance law, the Constitutional Court, the government, parliamentary inquiry committees, the CESE; laws on the integrity authority and the Mediator; rules of procedure of the House of Representatives |
| Rights and participation | 12 (8 / 4) | petitions, legislative motions, strike, Amazigh language, associations, public assemblies, access to information, the CNDH, the youth council, the parity authority, press law, a guide on open government |

Sources: Ministry of Justice (Adala portal, 22 documents), General Secretariat of the Government (6), House of Representatives (5), Ministry of the Interior (2). The full register is in [`data/sources.csv`](data/sources.csv). **The PDFs are not redistributed** because the reuse conditions of the source websites are not specified.

## Results

The final system (35 documents, `bge-m3`, at least 2 passages of the other language, question splitting, corrected prompt) was measured on **three question sets, before and after a round of fixes**. Accuracy and faithfulness are rated by an LLM judge for all three sets so that "before" and "after" are comparable.

| Question set | System | Hit rate@5 | Correct refusals (off-topic) | Wrongful refusals | Accuracy (judge, 0–2) | Faithfulness (judge) |
|---|---|---|---|---|---|---|
| Starting set (30 questions) | before → after | 92 % → 84 % | 5/5 → 5/5 | 0 % → 0 % | 1.92 → 1.92 | 30/30 → 30/30 |
| Tuning set (45 questions) | before → after | 80 % → **89 %** | 10/10 → 10/10 | 20 % → **3 %** | 1.40 → **1.57** | 44/45 → 45/45 |
| **Final test set (36 questions)** | before → after | 89 % → 86 % | 8/8 → 8/8 | 18 % → **11 %** | 1.43 → **1.54** | 36/36 → 36/36 |

The starting set and the tuning set were used to find and fix flaws; the **final test set** was written before any fix and measured once with the corrected system. A wrongful refusal is the assistant answering "not in my documents" when the answer exists.

- **Wrongful refusals dropped**: 20 % → 3 % on the tuning set and 18 % → 11 % on the final test (5 → 3 of 28 questions).
- **Judge-rated accuracy rose slightly**: 1.40 → 1.57 (tuning) and 1.43 → 1.54 (final test).
- **No new invented answers**: all 23 off-topic questions are still refused.
- **Retrieval did not improve reliably**: hit rate@5 went up on the tuning set, down by one question on the final test, and down on the starting set (the set the first version had been tuned on).
- **A language gap remains.** Over the three sets, after the fixes: when the question and the text are in the **same language** (35 questions), 94 % of the right documents are found and 0 % of the answers are wrongful refusals; when the **languages differ** (28 questions), 82 % and 14 %. On the final test alone, wrongful refusals on cross-language questions stayed at 3 of 15, so that part of the improvement is established on the tuning sets but not confirmed by the final test.

All sets are small (28 to 35 in-corpus questions each): a difference of one or two questions is within noise.

![Before and after the fixes, on the three question sets](backend/notebooks/figures/11_avant_apres_corrections.png)

![Before and after the fixes, by language of the question and of the text](backend/notebooks/figures/12_avant_apres_par_langue.png)

## Evaluation method

- **Starting set** (30 questions written at the beginning): 25 in-corpus (simple, combined, Arabic) and 5 off-topic. It tuned the first version and is the one scored by hand (average accuracy 1.92 / 2 for the first version).
- **Tuning set** (45 questions): aimed at the 24 documents the starting set ignored, written from the texts before seeing any answer. It first served as a fresh test, then to find and fix the flaws.
- **Final test set** (36 questions): written before any fix, 15 of its 28 in-corpus questions deliberately cross the language of the question and of the text.
- Together, the three sets cover **all 35 documents**. Each question comes with an expected answer, the expected document(s), the page and the excerpt, **found automatically in the texts**.
- **Metrics**: hit rate@5 (the right document is among the 5 retrieved passages), correct refusal, wrongful refusal, accuracy (0 = wrong or refused, 1 = partial, 2 = correct and complete), faithfulness (0 only if the answer contains something absent from the cited passages), latency.
- **LLM judge and Cohen's kappa.** A free-tier Gemini model rates the same answers with the same grid. Before I revised one of my own scores after seeing a disagreement, agreement was 24/25 with **kappa 0.65**; after the revision it is 25/25 (kappa 1.00) but no longer independent of the judge, so 0.65 is the figure to quote. **28 deliberately bad answers** (another question's answer, a changed number, an invented sentence, a wrongful refusal) were all caught (28/28), although these are blatant defects.

### Detailed evaluation

This section gives the details behind the table above. The French README has the same content with a few extra tables ([Évaluation](README.fr.md#évaluation)).

**Retrieval configurations** (hit rate@5 on the 25 in-corpus questions of the starting set; files in [`backend/evaluation/`](backend/evaluation/)):

| Configuration | Hit rate@5 |
|---|---|
| 17 documents, e5-base, chunks 800/150 | 72 % (18/25) |
| same + 2 slots for the other language | 76 % (19/25) |
| same + 3 slots | 80 % (20/25) |
| 17 documents, e5-base, chunks 1,200/200 | 76 % (19/25) |
| 17 documents, `bge-m3`, 800/150 | 84 % (21/25) |
| 35 documents, `bge-m3`, no reserved slots | 76 % (19/25) |
| 35 documents, `bge-m3`, 2 slots | 84 % (21/25) |
| 35 documents, `bge-m3`, 3 slots | 84 % (21/25) |
| 35 documents, `bge-m3`, 2 slots + question splitting | **92 % (23/25)** |

`bge-m3` was kept over `e5-base`, with 2 reserved slots and question splitting. These rows are on the starting set the system was tuned on, so they are not an independent measure.

**What the tuning set revealed** (45 questions, run once on the system before any fix):

- **Reliability depends on the language of the question versus the language of the text.** When both are the same, the right document was found 19 times out of 20; when they differ, 8 times out of 13 (a French question on an Arabic-only text: 6 of 10).
- **7 wrongful refusals on 35 in-corpus questions (20 %).** Five of them were French questions on Arabic texts. In two cases the right document was among the 5 passages, so it was the generation that refused, not the retrieval.
- **The benefit of language slots and question splitting was not confirmed**: 28/35 for the full system against 30/35 for the raw top-5 search.
- **Judge-rated accuracy was 1.40 / 2** (1.75 on the 28 questions that got an answer). Faithfulness was 44/45.

**The fixes** (found by analysing those 7 refusals and the misses):

1. The "reserved" slots for the other language acted as a **cap**: a question in Arabic took exactly 3 Arabic and 2 French passages, so a relevant third French passage was dropped. It is now a **guaranteed minimum**.
2. The LLM prompt was **too strict**: it said to refuse whenever the excerpts did not contain the answer, and said nothing about passages in the other language or partial answers. It now asks the model to read excerpts in the other language carefully, answer the part of the question that can be answered, and refuse only when no excerpt helps. On the starting and tuning sets, 6 of the 7 wrongful refusals became answers, and the 11 off-topic questions that reached the LLM were all still refused.
3. Sources open the PDF at the cited page, unreadable bullets are replaced, and the previous sentence is shown when the highlighted one starts with "They", "This", and so on (cosmetic, not measured).

**Protocol.** Fixing a system by looking at its errors on a question set and then measuring it on the same set gives flattering numbers. The starting and tuning sets were used to **tune** the fixes. The final test set (36 questions) was written before any fix, measured with the old system, set aside, then measured **once** with the corrected system, with nothing changed in between. Intermediate experiments are kept in [`backend/evaluation/experiments/`](backend/evaluation/experiments/). Translating each question into the other language before retrieval was not tried: it needs one more LLM call per question on a free quota that is already tight.

**Results by language** (88 in-corpus questions over the three sets, before → after the fixes):

| Question and text | Questions | Hit rate@5 | Wrongful refusals |
|---|---|---|---|
| Same language | 35 | 34 → 33 | 2 → 0 |
| Different languages | 28 | 21 → 23 | 9 → 4 |
| Texts in both languages | 25 | 21 → 20 | 1 → 0 |

On the final test alone (15 cross-language questions), wrongful refusals stay at 3 and hit rate@5 at 13/15: the gain on those questions is established on the starting and tuning sets, **not confirmed by the final test**.

**Honest summary.** The fixes do what was expected on wrongful refusals (lower on all three sets, final test included) without producing invented answers, and slightly raise the judge's accuracy. They do **not** reliably improve retrieval. Two gaps remain: cross-language questions are somewhat less successful (hit rate@5 82 % against 94 %, wrongful refusals 14 % against 0 %), and questions that need two texts are rarely solved (0 of 2 on the final test).

**LLM judge and Cohen's kappa.** A free-tier Gemini model (temperature 0) rates the same answers with the same grid ([`llm_judge.py`](backend/evaluation/llm_judge.py)); Cohen's kappa is computed by hand and tested on a textbook example.

| | Agreement (accuracy, 25 questions) | Cohen's kappa |
|---|---|---|
| **Before** I revised my score for question 25 | 24/25 (96 %) | **0.65** |
| After the revision | 25/25 (100 %) | 1.00 |

- The single disagreement was question 25 (my score 2, judge 1 because the answer omits the organic law). I then lowered my score to 1, so **the "after" figure is no longer independent of the judge**; quote 0.65.
- Faithfulness: agreement 30/30, but kappa is undefined because both raters always give 1.
- **Kappa paradox**: when almost all scores are equal, a judge that answered "2" to everything would also agree with me without being able to spot an error. Hence **negative controls** ([`judge_controls.py`](backend/evaluation/judge_controls.py)): 28 bad answers built from real ones, which the judge must catch.

| Fabricated defect | Expected | Caught |
|---|---|---|
| Answer of another question | accuracy < 2 | 8/8 |
| Changed number | accuracy < 2 or faithfulness 0 | 4/4 |
| Invented sentence added | faithfulness 0 | 8/8 |
| Wrongful refusal | accuracy 0 | 8/8 |
| **Total** | | **28/28** |

These are deliberately blatant defects (no subtle error is tested), only 4 answers contained a number, the judge and the generator are from the same model family, and the 28 controls were scored by the lightest model because the main model's quota was exhausted that day.

**Highlighted excerpts.** An excerpt used to be the first 200 characters of the cited passage, which did not always contain the answer. Share of the answer's words present in the passage that also appear in the excerpt shown (41 sources written in the answer's language):

| Excerpt shown | Mean coverage |
|---|---|
| Old: start of the passage, 200 characters | 33 % |
| Start of the passage, 300 characters (same length as the new one) | 51 % |
| **Chosen sentence** | **79 %** |

This measure is partly circular (the sentence is chosen using the same words that are counted) and was completed by reading examples, not by a systematic human judgment.

**Limits of the evaluation.**

- Only the final test set (28 in-corpus and 8 off-topic questions) is an independent test, measured once. Its numbers are imprecise: the drop in hit rate@5 from 89 % to 86 % is **one** question.
- The final test set is deliberately hard on language: 15 of its 28 in-corpus questions cross the language of the question and of the text, so its rates do not reflect real use.
- The starting set was scored by hand by one person. The tuning and final test sets are scored by an LLM judge of the same family as the generator, not validated by hand on those sets. All "before / after" accuracies in the table are the judge's.
- Question splitting depends on an LLM (two runs can differ on a question) and latency depends on the free tier's load (from 2.5 s to 10 s on average depending on the day).

## Exploratory analysis

The notebook [`01_analyse_exploratoire.ipynb`](backend/notebooks/01_analyse_exploratoire.ipynb) (outputs included, 12 figures) examines the data before judging the chatbot.

- **Healthy extraction**: median chunk length around 700 characters, 2 chunks under 200 characters, no "glued" Arabic letters, 8 exact duplicates out of 4,028.
- **Language structures the embedding space more than topic**: silhouette 0.071 by language against 0.022 by theme (0.072 on the Constitution alone, where both languages say the same thing). Both values are low.
- **The top-5 passages follow the question's language**: 84 % are French for a French question (the corpus is 62 % French) and 80 % are Arabic for an Arabic question (38 % of the corpus). This is why a minimum of passages from the other language is guaranteed.
- **No refusal threshold separates the questions**: the lowest in-corpus question scores 0.530 and the highest off-topic one 0.650, so refusal relies on a low threshold (0.50) combined with the LLM's own refusal.

![t-SNE map of the 4,028 chunks, by language then by theme](backend/notebooks/figures/03_carte_tsne.png)

## The web interface

| French answer, source unfolded | Arabic answer (right-to-left layout) |
|---|---|
| ![French answer with the answering sentence highlighted in the source](screenshots/answer_fr.png) | ![Arabic answer with the answering sentence highlighted in the source](screenshots/answer_ar.png) |
| **Neutral refusal to an opinion question** | **On a phone** |
| ![Polite neutral refusal](screenshots/neutral_refusal.png) | ![Interface on a phone](screenshots/mobile.png) |

The interface is a React application (Vite + Tailwind CSS). It contains no AI logic: it sends the question to the API and displays the answer, the sources and a permanent disclaimer, in French or Arabic.

## API

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/health` | the API is up and the index contains chunks |
| `POST` | `/chat` | answers a question with its sources |

The body of `/chat` is a `question` (1 to 500 characters) and an optional `theme` to limit the search. Errors: `422` for an empty or too long question, `429` above 10 requests per minute per IP address, `503` with a readable message when the LLM is unavailable. A real response (excerpt shortened):

```json
{
  "answer": "Le Roi nomme le Chef du Gouvernement au sein du parti politique arrivé en tête des élections des membres de la Chambre des Représentants, et au vu de leurs résultats [1].",
  "language": "fr",
  "found": true,
  "sources": [
    {
      "id": 1,
      "file": "constitution_2011_fr.pdf",
      "page": 13,
      "excerpt": "Article 47 Le Roi nomme le Chef du Gouvernement au sein du parti politique arrivé en tête des élections des me…",
      "highlight_start": 0,
      "highlight_end": 177,
      "url": "https://www.chambredesrepresentants.ma/fr/la-constitution-du-royaume-du-maroc-2011",
      "score": 0.655
    }
  ]
}
```

`found` is `false` for a polite refusal, and `highlight_start` / `highlight_end` frame the answering sentence inside `excerpt` (`null` when none stands out).

## Getting started

The repository contains the code, the evaluation and the document register, but **not the 35 PDFs** (the reuse conditions of the source websites are not specified) **nor the vector index**. You rebuild both locally, which is the only part that takes some time.

**You need:** Python 3.11 (the version used by the CI and Docker), Node.js 20.19 or newer (the CI uses 24), about 3 GB of free disk space (PyTorch and the `bge-m3` model), and a free [Gemini API key](https://aistudio.google.com/apikey) for the chat itself. The tests need neither the key nor the model.

### 1. Backend

```bash
git clone https://github.com/salmahanabal/Moroccan-civic-assistant.git
cd Moroccan-civic-assistant/backend

python -m venv venv
# Windows (PowerShell):  venv\Scripts\Activate.ps1
# macOS / Linux:         source venv/bin/activate

pip install -r requirements.txt
```

`requirements.txt` pins `torch==2.7.1`. On a machine without an NVIDIA GPU you can save several GB by installing the CPU build first, as the CI does: `pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu`, then the line above.

Create the settings file and put your key in it:

```bash
cp .env.example .env        # Windows: copy .env.example .env
# then edit .env and set LLM_API_KEY=<your Gemini key>
```

### 2. Corpus and index

1. Download the documents listed in [`data/sources.csv`](data/sources.csv) (column `url`) and save each one as `data/raw/<name in the column fichier>`, for example `data/raw/constitution_2011_fr.pdf`. Some sources are web pages that link to the PDF.
2. From `backend/`, cut the texts into chunks, then build the index. The first run downloads the embedding model (several hundred MB) and computing 4,028 vectors takes a few minutes on a CPU:

```bash
python -m src.make_chunks      # writes data/processed/chunks.jsonl
python -m src.build_index      # writes backend/chroma_db/
```

The index depends on the exact files, so the figures of the evaluation are only reproduced with the same 35 documents. If a website has since updated a text, the numbers can differ slightly.

### 3. Run the API

```bash
uvicorn main:app --reload
```

Open http://localhost:8000/docs to try `/health` and `/chat`.

### 4. Run the interface

In a second terminal:

```bash
cd frontend
cp .env.example .env        # Windows: copy .env.example .env  (VITE_API_URL=http://localhost:8000)
npm ci
npm run dev
```

Open http://localhost:5173. `ALLOWED_ORIGINS` in `backend/.env` already allows this address.

### 5. Optional

- **Tests** (from `backend/`): `python -m pytest -q`. They use fake LLM and embedding functions. `requirements-dev.txt` is only needed for the notebook.
- **Docker** (from the repository root, after building the index, because the image copies it): `docker compose up --build`, then http://localhost:8000/docs. The key is read from `backend/.env`.
- **Re-run the evaluation** (from `backend/`, needs the key and the index): `python -m evaluation.run_eval --questions questions_set3.csv --output results_set3_new.csv --label set3`, then `python -m evaluation.run_eval --summary`. The options of each script are described at the top of its file.

## Project structure

```
.
├── backend/
│   ├── main.py                  FastAPI API (/health, /chat)
│   ├── schemas.py               input and output formats (Pydantic)
│   ├── src/                     RAG pipeline: ingest, cleaning, chunking, embeddings, vectorstore,
│   │                            retriever, query_rewriter, generator, prompts, guards, excerpt, rag
│   ├── evaluation/              3 question sets, results, LLM judge, negative controls, before/after comparison
│   ├── notebooks/               exploratory analysis and figures
│   ├── tests/                   171 pytest tests
│   └── Dockerfile
├── frontend/                    React interface (Vite, Tailwind)
├── data/sources.csv             register of the 35 documents (the PDFs are not published)
├── docs/demo/                   demo as GIF and video
├── screenshots/                 interface screenshots
├── docker-compose.yml
└── .github/workflows/ci.yml     continuous integration
```

## Quality

- **171 pytest tests** covering extraction, cleaning (including Arabic repair), chunking, the vector store, question splitting, excerpt selection, guardrails, the generator, orchestration, the API and the evaluation tools. They never call the real LLM or the real embedding model: both are replaced by fake functions.
- **GitHub Actions** runs on every push: backend tests, frontend lint and build, then a Docker image build with a start-up check on `/health`.
- **No secret in Git**: the API key lives in an ignored `.env` file, and the CI uses a dummy key.
- **Readable code**: one function per step, comments in French, variable and function names in English.

## Limitations

- **Performance gap by language of the text.** The assistant answers in the question's language whatever the language of the text (24 of the 28 cross-language questions get an answer), with somewhat lower reliability: wrongful refusals are 14 % (4 of 28) when the languages differ against 0 % (0 of 35) when they are the same, and hit rate@5 is 82 % against 94 %. This is expected from a multilingual embedding model, which first brings together texts in the question's language.
- **Questions that need two texts** are rarely solved (0 of 2 on the final test, 2 of 4 on the tuning set).
- **Refusal threshold**: no threshold separates in-corpus from off-topic questions (0.530 against 0.650), so refusal relies on a low threshold combined with the LLM's refusal.
- **Link to the Constitution**: "Open the document" leads to the home page of the text (a web page with one address for the whole document), not to the cited article.
- **Small question sets**: one or two questions of difference is within noise, and the tuning and final-test scores come from an LLM judge, not from a person.
- **Corpus**: mostly legal texts, harder to read than teaching guides; only 2 documents on political parties, both in Arabic; some texts may have been amended since collection; some Arabic PDFs keep extraction defects that cleaning does not repair.
- **Free LLM tier**: quotas per model and per day, one reason the project is not hosted publicly.
- **Scope**: no conversation memory, and English is not supported (polite refusal).

## Ideas for improvement

- Translate or rephrase the question into the other language before retrieval (one more LLM call per question, not tried), or compare sentence-level vectors, then measure on a **fourth question set** (the final test set must no longer be used for tuning).
- Add a reranker and a keyword search alongside the vector search, and try 1,200-character chunks with `bge-m3` (only tried with `e5-base`).
- Have a person score a sample of the tuning-set and final-test answers by hand, to validate the LLM judge on those sets.
- Add conversation memory and English support.

## Tech stack

Python 3.11, PyMuPDF, sentence-transformers (`BAAI/bge-m3`), ChromaDB, Gemini API (REST), FastAPI, Pydantic, slowapi, React, Vite, Tailwind CSS, Docker, GitHub Actions, pytest, pandas, scikit-learn, matplotlib, Jupyter.

## Privacy and disclaimer

Answers are **indicative**, drawn from official texts, and may be out of date: check with the competent institutions. The assistant gives no personalised legal advice and **no political opinion**. The text of the questions is never written to the API logs.

Sources: Ministry of Justice (Adala portal), General Secretariat of the Government, House of Representatives, Ministry of the Interior (electoral lists portal). The reuse conditions of these websites are not specified, which is why the documents are not redistributed here.

## Author

<table>
  <tr>
    <td align="center"><a href="https://github.com/salmahanabal"><b>Salma Hanabal</b></a><br><sub>@salmahanabal</sub></td>
  </tr>
</table>
