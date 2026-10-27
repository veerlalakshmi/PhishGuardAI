# PhishGuard AI — Machine Learning-Based Phishing URL Detector

A Flask web application that estimates whether a URL is **potentially phishing** or **predicted legitimate**, using a
scikit-learn model trained on a labelled public dataset. URLs are analysed as text only: they are never visited.

> **Status:** the code, tests and web app are complete. The model is **not trained until you add the dataset** and run
> `train_model.py`. Until then the app shows a "Model not trained yet" banner and refuses to predict. No results in this
> repository are pre-computed or invented.

## 1. Project overview
End-to-end ML project: data cleaning → URL feature engineering → comparing Logistic Regression and Random Forest →
honest evaluation → saving the best model → serving predictions in a responsive Flask dashboard.

## 2. Problem statement
Phishing links imitate trusted sites to steal credentials. Users need a quick signal about suspicious links *before* clicking.

## 3. Objectives
- Learn URL patterns that separate phishing from legitimate links.
- Compare two classifiers fairly and choose one with phishing recall in mind.
- Provide a safe, clear web interface that states its limitations.

## 4. Features
URL analyser · model-performance dashboard (real metrics + confusion matrices) · How It Works / About / Privacy pages ·
opt-in local prediction history with a clear button · CSRF protection, input limits, escaped output, security headers ·
automated tests.

## 5. Technology stack
Python 3.10+, scikit-learn, pandas, NumPy, Joblib, Matplotlib, Seaborn, Flask, SQLite, Pytest, HTML5/CSS3/JavaScript.

## 6. Project architecture
```
Browser ──► Flask (app.py) ──► src/prediction.py ──► src/feature_extraction.py (shared with training)
                                      │
                                      └──► models/phishing_model.joblib  (created by train_model.py)
train_model.py ──► src/data_preprocessing.py ─► src/model_training.py ─► models/ + reports/
```
| Path | Purpose |
|---|---|
| `app.py` | Routes, CSRF, error handlers, optional history |
| `train_model.py` | Command-line training script |
| `config.py` | Paths, limits, dataset column names |
| `src/feature_extraction.py` | URL validation + 27 numeric features |
| `src/data_preprocessing.py` | Load, validate, clean, normalise labels |
| `src/model_training.py` | Pipelines, metrics, model selection, plots |
| `src/prediction.py` | Loads the saved model, returns predictions |
| `templates/`, `static/` | Pages, CSS, JavaScript |
| `tests/` | Pytest suite (uses a clearly labelled mock model) |
| `docs/` | Internship report, resume text, interview questions |

## 7. Dataset source and download instructions
See [`data/README.md`](data/README.md). Recommended: **PhiUSIIL Phishing URL Dataset** from the UCI repository
(https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset). Save the CSV as `data\dataset.csv`.

## 8. Dataset format and label definitions
CSV with a `URL` column and a `label` column. In PhiUSIIL `1` = legitimate, `0` = phishing. Internally this project
converts to **1 = phishing, 0 = legitimate**. Change `config.py` if your dataset uses other names or values.

## 9–11. Installation on Windows (PowerShell)
```powershell
cd PhishGuardAI
py -m venv venv
.\venv\Scripts\Activate.ps1
# If activation is blocked:  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 12. Model training
```powershell
python train_model.py                  # uses data\dataset.csv
python train_model.py --sample 50000   # optional quick run on a stratified subset
```
This cleans the data, splits it (80/20, stratified, seed 42), trains both models, prints metrics, and saves
`models\phishing_model.joblib`, `reports\metrics.json`, confusion-matrix PNGs and classification reports.
**Which model is selected?** The one with the higher F2 score for the phishing class (recall counts more than precision,
because a missed phishing URL is the costly error). Accuracy alone is not used.

## 13–14. Start the app and open it
```powershell
python app.py
```
Open http://127.0.0.1:5000 in your browser. (Debug mode is off unless you set `$env:FLASK_DEBUG="1"` for local development.)

## 15. Run tests
```powershell
python -m pytest -v
```
The tests need no dataset: they use a mock predictor (clearly labelled "tests only") and a tiny **synthetic** dataset that
only checks the training code runs. Those synthetic numbers are never saved to `reports/`.

## 16. How to interpret the metrics (phishing = positive class)
- **Accuracy** – share of all predictions that were right; misleading if classes are imbalanced.
- **Precision** – of URLs flagged as phishing, how many really were. Low precision = many false alarms.
- **Recall** – of all real phishing URLs, how many were caught. Low recall = dangerous misses (**false negatives**).
- **F1** – balance of precision and recall. **F2** (used for selection) favours recall.
- **ROC-AUC** – how well the model ranks phishing above legitimate across all thresholds.
- **Confusion matrix** – counts of TN, FP, FN, TP. Look at the false-negative cell first.

## 17. Screenshots
After training and starting the app, capture with **Win + Shift + S** and save into `docs\screenshots\`:
1. Home page · 2. A "Potentially Phishing" result · 3. A "Predicted Legitimate" result · 4. Model Performance page
· 5. Terminal showing `train_model.py` output · 6. `pytest` passing. (Only use real runs.)
Example URLs for demos: use harmless made-up strings such as `http://192.168.0.1/secure-login/verify@account.example`.
Never open real phishing links.

## 18. Limitations and ethical considerations
URL-only analysis; dataset artefacts; false negatives and positives; shortened links; adversarial attackers.
"Predicted Legitimate" is **not** a safety guarantee. History is opt-in and stored locally; see the Privacy page.
Use only for education and awareness.

## 19. Future enhancements
Cross-validation and hyper-parameter tuning · probability calibration and adjustable threshold · additional URL features
(character n-grams) · SHAP/feature-importance explanations · domain-reputation lookups (opt-in) · Docker deployment ·
browser extension.

## 20. GitHub upload instructions
```powershell
git init
git add .
git status        # check: no dataset, models, venv, instance\*.db
git commit -m "Initial commit: PhishGuard AI"
git branch -M main
git remote add origin https://github.com/<your-username>/PhishGuardAI.git
git push -u origin main
```
