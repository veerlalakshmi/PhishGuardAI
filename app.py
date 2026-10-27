"""PhishGuard AI - Flask application."""
import json
import secrets
import sqlite3
from datetime import datetime, timezone

from flask import (Flask, abort, flash, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)

from config import Config
from src.feature_extraction import FEATURE_NAMES, URLValidationError, url_anatomy
from src.prediction import ModelNotAvailableError, Predictor

ALLOWED_REPORT_FILES = {
    "confusion_matrix_logistic_regression.png",
    "confusion_matrix_random_forest.png",
}


def create_app(config_overrides=None, predictor=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)
    app.predictor = predictor or Predictor(app.config["MODEL_PATH"])
    init_db(app)

    # ---------- helpers ----------
    def csrf_token():
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        return session["csrf"]

    def check_csrf():
        sent = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
        if not sent or not secrets.compare_digest(sent, session.get("csrf", "")):
            abort(400)

    def load_metrics():
        path = app.config["METRICS_PATH"]
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    @app.context_processor
    def inject_globals():
        return {"csrf_token": csrf_token, "model_ready": app.predictor.is_ready,
                "max_url_length": app.config["MAX_URL_LENGTH"], "feature_count": len(FEATURE_NAMES)}

    @app.after_request
    def security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; form-action 'self'"
        return resp

    # ---------- pages ----------
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/analyze")
    def analyze():
        check_csrf()
        raw = request.form.get("url", "")
        save = request.form.get("save_history") == "on"
        try:
            result = app.predictor.predict(raw, app.config["MAX_URL_LENGTH"])
        except URLValidationError as exc:
            return render_template("index.html", error=str(exc), submitted=raw[:app.config["MAX_URL_LENGTH"]]), 400
        except ModelNotAvailableError as exc:
            return render_template("index.html", error=str(exc), submitted=raw[:200]), 503
        except Exception:  # noqa: BLE001 - never leak internals
            app.logger.exception("Prediction failed")
            return render_template("index.html", error="Something went wrong while analysing this URL. Please try again.",
                                   submitted=raw[:200]), 500
        if save:
            add_history(app, result["url"], result["label"])
        return render_template("result.html", result=result, anatomy=url_anatomy(result["url"]), saved=save)

    @app.post("/api/predict")
    def api_predict():
        check_csrf()
        data = request.get_json(silent=True) or {}
        try:
            r = app.predictor.predict(data.get("url"), app.config["MAX_URL_LENGTH"])
        except URLValidationError as exc:
            return jsonify(error=str(exc)), 400
        except ModelNotAvailableError as exc:
            return jsonify(error=str(exc)), 503
        except Exception:  # noqa: BLE001
            app.logger.exception("API prediction failed")
            return jsonify(error="Internal error."), 500
        return jsonify(label=r["label"], is_phishing=r["is_phishing"], model=r["model_name"],
                       phishing_probability_estimate=r["phishing_probability"])

    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html", metrics=load_metrics())

    @app.get("/reports/<path:filename>")
    def report_file(filename):
        if filename not in ALLOWED_REPORT_FILES:
            abort(404)
        return send_from_directory(app.config["REPORT_DIR"], filename)

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/how-it-works")
    def how_it_works():
        return render_template("how_it_works.html")

    @app.get("/privacy")
    def privacy():
        return render_template("privacy.html")

    @app.get("/history")
    def history():
        return render_template("history.html", rows=get_history(app))

    @app.post("/history/clear")
    def history_clear():
        check_csrf()
        clear_history(app)
        flash("Prediction history cleared.")
        return redirect(url_for("history"))

    # ---------- errors ----------
    @app.errorhandler(400)
    def bad_request(_):
        return render_template("error.html", code=400, message="Bad request. Please go back and try again."), 400

    @app.errorhandler(404)
    def not_found(_):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(_):
        return render_template("error.html", code=413, message="Request too large."), 413

    @app.errorhandler(500)
    def server_error(_):
        return render_template("error.html", code=500, message="Internal server error."), 500

    return app


# ---------- history (SQLite, parameterised queries only) ----------
def _db(app):
    return sqlite3.connect(app.config["DATABASE_PATH"])


def init_db(app):
    try:
        app.config["DATABASE_PATH"].parent.mkdir(parents=True, exist_ok=True)
        with _db(app) as con:
            con.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "url TEXT NOT NULL, prediction TEXT NOT NULL, created_at TEXT NOT NULL)")
    except sqlite3.Error:
        app.logger.warning("History database unavailable; history disabled.")


def add_history(app, url, prediction):
    try:
        with _db(app) as con:
            con.execute("INSERT INTO history (url, prediction, created_at) VALUES (?, ?, ?)",
                        (url, prediction, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")))
    except sqlite3.Error:
        app.logger.warning("Could not save history entry.")


def get_history(app, limit=50):
    try:
        with _db(app) as con:
            return con.execute("SELECT url, prediction, created_at FROM history ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    except sqlite3.Error:
        return []


def clear_history(app):
    try:
        with _db(app) as con:
            con.execute("DELETE FROM history")
    except sqlite3.Error:
        pass


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
