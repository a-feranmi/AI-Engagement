CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ==============================
-- CORE: dimensions / master data
-- ==============================
CREATE TABLE IF NOT EXISTS core.clients (
    client_id            VARCHAR(20) PRIMARY KEY,
    client_name          VARCHAR(150) NOT NULL,
    industry             VARCHAR(80) NOT NULL,
    company_size         VARCHAR(30),
    account_manager_id   VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS core.talents (
    talent_id            VARCHAR(20) PRIMARY KEY,
    talent_name          VARCHAR(120) NOT NULL,
    role                 VARCHAR(100) NOT NULL,
    seniority            VARCHAR(40) NOT NULL,
    years_experience     NUMERIC(4,1) NOT NULL CHECK (years_experience >= 0),
    primary_skill        VARCHAR(100),
    location             VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS core.engagements (
    engagement_id        VARCHAR(20) PRIMARY KEY,
    client_id            VARCHAR(20) NOT NULL REFERENCES core.clients(client_id),
    talent_id            VARCHAR(20) NOT NULL REFERENCES core.talents(talent_id),
    role                 VARCHAR(100) NOT NULL,
    start_date           DATE NOT NULL,
    expected_end_date    DATE NOT NULL,
    monthly_contract_value NUMERIC(14,2) NOT NULL CHECK (monthly_contract_value >= 0),
    status               VARCHAR(30) NOT NULL,
    termination_date    DATE,
    outcome              VARCHAR(40),
    CHECK (expected_end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS core.performance_reviews (
    performance_id      BIGSERIAL PRIMARY KEY,
    engagement_id       VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    review_date         DATE NOT NULL,
    technical_score     NUMERIC(5,2) CHECK (technical_score BETWEEN 0 AND 100),
    delivery_score      NUMERIC(5,2) CHECK (delivery_score BETWEEN 0 AND 100),
    communication_score NUMERIC(5,2) CHECK (communication_score BETWEEN 0 AND 100),
    overall_score       NUMERIC(5,2) CHECK (overall_score BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS core.client_feedback (
    feedback_id         BIGSERIAL PRIMARY KEY,
    engagement_id       VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    feedback_date       DATE NOT NULL,
    rating              NUMERIC(4,2) CHECK (rating BETWEEN 1 AND 5),
    comment             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS core.project_milestones (
    milestone_id        BIGSERIAL PRIMARY KEY,
    engagement_id       VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    milestone_name      VARCHAR(150) NOT NULL,
    due_date             DATE NOT NULL,
    completion_date      DATE,
    status               VARCHAR(30) NOT NULL,
    delay_days           INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS core.timesheets (
    timesheet_id        BIGSERIAL PRIMARY KEY,
    engagement_id       VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    period_start        DATE NOT NULL,
    expected_hours      NUMERIC(7,2) NOT NULL,
    actual_hours        NUMERIC(7,2) NOT NULL,
    utilisation_rate    NUMERIC(6,4)
);

CREATE TABLE IF NOT EXISTS core.checkins (
    checkin_id          BIGSERIAL PRIMARY KEY,
    engagement_id       VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    checkin_date        DATE NOT NULL,
    note                TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS core.placement_outcomes (
    outcome_id          BIGSERIAL PRIMARY KEY,
    engagement_id       VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    outcome_date        DATE NOT NULL,
    outcome_type        VARCHAR(50) NOT NULL,
    successful          BOOLEAN NOT NULL
);

-- ==============================
-- ANALYTICS / ML outputs
-- ==============================
CREATE TABLE IF NOT EXISTS analytics.engagement_health (
    engagement_id        VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    as_of_date           DATE NOT NULL,
    performance_health   NUMERIC(6,2),
    client_feedback_health NUMERIC(6,2),
    milestone_health     NUMERIC(6,2),
    utilisation_health   NUMERIC(6,2),
    sentiment_health     NUMERIC(6,2),
    behs                 NUMERIC(6,2),
    health_band          VARCHAR(20),
    PRIMARY KEY (engagement_id, as_of_date)
);

CREATE TABLE IF NOT EXISTS analytics.sentiment_scores (
    sentiment_id         BIGSERIAL PRIMARY KEY,
    engagement_id        VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    source_date           DATE NOT NULL,
    sentiment_score       NUMERIC(7,4),
    sentiment_label       VARCHAR(20),
    issue_category        VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS analytics.risk_predictions (
    prediction_id         BIGSERIAL PRIMARY KEY,
    engagement_id         VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    prediction_date       DATE NOT NULL,
    risk_probability      NUMERIC(7,5) CHECK (risk_probability BETWEEN 0 AND 1),
    risk_band             VARCHAR(20) NOT NULL,
    model_name            VARCHAR(80) NOT NULL,
    model_version         VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS analytics.interventions (
    intervention_id       BIGSERIAL PRIMARY KEY,
    engagement_id         VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    intervention_date     DATE NOT NULL,
    intervention_type     VARCHAR(80) NOT NULL,
    owner                 VARCHAR(100),
    priority              VARCHAR(20),
    status                VARCHAR(30),
    due_date              DATE,
    completed_date        DATE,
    outcome               TEXT
);

CREATE TABLE IF NOT EXISTS analytics.revenue_exposure (
    engagement_id         VARCHAR(20) NOT NULL REFERENCES core.engagements(engagement_id),
    as_of_date            DATE NOT NULL,
    monthly_contract_value NUMERIC(14,2) NOT NULL,
    remaining_months     NUMERIC(8,2) NOT NULL,
    contract_exposure    NUMERIC(16,2) NOT NULL,
    risk_probability     NUMERIC(7,5) NOT NULL,
    risk_adjusted_exposure NUMERIC(16,2) NOT NULL,
    PRIMARY KEY (engagement_id, as_of_date)
);

CREATE INDEX IF NOT EXISTS idx_engagement_client ON core.engagements(client_id);
CREATE INDEX IF NOT EXISTS idx_engagement_talent ON core.engagements(talent_id);
CREATE INDEX IF NOT EXISTS idx_performance_engagement_date ON core.performance_reviews(engagement_id, review_date);
CREATE INDEX IF NOT EXISTS idx_feedback_engagement_date ON core.client_feedback(engagement_id, feedback_date);
CREATE INDEX IF NOT EXISTS idx_checkins_engagement_date ON core.checkins(engagement_id, checkin_date);
CREATE INDEX IF NOT EXISTS idx_predictions_engagement_date ON analytics.risk_predictions(engagement_id, prediction_date);
