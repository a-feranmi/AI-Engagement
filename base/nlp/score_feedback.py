"""AI / NLP: sentiment + issue classification of client feedback.

1. Sentiment: VADER (self-contained lexicon, no runtime download, deploy-safe),
   adapted to consulting-delivery language. Out of the box VADER reads phrases
   such as "technical gaps ... requested additional support" (+0.40) or
   "response times have become inconsistent" (+0.46) as POSITIVE, because
   "support" and "response" carry positive weight and "gaps"/"inconsistent"
   carry none. DOMAIN_LEXICON adds negative weights for delivery-risk vocabulary,
   the standard way to domain-adapt a lexicon-based model.

2. Issue taxonomy: a keyword classifier tags each comment that expresses a
   CONCERN (sentiment Negative or Neutral) against the diagnostic taxonomy.
   Positive comments are tagged NO_ISSUE; otherwise praise such as
   "communication with the client is strong" would be counted as a
   communication problem and inflate the root-cause chart.

Output feeds the root-cause dashboard and the app.


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

# Delivery-risk vocabulary VADER under-weights (valence scale -4 .. +4).
DOMAIN_LEXICON = {
    "gaps": -1.8, "gap": -1.6, "inconsistent": -1.8, "declined": -1.6,
    "rework": -1.5, "delayed": -1.6, "concerns": -1.6, "follow-up": -0.8,
    "unpredictable": -1.6, "slippage": -1.8, "escalation": -1.4, "overdue": -1.8,
}
# "less predictable" is a negated positive VADER does not catch; map the phrase.
PHRASES = {"less predictable": "unpredictable", "no longer fully aligned": "misaligned"}
DOMAIN_LEXICON["misaligned"] = -1.6

NEGATIVE_BELOW, POSITIVE_ABOVE = -0.05, 0.2


def build_analyzer() -> SentimentIntensityAnalyzer:
    analyzer = SentimentIntensityAnalyzer()
    analyzer.lexicon.update(DOMAIN_LEXICON)
    return analyzer


def sentiment(analyzer: SentimentIntensityAnalyzer, text: str) -> float:
    t = str(text).lower()
    for phrase, token in PHRASES.items():
        t = t.replace(phrase, token)
    return analyzer.polarity_scores(t)["compound"]


def classify_issue(text: str) -> str:
    t = str(text).lower()
    scores = {k: sum(w in t for w in ws) for k, ws in ISSUE_KEYWORDS.items()}
    cat = max(scores, key=scores.get)
    return cat if scores[cat] > 0 else "GENERAL"


def main() -> None:
    fb = pd.read_csv(DATA_DIR / "client_feedback.csv", parse_dates=["feedback_date"])
    analyzer = build_analyzer()
    fb["sentiment_score"] = fb["comment"].map(lambda c: sentiment(analyzer, c))
    fb["sentiment_label"] = pd.cut(fb["sentiment_score"], [-1.01, NEGATIVE_BELOW, POSITIVE_ABOVE, 1.01],
                                   labels=["Negative", "Neutral", "Positive"])
    fb["issue_category"] = [classify_issue(c) if lab != "Positive" else "NO_ISSUE"
                            for c, lab in zip(fb["comment"], fb["sentiment_label"])]

    out = (fb[["engagement_id", "feedback_date", "sentiment_score",
               "sentiment_label", "issue_category"]]
           .rename(columns={"feedback_date": "source_date"}))
    out.to_csv(ARTIFACTS / "sentiment_scores.csv", index=False)

    print("VADER (domain-adapted) sentiment complete.")
    print(out["sentiment_label"].value_counts(normalize=True).round(3).to_string())
    concerns = out[out.issue_category != "NO_ISSUE"]
    print(f"\nIssue mix across {len(concerns):,} concern comments:")
    print(concerns["issue_category"].value_counts().to_string())


if __name__ == "__main__":
    main()
