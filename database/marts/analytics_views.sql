-- Analytics marts (PostgreSQL). Portable standard SQL, public schema,
-- consistent with the tables the loader creates and the as_of_date column.
DROP VIEW IF EXISTS v_latest_engagement_health;
CREATE VIEW v_latest_engagement_health AS
SELECT eh.* FROM engagement_health eh
JOIN (SELECT engagement_id, MAX(as_of_date) AS max_date FROM engagement_health GROUP BY engagement_id) x
  ON eh.engagement_id = x.engagement_id AND eh.as_of_date = x.max_date;

DROP VIEW IF EXISTS v_latest_risk;
CREATE VIEW v_latest_risk AS
SELECT rp.* FROM risk_predictions rp
JOIN (SELECT engagement_id, MAX(as_of_date) AS max_date FROM risk_predictions GROUP BY engagement_id) x
  ON rp.engagement_id = x.engagement_id AND rp.as_of_date = x.max_date;

DROP VIEW IF EXISTS v_revenue_protection;
CREATE VIEW v_revenue_protection AS
SELECT r.*, c.client_name, e.client_id, e.talent_id, t.role
FROM revenue_exposure r
JOIN engagements e ON e.engagement_id = r.engagement_id
JOIN clients c ON c.client_id = e.client_id
JOIN talents t ON t.talent_id = e.talent_id;
