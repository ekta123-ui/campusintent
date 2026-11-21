# Real queries (recommended)

Add `real_test_queries.csv` here with two columns: `query,intent`.
Collect 300-500 genuine questions from classmates or the college helpdesk, label them with the
same 16 intents, and keep them OUT of training. `python -m src.train_baseline` will then also
report accuracy and macro F1 on this set - that is the number to quote in your report.
