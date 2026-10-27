"""Train and compare Logistic Regression and Random Forest, then save the best model.

Usage (PowerShell):   python train_model.py
                      python train_model.py --dataset data\dataset.csv --sample 50000
"""
import argparse
import sys

from config import Config
from src.data_preprocessing import DatasetError, load_dataset
from src.model_training import train_and_report


def main():
    ap = argparse.ArgumentParser(description="Train the PhishGuard AI model.")
    ap.add_argument("--dataset", default=str(Config.DATASET_PATH), help="path to the labelled URL CSV")
    ap.add_argument("--sample", type=int, default=0, help="optional: use a stratified random subset of N rows (quick runs)")
    args = ap.parse_args()

    try:
        df, info = load_dataset(args.dataset, Config.URL_COLUMN, Config.LABEL_COLUMN, Config.LEGITIMATE_LABEL_VALUE)
    except DatasetError as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        return 1

    if args.sample and args.sample < len(df):
        df = df.groupby("label", group_keys=False).sample(frac=args.sample / len(df), random_state=Config.RANDOM_STATE)
        info["sampled_rows_used"] = int(len(df))

    print("Dataset summary:", info)
    metrics = train_and_report(df, info, Config.MODEL_PATH, Config.REPORT_DIR, Config.TEST_SIZE, Config.RANDOM_STATE)

    print("\n=== Results on the held-out test set ===")
    for name, r in metrics["models"].items():
        cm = r["confusion_matrix"]
        print(f"{name:20s} acc={r['accuracy']:.4f} prec={r['precision_phishing']:.4f} "
              f"rec={r['recall_phishing']:.4f} f1={r['f1_phishing']:.4f} auc={r.get('roc_auc', float('nan')):.4f} "
              f"missed phishing (FN)={cm['false_negative']}")
    print(f"\nSelected model: {metrics['selected_model']}  ({metrics['selection_criterion']})")
    print(f"Saved model   -> {Config.MODEL_PATH}\nSaved reports -> {Config.REPORT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
