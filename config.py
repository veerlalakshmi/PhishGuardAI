"""Central configuration. Secrets come from environment variables, never from code."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_secret_key() -> str:
    """Use SECRET_KEY from the environment, else create/read a local key file in instance/."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_file = BASE_DIR / "instance" / "secret_key.txt"
    try:
        if key_file.exists():
            return key_file.read_text().strip()
        key_file.parent.mkdir(exist_ok=True)
        key = secrets.token_hex(32)
        key_file.write_text(key)
        return key
    except OSError:
        return secrets.token_hex(32)  # fallback: sessions reset on restart


class Config:
    SECRET_KEY = _load_secret_key()
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"   # local development only
    MAX_CONTENT_LENGTH = 16 * 1024                      # reject huge request bodies
    MAX_URL_LENGTH = 2048

    DATASET_PATH = Path(os.environ.get("PHISHGUARD_DATASET", BASE_DIR / "data" / "dataset.csv"))
    MODEL_PATH = BASE_DIR / "models" / "phishing_model.joblib"
    REPORT_DIR = BASE_DIR / "reports"
    METRICS_PATH = REPORT_DIR / "metrics.json"
    DATABASE_PATH = BASE_DIR / "instance" / "history.db"

    # Dataset column names (defaults match the UCI PhiUSIIL dataset).
    URL_COLUMN = "URL"
    LABEL_COLUMN = "label"
    # In PhiUSIIL, label 1 = legitimate and 0 = phishing. Change if your dataset differs.
    LEGITIMATE_LABEL_VALUE = 1

    RANDOM_STATE = 42
    TEST_SIZE = 0.2
