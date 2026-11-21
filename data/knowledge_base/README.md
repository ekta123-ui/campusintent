# Knowledge base

Everything in this folder is ingested into the vector database by `python scripts/ingest_kb.py`.

| File type | How it is used |
|---|---|
| `*.csv` | FAQ rows. Columns: `question, alt_questions (separated by " \| "), answer, intent, course, source` |
| `*.md`, `*.txt` | Long documents (prospectus, rules). Split into chunks automatically. |
| `*.pdf` | Same as above (needs `pip install pypdf`). |

`starter_faq.csv` contains **generic** starter answers (no real fees, dates or phone numbers).
Replace or extend them with your college's real information, then run the ingest script again
(`--reset` removes file-based entries first and keeps answers added by staff through the admin panel).

Sub-folders (such as `templates/`) are NOT ingested.
