# CampusIntent: NLP Intent Classification + RAG Helpdesk for College Queries

A student asks a question (English, informal English, Hinglish, with typos). The system:

1. **Classifies the intent** (16 classes: Admission, Fees, Exam_Results, Hostel_Accommodation, Transport_Bus,
   Cafeteria_Food, Location_Directions, Placement, ...) and **extracts entities** (course, semester, weekday, date, document).
2. **Retrieves** the most relevant answers from a **vector database** knowledge base (RAG), re-ranked using the intent.
3. **Answers** from those sources (extractive, or written by Claude if you set an API key).
4. **Saves every new problem in a second vector collection.** Repeated questions are counted; questions the
   knowledge base cannot answer go to a staff queue. When staff answer them, the answer is added to the
   knowledge base, so the system learns the new problem.

```
student question
      |
      v
 NLP classifier (TF-IDF / DistilBERT) --> intent + entities
      |
      v
 vector DB "kb"  (FAQ + documents)  --> top matches, re-ranked by intent/course
      |                                   |
      | similarity >= threshold           | below threshold
      v                                   v
 answer (+ sources)                 "unanswered": saved in vector DB "queries"
                                          |   (duplicates are counted)
                                          v
                                    staff panel --> resolve --> added to "kb"  (system learns)
```

Courses covered: MCA, BCA, B.Sc, M.Sc, B.Com, LLB, Hotel Management, B.Pharmacy, D.Pharmacy,
B.Tech (Cyber Security, Web Development, AI & ML).

## Quick start (Windows / macOS / Linux)

```bash
pip install -r requirements.txt

python scripts/split_data.py          # train/val/test CSVs
python -m src.train_baseline          # trains and saves the intent classifier
python -m pytest                      # tests (13)

python -m uvicorn api.main:app --reload     # API  -> http://localhost:8000/docs
```
On first start the API loads the starter knowledge base into the vector database automatically.

Frontend (second terminal, needs Node.js):
```bash
cd frontend
npm install
npm run dev                           # http://localhost:5173  (tabs: Student chat | Staff panel)
```

Try the RAG pipeline from the command line:
```bash
python -m src.rag "how do I get a bonafide certificate?"
```

## Optional upgrades (each one is independent)

The project works without these: it falls back to built-in components. Install them one by one
(`requirements-optional.txt`) so one failure does not block the others.

| Package | What it upgrades | Fallback if missing |
|---|---|---|
| `chromadb` | real vector database (ChromaDB) | built-in numpy + JSON vector store |
| `sentence-transformers` | semantic embeddings (understands meaning and paraphrases) | offline hashing embedder (matches shared words, robust to typos) |
| `anthropic` + env `ANTHROPIC_API_KEY` | Claude writes the final answer from the retrieved sources | returns the best matching knowledge-base answer |
| `pypdf` | ingest PDF documents | PDFs are skipped |

Windows (PowerShell): `setx ANTHROPIC_API_KEY "sk-ant-..."` then open a new terminal.
The model name can be changed with the `CLAUDE_MODEL` environment variable.

If you install `chromadb` or `sentence-transformers` AFTER the first run, delete `data/vectordb/` so the
database is rebuilt with the new components (the API re-ingests the knowledge base on start).
Staff-added answers live inside `data/vectordb/`; export them first if you want to keep them.

## Your own knowledge base (important)

`data/knowledge_base/starter_faq.csv` has **generic** answers (no real fees, dates or phone numbers), because
I do not know your college's facts. Replace or extend it:

* **FAQ rows** in a CSV: `question, alt_questions (separated by |), answer, intent, course, source`
* **Documents** (prospectus, rules, notices) as `.md`, `.txt` or `.pdf` in the same folder
  (see `data/knowledge_base/templates/college_info_TEMPLATE.md.txt`)

Then run `python scripts/ingest_kb.py --reset` (removes old file-based entries, keeps staff-added answers).

## The learning loop

* `POST /ask` embeds the question and stores it in the `queries` vector collection with its predicted
  intent, status (`answered`, `unanswered`, `resolved`, `needs_review`) and how many times it was asked.
* Near-identical questions are merged (count goes up). The **Staff panel** shows what is asked most and unanswered.
* `POST /admin/resolve` (or the Staff panel) adds the staff answer to the knowledge base. The same question is
  answered immediately next time.
* Thumbs-down feedback on an answer moves it to `needs_review`.
* `python scripts/export_new_queries.py` writes `data/real_queries/collected_queries.csv`: genuine student queries
  with intents. Review them, then use them as the **real test set** and/or add them to the training data and
  retrain with `python -m src.train_baseline`.

Set `ADMIN_KEY` (environment variable) to require the `X-Admin-Key` header on staff endpoints.

## API

| Endpoint | Purpose |
|---|---|
| `POST /ask` | full RAG answer + saves the question (`"save": false` to skip) |
| `POST /predict` | intent classification only |
| `POST /feedback` | thumbs up / down for an answer |
| `GET /stats` | knowledge-base size, saved questions, top questions |
| `GET /admin/questions?status=unanswered` | staff queue |
| `POST /admin/resolve` | answer a saved question (adds it to the knowledge base) |
| `POST /admin/knowledge` | add an FAQ directly |

## Project layout

| Folder | Purpose |
|---|---|
| `data/raw`, `data/processed` | synthetic intent dataset (5,120 queries) and splits |
| `data/knowledge_base` | FAQ / documents that feed the vector database |
| `data/vectordb` | created at runtime: the vector database |
| `data/real_queries` | real labelled queries (test set) |
| `src/` | preprocessing, NLP features, classifier, embeddings, vector store, RAG, LLM helper, evaluation |
| `api/`, `frontend/` | FastAPI backend and React app |
| `notebooks/` | EDA, preprocessing, baselines, DistilBERT, error analysis, RAG demo |
| `scripts/` | dataset generator, splitter, KB ingest, query export |

## Results to report (and how to read them)

Intent classifier (synthetic test set): about 99.6% macro F1 with TF-IDF + Linear SVM. **This is inflated** because the
dataset is template-generated. Add 300-500 real labelled queries in `data/real_queries/real_test_queries.csv`
and report that score as the honest one.

Retrieval (`python -m src.eval_rag`, starter KB, offline hashing embedder, 768 synthetic test queries):

| Metric | Value |
|---|---|
| Right topic ranked first | 92.6% |
| Right topic within top 4 | 95.3% |
| Answered at threshold 0.30 (coverage) | 75.4%, of which 93.9% from the right topic |
| Out_of_Scope questions wrongly answered | 0% |

Run `python -m src.eval_rag` again after installing `sentence-transformers` and compare: that is a good
experiment for your report (lexical hashing vs semantic embeddings). Re-tune `ANSWER_THRESHOLD` in
`src/config.py` from the table it prints.

## Known limitations

* The hashing embedder matches words, not meaning, so paraphrases ("Do you have a robotics club?" vs "Is there a
  robotics club?") may be stored as separate questions. `sentence-transformers` fixes most of this.
* The Claude answer-writing path needs your API key and was not run in my test environment; if it fails,
  the pipeline falls back to the extractive answer.
* The starter knowledge base is generic. Answer quality depends on the real information you add.
* Staff endpoints use a simple shared key, not full authentication. Do not expose them publicly as they are.
* Entity extraction keeps one course per query.
