# NLP / AI layer

MVP (implemented in `score_feedback.py`):
- VADER sentiment on client-feedback text, domain-adapted with delivery-risk vocabulary
  ("gaps", "inconsistent", "rework", "delayed", ...)
- issue taxonomy applied only to comments that express a concern (positive comments are
  tagged NO_ISSUE so praise is not counted as a problem)
- issue taxonomy:
  COMMUNICATION, DELIVERY, TECHNICAL_SKILL, QUALITY, TIMELINE,
  COLLABORATION, CLIENT_EXPECTATION, AVAILABILITY

Portfolio enhancement:
- transformer embeddings / stronger classifier

Prescriptive AI should operate from structured risk drivers and remain human-reviewed.
