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

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from base.prescriptive.recommendations import recommend
from core.db import read_sql, exec_sql   # DB-agnostic: SQLite locally, Postgres in the cloud

METRICS = ROOT / "artifacts" / "model" / "metrics.json"

st.set_page_config(page_title="Engagement360", page_icon="📈",
                   layout="wide", initial_sidebar_state="expanded")

# ----------------------------------------------------------------- branding
SKY, SKY_DARK, SKY_LIGHT = "#0EA5E9", "#0369A1", "#7DD3FC"
SKY_SEQ = ["#0EA5E9", "#0284C7", "#38BDF8", "#0369A1", "#7DD3FC", "#075985"]
BAND_COLORS = {"Healthy": "#16A34A", "Low": "#16A34A", "Watch": "#F59E0B", "Critical": "#DC2626"}

LOGO = ('<svg width="58" height="58" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="2" y="2" width="44" height="44" rx="12" fill="#0EA5E9"/>'
        '<path d="M7 27 L17 27 L21 16 L27 33 L31 24 L41 24" fill="none" stroke="#ffffff" '
        'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')

# ----------------------------------------------------------------- theme
if "theme" not in st.session_state:
    st.session_state.theme = "Light"


def inject_css(theme: str) -> dict:
    if theme == "Dark":
        bg, panel, card, text, border, muted = "#0B1220", "#0F1B2D", "#12203A", "#E2E8F0", "#1E3A5F", "#94A3B8"
        template = "plotly_dark"
    else:
        bg, panel, card, text, border, muted = "#F5FAFF", "#FFFFFF", "#FFFFFF", "#0F172A", "#DBEAFE", "#64748B"
        template = "plotly_white"
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background:{bg}; color:{text}; }}
    [data-testid="stHeader"] {{ background:transparent; }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] * {{ color:{text}; }}
    [data-testid="stSidebar"] {{ background:{panel}; border-right:1px solid {border}; }}
    .block-container {{ padding-top:1.1rem; }}
    h1,h2,h3,h4,p,label,span {{ color:{text}; }}
    .brandbar {{ display:flex; align-items:center; gap:14px; margin-bottom:2px; }}
    .brandbar > div {{ display:flex; flex-direction:column; justify-content:center; }}
    .brandbar .title {{ font-size:1.55rem; font-weight:800; line-height:1.1; color:{text}; }}
    .brandbar .sub {{ font-size:.85rem; color:{muted}; }}
    .kpi {{ border-radius:14px; padding:14px 16px; background:{card};
            border:1px solid {border}; border-left:6px solid var(--accent,{SKY}); }}
    .kpi .lab {{ font-size:.76rem; color:{muted}; margin-bottom:4px; letter-spacing:.02em; }}
    .kpi .val {{ font-size:1.5rem; font-weight:800; }}
    .stFormSubmitButton>button, div.stButton>button {{ border-radius:10px; }}
    .stFormSubmitButton>button *, div.stButton>button * {{ color:#0F172A !important; }}
    div.stButton>button[kind="primary"] *, .stFormSubmitButton>button[kind="primary"] * {{ color:#ffffff !important; }}
    .st-key-logincard {{ border:1.5px solid #0EA5E9 !important; border-radius:16px; padding:16px 20px; }}
    [data-testid="stToolbar"] svg, [data-testid="stToolbarActions"] svg,
    [data-testid="stToolbar"] a, [data-testid="stToolbar"] button {{ color:{text} !important; fill:{text} !important; }}
    </style>""", unsafe_allow_html=True)
    return {"template": template, "muted": muted}


# sidebar top: logo + theme toggle (available before and after login)
_sidebar_logo = LOGO.replace('width="58" height="58"', 'width="34" height="34"')
st.sidebar.markdown(
    f'<div class="brandbar" style="margin-top:-12px;">{_sidebar_logo}'
    f'<div class="title" style="font-size:1.1rem">Engagement360</div></div>',
    unsafe_allow_html=True)
theme = st.sidebar.radio("Theme", ["Light", "Dark"], horizontal=True,
                         index=0 if st.session_state.theme == "Light" else 1)
st.session_state.theme = theme
THEME = inject_css(theme)


def style_fig(fig, h=330):
    fig.update_layout(template=THEME["template"], height=h, colorway=SKY_SEQ,
                      margin=dict(l=10, r=10, t=36, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def header():
    st.markdown(
        f'<div class="brandbar" style="margin-top:-14px;">{LOGO}<div><div class="title">Engagement360</div>'
        f'<div class="sub">AI-Powered Engagement Health, Early-Warning & Revenue Protection</div>'
        f'</div></div>', unsafe_allow_html=True)


# ----------------------------------------------------------------- auth
def account_manager_ids() -> list[str]:
    try:
        d = read_sql("SELECT DISTINCT account_manager_id AS am FROM clients ORDER BY account_manager_id")
        return d["am"].astype(str).tolist()
    except Exception:
        return []


ADMIN_PW = "admin123"
try:
    ADMIN_PW = st.secrets["auth"]["admin_password"]
except Exception:
    pass


def login_gate():
    if st.session_state.get("auth"):
        return
    header()
    _, mid, _ = st.columns([1, 1.4, 1])
    box = mid.container(border=True, key="logincard")
    box.markdown("#### Sign in")
    role = box.radio("Access level", ["Administrator", "Account Manager", "Guest (view only)"])
    if role == "Administrator":
        pw = box.text_input("Admin password", type="password")
        if box.button("Sign in", type="primary", use_container_width=True):
            if pw == ADMIN_PW:
                st.session_state.auth = {"role": "Administrator", "am": None, "name": "Administrator"}
                st.rerun()
            else:
                box.error("Incorrect password.")
    elif role == "Account Manager":
        ams = account_manager_ids()
        am = box.selectbox("Your account-manager ID", ams) if ams else None
        if box.button("Sign in", type="primary", use_container_width=True):
            st.session_state.auth = {"role": "Account Manager", "am": str(am), "name": f"Account Manager {am}"}
            st.rerun()
    else:
        if box.button("Continue as guest", type="primary", use_container_width=True):
            st.session_state.auth = {"role": "Guest", "am": None, "name": "Guest"}
            st.rerun()
    box.caption("Demo access - synthetic data. Administrator password: **admin123**. "
                "Account managers sign in by ID and see only their own clients. "
                "Guests view the full portfolio read-only.")
    st.stop()


login_gate()
AUTH = st.session_state.auth
CAN_WRITE = AUTH["role"] in ("Administrator", "Account Manager")

# sidebar: signed-in identity + logout
st.sidebar.divider()
st.sidebar.markdown(f"**Signed in**  \n{AUTH['name']}  \n`{AUTH['role']}`")
if st.sidebar.button("Log out"):
    del st.session_state["auth"]
    st.rerun()

st.sidebar.divider()
auto = st.sidebar.checkbox("Auto-refresh every 5 min", value=True)
if auto and st_autorefresh is not None:
    st_autorefresh(interval=5 * 60 * 1000, key="auto_refresh")
if st.sidebar.button("Refresh now"):
    st.cache_data.clear()
    st.rerun()


# ----------------------------------------------------------------- data
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
               e.client_id, c.client_name, c.industry, c.account_manager_id,
               e.talent_id, t.talent_name, e.role, e.monthly_contract_value,
               r.risk_probability, r.risk_band,
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
    d = read_sql("SELECT top_drivers FROM risk_drivers WHERE engagement_id=:eid ORDER BY as_of_date DESC LIMIT 1",
                 eid=engagement_id)
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
    header()
    st.error(str(exc))
    st.stop()

# role-based access: an account manager sees only their own clients
if AUTH["role"] == "Account Manager":
    df = df[df.account_manager_id.astype(str) == AUTH["am"]].copy()

header()

# ----------------------------------------------------------------- filters
st.sidebar.header("Portfolio filters")
clients = st.sidebar.multiselect("Client", sorted(df.client_name.unique()), key="Client")
roles = st.sidebar.multiselect("Role", sorted(df.role.unique()), key="Role")
industries = st.sidebar.multiselect("Industry", sorted(df.industry.unique()), key="Industry")
risk_bands = st.sidebar.multiselect("Risk band", ["Low", "Watch", "Critical"], key="Risk band")
if st.sidebar.button("Reset filters"):
    for _k in ("Client", "Role", "Industry", "Risk band"):
        st.session_state.pop(_k, None)
    st.rerun()

filtered = df.copy()
if clients:
    filtered = filtered[filtered.client_name.isin(clients)]
if roles:
    filtered = filtered[filtered.role.isin(roles)]
if industries:
    filtered = filtered[filtered.industry.isin(industries)]
if risk_bands:
    filtered = filtered[filtered.risk_band.isin(risk_bands)]

# ----------------------------------------------------------------- KPIs
crit = int((filtered.risk_band == "Critical").sum())
watch = int((filtered.risk_band == "Watch").sum())
healthy = int((filtered.health_band == "Healthy").sum())
exposure = float(filtered.risk_adjusted_exposure.fillna(0).sum())


def kpi(col, label, value, accent):
    col.markdown(f'<div class="kpi" style="--accent:{accent}"><div class="lab">{label}</div>'
                 f'<div class="val" style="color:{accent}">{value}</div></div>', unsafe_allow_html=True)


k1, k2, k3, k4, k5 = st.columns(5)
kpi(k1, "ACTIVE ENGAGEMENTS", f"{len(filtered):,}", SKY)
kpi(k2, "HEALTHY", f"{healthy:,}", BAND_COLORS["Healthy"])
kpi(k3, "WATCH", f"{watch:,}", BAND_COLORS["Watch"])
kpi(k4, "CRITICAL RISK", f"{crit:,}", BAND_COLORS["Critical"])
kpi(k5, "REVENUE-AT-RISK", f"₦{exposure/1e9:,.2f}B", SKY_DARK)

st.divider()
left, right = st.columns([1, 1.5])
with left:
    st.subheader("Portfolio health")
    health = filtered.health_band.value_counts().reindex(["Healthy", "Watch", "Critical"]).fillna(0).reset_index()
    health.columns = ["health_band", "engagements"]
    fig = px.bar(health, x="health_band", y="engagements", text="engagements",
                 color="health_band", color_discrete_map=BAND_COLORS)
    style_fig(fig, 330).update_layout(showlegend=False, xaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Highest-priority engagements")
    top = filtered.sort_values(["risk_probability", "risk_adjusted_exposure"], ascending=False).head(10).copy()
    top["Risk"] = (top.risk_probability.fillna(0) * 100).round(1).astype(str) + "%"
    top["Exposure"] = top.risk_adjusted_exposure.fillna(0).map(lambda x: f"₦{x/1e6:,.2f}M")
    show = top[["engagement_id", "client_name", "role", "risk_band", "Risk", "Exposure"]]

    def _band_style(v):
        c = BAND_COLORS.get(v, THEME["muted"])
        return f"background-color:{c}22; color:{c}; font-weight:700;"
    try:
        show = show.style.map(_band_style, subset=["risk_band"])
    except Exception:
        pass
    st.dataframe(show, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------- tabs
portfolio_tab, investigation_tab, interventions_tab, model_tab = st.tabs(
    ["Portfolio", "Engagement investigation", "Interventions", "Model & governance"])

with portfolio_tab:
    st.subheader("Revenue exposure by client")
    client_exp = (filtered.groupby("client_name", as_index=False)["risk_adjusted_exposure"].sum()
                  .sort_values("risk_adjusted_exposure", ascending=False).head(15))
    client_exp["Exposure (₦M)"] = client_exp.risk_adjusted_exposure / 1e6
    fig = px.bar(client_exp, y="client_name", x="Exposure (₦M)", orientation="h")
    style_fig(fig, 480).update_layout(yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Risk distribution")
    fig2 = px.histogram(filtered["risk_probability"].fillna(0), nbins=20, labels={"value": "Risk probability"})
    style_fig(fig2, 330).update_layout(showlegend=False)
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
        m2.metric("Risk probability", f"{(row.risk_probability or 0)*100:.1f}%")
        m3.metric("Risk band", str(row.risk_band))
        m4.metric("Revenue-at-Risk", f"₦{(row.risk_adjusted_exposure or 0)/1e6:,.2f}M")

        trend = read_sql("""
            SELECT as_of_date, behs, performance_health, client_feedback_health,
                   milestone_health, utilisation_health, sentiment_health
            FROM engagement_health WHERE engagement_id=:eid ORDER BY as_of_date
        """, eid=selected)
        trend["as_of_date"] = pd.to_datetime(trend["as_of_date"])
        tlong = trend.melt(id_vars="as_of_date", var_name="metric", value_name="score")
        fig3 = px.line(tlong, x="as_of_date", y="score", color="metric")
        style_fig(fig3, 360).update_layout(yaxis_title="Score")
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
            risk_probability=float(row.risk_probability or 0), behs=float(row.behs),
            sentiment_health=float(row.sentiment_health), performance_health=float(row.performance_health),
            delay_days=avg_delay(selected), feedback_rating=avg_rating(selected))
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
        scenario_behs = np.clip(base_score + 0.30*perf_uplift + 0.20*sentiment_uplift + 1.2*delay_reduction, 0, 100)
        scenario_risk = float(np.clip(base_risk - 0.006*(scenario_behs-base_score), 0.01, 0.99))
        w1, w2 = st.columns(2)
        w1.metric("Current model risk", f"{base_risk*100:.1f}%")
        w2.metric("Scenario risk", f"{scenario_risk*100:.1f}%", delta=f"{(scenario_risk-base_risk)*100:+.1f} pp")

with interventions_tab:
    if not CAN_WRITE:
        st.info("View-only access. Sign in as an Administrator or an Account Manager to log interventions.")
    else:
        st.subheader("Log an intervention")
        candidates = sorted(filtered.engagement_id.unique()) if len(filtered) else sorted(df.engagement_id.unique())
        if candidates:
            selected_i = st.selectbox("Engagement", candidates, key="intervention_engagement")
            rrow = df[df.engagement_id == selected_i].iloc[0]
            recs = recommend(
                risk_probability=float(rrow.risk_probability or 0), behs=float(rrow.behs),
                sentiment_health=float(rrow.sentiment_health), performance_health=float(rrow.performance_health),
                delay_days=avg_delay(selected_i), feedback_rating=avg_rating(selected_i))
            action_options = [r.action for r in recs] + ["Mentoring", "Escalation", "Scope clarification"]
            with st.form("intervention_form"):
                a, b, c = st.columns(3)
                itype = a.selectbox("Intervention type", list(dict.fromkeys(action_options)))
                owner = b.text_input("Owner", AUTH["name"])
                priority = c.selectbox("Priority", ["High", "Medium", "Low"])
                due_days = st.number_input("Due within (days)", 1, 60, 7)
                notes = st.text_area("Action notes", "")
                submitted = st.form_submit_button("Log intervention", type="primary")
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
        if CAN_WRITE and "intervention_id" in ints.columns:
            open_ids = ints.loc[ints.status.eq("Open"), "intervention_id"].tolist()
            if open_ids:
                st.markdown("### Close an intervention")
                iid = st.selectbox("Open intervention", open_ids)
                outcome = st.selectbox("Outcome", ["Risk reduced", "Risk unchanged", "Escalated", "Client renewed", "Other"])
                note = st.text_input("Outcome note", "")
                if st.button("Mark completed"):
                    exec_sql("UPDATE interventions SET status='Closed', completed_date=:cd, outcome=:oc WHERE intervention_id=:iid",
                             cd=str(date.today()), oc=f"{outcome}: {note}", iid=int(iid))
                    st.cache_data.clear()
                    st.success("Intervention closed and outcome recorded.")
                    st.rerun()
    else:
        st.caption("No interventions recorded yet.")

with model_tab:
    st.subheader("Model performance")
    if METRICS.exists():
        metrics = json.loads(METRICS.read_text())
        mdf = pd.DataFrame([
            {"Model": name, "Precision": vals["precision"], "Recall": vals["recall"],
             "F1": vals["f1"], "ROC-AUC": vals["roc_auc"]}
            for name, vals in metrics["results"].items()])
        st.dataframe(mdf.style.format({c: "{:.3f}" for c in mdf.columns if c != "Model"}),
                     use_container_width=True, hide_index=True)
        selected_model = metrics["selected_model"]
        st.success(f"Primary early-warning model: {selected_model.replace('_', ' ').title()} · "
                   f"intervention threshold = {metrics['band_threshold']:.2f}")
        st.markdown(f"**Critical interpretation:** {selected_model.replace('_', ' ').title()} is selected "
                    "because recall is prioritised for early warning — catching an at-risk engagement matters "
                    "more than an occasional false alarm. The precision-recall trade-off is stated openly, not hidden.")

    st.subheader("Governance checklist")
    st.checkbox("Human review required before intervention", value=True, disabled=True)
    st.checkbox("Role-based access (admin / account manager / guest)", value=True, disabled=True)
    st.checkbox("Synthetic academic data / no confidential client records", value=True, disabled=True)
    st.checkbox("Temporal leakage controls applied in modelling", value=True, disabled=True)
    st.checkbox("Model version and decision audit trail retained", value=True, disabled=True)