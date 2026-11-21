# Results

## Classical baselines

| model                        |   val_accuracy |   val_f1_macro |   test_accuracy |   test_f1_macro |   train_seconds |
|:-----------------------------|---------------:|---------------:|----------------:|----------------:|----------------:|
| TF-IDF + Naive Bayes         |         0.9779 |         0.9778 |          0.9818 |          0.9816 |            0.25 |
| TF-IDF + Logistic Regression |         0.9896 |         0.9896 |          0.9935 |          0.9935 |            1.38 |
| TF-IDF + Linear SVM          |         0.9909 |         0.9909 |          0.9961 |          0.9961 |            0.48 |

Best baseline (by validation macro F1): **TF-IDF + Linear SVM**

Most confused intent pairs on the test set (true, predicted, count):

- Timetable_Schedule -> Exam_Results: 2
- Transport_Bus -> Faculty_Department: 1
