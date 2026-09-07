from __future__ import annotations

import os
import streamlit as st

# Bridge Streamlit Cloud secrets -> environment BEFORE the DB layer is imported,
# so core.config picks up DB_URL (Neon/Postgres) on deploy. No-op locally.
try:
    if "DB_URL" in st.secrets:
        os.environ["DB_URL"] = st.secrets["DB_URL"]
except Exception:
    pass

from datetime import date, timedelta
from pathlib import Path
import sys
import json
import pandas as pd
import numpy as np
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base.prescriptive.recommendations import recommend
from core.db import read_sql, exec_sql   # DB-agnostic: SQLite locally, Postgres in the cloud

METRICS = ROOT / "artifacts" / "model" / "metrics.json"

st.set_page_config(
    page_title="Engagement360",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.5rem;}
.metric-card {padding: 0.8rem 1rem; border-radius: 0.8rem; background: rgba(120,120,120,.08);}
.small-muted {font-size: .82rem; opacity: .72;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def portfolio() -> pd.DataFrame:
    return read_sql("""
        WITH h AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY engagement_id ORDER BY as_of_date DESC) rn
            FROM engagement_health
        ),
        r AS (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY engagement_id ORDER BY as_of_date DESC) rn
            FROM risk_predictions
        )
        SELECT h.engagement_id, h.as_of_date, h.behs, h.health_band,
               h.performance_health, h.client_feedback_health, h.milestone_health,
               h.utilisation_health, h.sentiment_health,
               e.client_id, c.client_name, c.industry, e.talent_id, t.talent_name,
               e.role, e.monthly_contract_value, r.risk_probability, r.risk_band,
               x.remaining_months, x.contract_exposure, x.risk_adjusted_exposure
        FROM h
        JOIN engagements e ON e.engagement_id = h.engagement_id
        JOIN clients c ON c.client_id = e.client_id
        JOIN talents t ON t.talent_id = e.talent_id
        LEFT JOIN r ON r.engagement_id = h.engagement_id AND r.rn = 1
        LEFT JOIN revenue_exposure x ON x.engagement_id = h.engagement_id
        WHERE h.rn = 1
    """)


def current_interventions() -> pd.DataFrame:
    return read_sql("SELECT * FROM interventions ORDER BY intervention_date DESC")


def risk_drivers(engagement_id: str) -> str:
    d = read_sql(
        "SELECT top_drivers FROM risk_drivers WHERE engagement_id=:eid ORDER BY as_of_date DESC LIMIT 1",
        eid=engagement_id,
    )
    return str(d.iloc[0]["top_drivers"]) if len(d) else "No material driver narrative available."


def avg_delay(engagement_id: str) -> float:
    x = read_sql("SELECT AVG(delay_days) d FROM project_milestones WHERE engagement_id=:eid", eid=engagement_id)
    return float(x.iloc[0]["d"] or 0)


def avg_rating(engagement_id: str) -> float:
    x = read_sql("SELECT AVG(rating) r FROM client_feedback WHERE engagement_id=:eid", eid=engagement_id)
    return float(x.iloc[0]["r"] or 5)


try:
    df = portfolio()
except Exception as exc:
    st.error(str(exc))
    st.stop()

st.title("Engagement360")
st.caption("AI-Powered Engagement Health, Early-Warning & Revenue Protection Platform")
st.info("Synthetic Bredge-inspired academic dataset — no confidential Bredge/client data used.")

# Sidebar filters
st.sidebar.header("Portfolio filters")
clients = st.sidebar.multiselect("Client", sorted(df.client_name.unique()))
roles = st.sidebar.multiselect("Role", sorted(df.role.unique()))
industries = st.sidebar.multiselect("Industry", sorted(df.industry.unique()))
risk_bands = st.sidebar.multiselect("Risk band", ["Low", "Watch", "Critical"])

filtered = df.copy()
if clients:
    filtered = filtered[filtered.client_name.isin(clients)]
if roles:
    filtered = filtered[filtered.role.isin(roles)]
if industries:
    filtered = filtered[filtered.industry.isin(industries)]
if risk_bands:
    filtered = filtered[filtered.risk_band.isin(risk_bands)]

# Executive KPI strip
crit = int((filtered.risk_band == "Critical").sum())
watch = int((filtered.risk_band == "Watch").sum())
healthy = int((filtered.health_band == "Healthy").sum())
exposure = float(filtered.risk_adjusted_exposure.fillna(0).sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Active engagements", f"{len(filtered):,}")
k2.metric("Healthy", f"{healthy:,}")
k3.metric("Watch", f"{watch:,}")
k4.metric("Critical risk", f"{crit:,}")
k5.metric("Risk-adjusted exposure", f"₦{exposure/1e9:,.2f}B")

# Executive overview
st.divider()
left, right = st.columns([1, 1.5])
with left:
    st.subheader("Portfolio health")
    health = filtered.health_band.value_counts().reindex(["Healthy", "Watch", "Critical"]).fillna(0).reset_index()
    health.columns = ["health_band", "engagements"]
    fig = px.bar(health, x="health_band", y="engagements", text="engagements")
    fig.update_layout(height=330, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Highest-priority engagements")
    top = filtered.sort_values(["risk_probability", "risk_adjusted_exposure"], ascending=False).head(10).copy()
    top["Risk"] = (top.risk_probability.fillna(0) * 100).round(1).astype(str) + "%"
    top["Exposure"] = top.risk_adjusted_exposure.fillna(0).map(lambda x: f"₦{x/1e6:,.2f}M")
    st.dataframe(top[["engagement_id", "client_name", "role", "risk_band", "Risk", "Exposure"]], use_container_width=True, hide_index=True)

# Tabs
portfolio_tab, investigation_tab, interventions_tab, model_tab = st.tabs([
    "Portfolio",
    "Engagement investigation",
    "Interventions",
    "Model & governance",
])

with portfolio_tab:
    st.subheader("Revenue exposure by client")
    client_exp = filtered.groupby("client_name", as_index=False)["risk_adjusted_exposure"].sum().sort_values("risk_adjusted_exposure", ascending=False).head(15)
    client_exp["Exposure (₦M)"] = client_exp.risk_adjusted_exposure / 1e6
    fig = px.bar(client_exp, y="client_name", x="Exposure (₦M)", orientation="h")
    fig.update_layout(height=480, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Risk distribution")
    risk_dist = filtered["risk_probability"].fillna(0)
    fig2 = px.histogram(risk_dist, nbins=20, labels={"value": "Risk probability"})
    fig2.update_layout(height=330)
    st.plotly_chart(fig2, use_container_width=True)

with investigation_tab:
    if filtered.empty:
        st.warning("No engagements match the current filters.")
    else:
        selected = st.selectbox("Select engagement", sorted(filtered.engagement_id.unique()))
        row = filtered[filtered.engagement_id == selected].iloc[0]
        st.caption(f"{row.talent_name} · {row.role} · {row.client_name} · {row.industry}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("BEHS", f"{row.behs:.1f}/100")
        m2.metric("Risk probability", f"{row.risk_probability*100:.1f}%")
        m3.metric("Risk band", str(row.risk_band))
        m4.metric("Risk-adjusted exposure", f"₦{row.risk_adjusted_exposure/1e6:,.2f}M")

        trend = read_sql("""
            SELECT as_of_date, behs, performance_health, client_feedback_health,
                   milestone_health, utilisation_health, sentiment_health
            FROM engagement_health WHERE engagement_id=:eid ORDER BY as_of_date
        """, eid=selected)
        trend["as_of_date"] = pd.to_datetime(trend["as_of_date"])
        tlong = trend.melt(id_vars="as_of_date", var_name="metric", value_name="score")
        fig3 = px.line(tlong, x="as_of_date", y="score", color="metric")
        fig3.update_layout(height=360, yaxis_title="Score")
        st.plotly_chart(fig3, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Top risk drivers")
            for driver in risk_drivers(selected).split(" | "):
                st.markdown(f"- {driver}")
        with c2:
            st.markdown("### Recent client feedback")
            notes = read_sql("""
                SELECT f.feedback_date, f.rating, f.comment, s.sentiment_label, s.issue_category
                FROM client_feedback f
                LEFT JOIN sentiment_scores s
                  ON f.engagement_id=s.engagement_id AND f.feedback_date=s.source_date
                WHERE f.engagement_id=:eid ORDER BY f.feedback_date DESC LIMIT 5
            """, eid=selected)
            st.dataframe(notes, use_container_width=True, hide_index=True)

        st.markdown("### AI-assisted intervention recommendation")
        recs = recommend(
            risk_probability=float(row.risk_probability or 0),
            behs=float(row.behs),
            sentiment_health=float(row.sentiment_health),
            performance_health=float(row.performance_health),
            delay_days=avg_delay(selected),
            feedback_rating=avg_rating(selected),
        )
        for rec in recs:
            st.markdown(f"**{rec.priority} · {rec.action}** — {rec.reason}  ")
            st.caption(f"Owner: {rec.owner} · Suggested action window: {rec.due_days} days")
        st.caption("AI recommendations are decision support only; a manager must review and approve an intervention.")

        st.markdown("### What-if scenario")
        st.caption("Scenario simulation only — not a causal estimate.")
        s1, s2, s3 = st.columns(3)
        perf_uplift = s1.slider("Performance uplift", -10, 15, 0)
        sentiment_uplift = s2.slider("Sentiment uplift", -20, 20, 0)
        delay_reduction = s3.slider("Reduce average delay (days)", 0, 10, 0)
        base_risk = float(row.risk_probability or 0)
        base_score = float(row.behs)
        # Transparent heuristic simulation for the MVP.
        scenario_behs = np.clip(base_score + 0.30*perf_uplift + 0.20*sentiment_uplift + 1.2*delay_reduction, 0, 100)
        scenario_risk = float(np.clip(base_risk - 0.006*(scenario_behs-base_score), 0.01, 0.99))
        w1, w2 = st.columns(2)
        w1.metric("Current model risk", f"{base_risk*100:.1f}%")
        w2.metric("Scenario risk", f"{scenario_risk*100:.1f}%", delta=f"{(scenario_risk-base_risk)*100:+.1f} pp")

with interventions_tab:
    st.subheader("Log an intervention")
    candidates = sorted(filtered.engagement_id.unique()) if len(filtered) else sorted(df.engagement_id.unique())
    selected_i = st.selectbox("Engagement", candidates, key="intervention_engagement")
    rrow = df[df.engagement_id == selected_i].iloc[0]
    recs = recommend(
        risk_probability=float(rrow.risk_probability or 0),
        behs=float(rrow.behs),
        sentiment_health=float(rrow.sentiment_health),
        performance_health=float(rrow.performance_health),
        delay_days=avg_delay(selected_i),
        feedback_rating=avg_rating(selected_i),
    )
    action_options = [r.action for r in recs] + ["Mentoring", "Escalation", "Scope clarification"]
    with st.form("intervention_form"):
        a, b, c = st.columns(3)
        itype = a.selectbox("Intervention type", list(dict.fromkeys(action_options)))
        owner = b.text_input("Owner", "Account Manager")
        priority = c.selectbox("Priority", ["High", "Medium", "Low"])
        due_days = st.number_input("Due within (days)", 1, 60, 7)
        notes = st.text_area("Action notes", "")
        submitted = st.form_submit_button("Log intervention")
    if submitted:
        _today = date.today()
        exec_sql("""
            INSERT INTO interventions
            (engagement_id, intervention_date, intervention_type, owner, priority, status, due_date, completed_date, outcome)
            VALUES (:eid, :today, :itype, :owner, :priority, 'Open', :due, NULL, :notes)
        """, eid=selected_i, today=str(_today), itype=itype, owner=owner,
             priority=priority, due=str(_today + timedelta(days=int(due_days))), notes=notes)
        st.cache_data.clear()
        st.success("Intervention logged to the SQL database.")

    st.subheader("Intervention register")
    ints = current_interventions()
    if len(ints):
        st.dataframe(ints, use_container_width=True, hide_index=True)
        open_ids = ints.loc[ints.status.eq("Open"), "intervention_id"].tolist()
        if open_ids:
            st.markdown("### Close an intervention")
            iid = st.selectbox("Open intervention", open_ids)
            outcome = st.selectbox("Outcome", ["Risk reduced", "Risk unchanged", "Escalated", "Client renewed", "Other"])
            note = st.text_input("Outcome note", "")
            if st.button("Mark completed"):
                exec_sql("UPDATE interventions SET status='Closed', completed_date=:cd, outcome=:oc WHERE intervention_id=:iid", cd=str(date.today()), oc=f"{outcome}: {note}", iid=int(iid))
                st.cache_data.clear()
                st.success("Intervention closed and outcome recorded.")
                st.rerun()

with model_tab:
    st.subheader("Model performance")
    if METRICS.exists():
        metrics = json.loads(METRICS.read_text())
        mdf = pd.DataFrame([
            {"Model": name, "Precision": vals["precision"], "Recall": vals["recall"], "F1": vals["f1"], "ROC-AUC": vals["roc_auc"]}
            for name, vals in metrics["results"].items()
        ])
        st.dataframe(mdf.style.format({c: "{:.3f}" for c in mdf.columns if c != "Model"}), use_container_width=True, hide_index=True)
        selected_model = metrics["selected_model"]
        st.success(f"Primary early-warning model: {selected_model.replace('_', ' ').title()} · intervention threshold = {metrics['band_threshold']:.2f}")
        st.markdown(f"**Critical interpretation:** {selected_model.replace('_', ' ').title()} is selected because recall is prioritised for early warning — catching an at-risk engagement matters more than an occasional false alarm. The precision-recall trade-off is stated openly, not hidden.")

    st.subheader("Governance checklist")
    st.checkbox("Human review required before intervention", value=True, disabled=True)
    st.checkbox("Synthetic academic data / no confidential client records", value=True, disabled=True)
    st.checkbox("Temporal leakage controls applied in modelling", value=True, disabled=True)
    st.checkbox("Model version and decision audit trail retained", value=True, disabled=True)