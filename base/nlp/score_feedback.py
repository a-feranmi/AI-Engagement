"""AI / NLP — Sentiment + Issue Classification.

Uses VADER (self-contained lexicon, no runtime download — deploy-safe) to score
client feedback sentiment, and a keyword classifier to tag each note against the
diagnostic issue taxonomy. Output feeds the root-cause dashboard and the app.

Run:  python -m src.nlp.score_feedback
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.config import DATA_DIR, ARTIFACTS

ISSUE_KEYWORDS = {
    "COMMUNICATION": ["communication", "updates", "stakeholders", "clarity"],
    "DELIVERY": ["delivery", "deliverables", "output", "implementation"],
    "TECHNICAL_SKILL": ["technical", "architecture", "code", "skill"],
    "QUALITY": ["quality", "defects", "rework", "accuracy"],
    "TIMELINE": ["deadline", "timeline", "delay", "schedule"],
    "COLLABORATION": ["team", "collaboration", "handover", "alignment"],
    "CLIENT_EXPECTATION": ["expectations", "scope", "requirements", "priority"],
    "AVAILABILITY": ["availability", "capacity", "attendance", "response time"],
}


def classify_issue(text: str) -> str:
    t = str(text).lower()
    scores = {k: sum(w in t for w in ws) for k, ws in ISSUE_KEYWORDS.items()}
    cat = max(scores, key=scores.get)
    return cat if scores[cat] > 0 else "GENERAL"


def main() -> None:
    fb = pd.read_csv(DATA_DIR / "client_feedback.csv", parse_dates=["feedback_date"])
    analyzer = SentimentIntensityAnalyzer()
    fb["sentiment_score"] = fb["comment"].map(
        lambda c: analyzer.polarity_scores(str(c))["compound"])
    fb["sentiment_label"] = pd.cut(fb["sentiment_score"], [-1.01, -0.2, 0.2, 1.01],
                                   labels=["Negative", "Neutral", "Positive"])
    fb["issue_category"] = fb["comment"].map(classify_issue)

    out = (fb[["engagement_id", "feedback_date", "sentiment_score",
               "sentiment_label", "issue_category"]]
           .rename(columns={"feedback_date": "source_date"}))
    out.to_csv(ARTIFACTS / "sentiment_scores.csv", index=False)

    print("VADER sentiment complete.")
    print(out["sentiment_label"].value_counts(normalize=True).round(3).to_string())
    print("\nTop diagnostic issues:")
    print(out[out.issue_category != "GENERAL"]["issue_category"]
          .value_counts(normalize=True).round(3).head(6).to_string())


if __name__ == "__main__":
    main()
