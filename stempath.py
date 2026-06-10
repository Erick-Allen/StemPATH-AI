from html import escape

import streamlit as st

from src.core import StemPathCore


st.set_page_config(
    page_title="StemPATH-AI",
    layout="wide",
)

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] {
        width: 330px !important;
    }

    section[data-testid="stSidebar"] * {
        font-size: 14px;
    }

    .career-preview {
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 12px;
        padding: 12px;
        margin-top: 10px;
        background: rgba(255,255,255,0.045);
    }

    .career-title {
        font-size: 1.05rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .career-description {
        font-size: 0.85rem;
        line-height: 1.5;
        margin-bottom: 12px;

        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .section-label {
        font-size: 0.78rem;
        font-weight: 800;
        margin-top: 10px;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .pill {
        display: inline-block;
        padding: 5px 9px;
        margin: 3px 3px 3px 0;
        border-radius: 999px;
        background: rgba(255,255,255,0.11);
        font-size: 0.78rem;
        line-height: 1.2;
    }

    .muted {
        font-size: 0.82rem;
    }

        .result-card {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 16px;
        background: var(--secondary-background-color);
    }

    .result-group {
        margin-bottom: 14px;
    }

    .result-group:last-child {
        margin-bottom: 0;
    }

    .result-label {
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.65;
        margin-bottom: 2px;
    }

    .result-title {
        font-size: 1.45rem;
        font-weight: 800;
        margin-bottom: 14px;
        color: var(--text-color);
    }

    .result-value {
        font-size: 0.95rem;
        line-height: 1.45;
        color: var(--text-color);
        margin: 0;
    }

    .score {
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-color);
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def load_core():
    core = StemPathCore()
    core.ensure_ready()
    return core


def shorten(text: str, limit: int = 170) -> str:
    if not text:
        return "No description available."

    if len(text) <= limit:
        return text

    return text[:limit].rsplit(" ", 1)[0] + "..."


def render_pills(items: list[str], limit: int = 3) -> str:
    if not items:
        return '<span class="muted">No data found.</span>'

    return " ".join(
        f'<span class="pill">{escape(item)}</span>'
        for item in items[:limit]
    )


def render_career_preview(career_profile: dict) -> None:
    graph = career_profile.get("graph_context", {})

    domains = graph.get("domains", [])
    skills = graph.get("skills", [])
    technologies = graph.get("technologies", [])
    tasks = graph.get("tasks", [])
    knowledge = graph.get("knowledge", [])

    domain = domains[0] if domains else "Uncategorized"
    description = shorten(career_profile.get("description", ""))

    card_html = (
        '<div class="career-preview">'
        f'<div class="career-title">{escape(career_profile["title"])}</div>'
        f'<div class="career-description">{escape(description)}</div>'
        '<div class="section-label">Domain</div>'
        f'<span class="pill">{escape(domain)}</span>'
        '<div class="section-label">Top Skills</div>'
        f'{render_pills(skills, limit=3)}'
        '<div class="section-label">Common Technologies</div>'
        f'{render_pills(technologies, limit=3)}'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)


def render_list(title: str, items: list[str], limit: int = 8) -> None:
    st.markdown(f"#### {title}")

    if not items:
        st.caption("No data found.")
        return

    for item in items[:limit]:
        st.markdown(f"- {item}")


core = load_core()

with st.sidebar:
    st.header("Career Explorer")
    st.caption("Search careers loaded from the O*NET graph.")

    career_options = core.list_career_options(limit=200)
    career_titles = [career["title"] for career in career_options]

    selected_title = st.selectbox(
        "Search or select a career",
        career_titles,
    )

    selected_career = next(
        career for career in career_options if career["title"] == selected_title
    )

    career_profile = core.get_career_profile(selected_career["key"])

    if career_profile:
        render_career_preview(career_profile)

    st.divider()

    st.header("Example Questions")

    example = st.radio(
        "Choose a starting point",
        [
            "What careers use Python and SQL?",
            "What STEM jobs involve cybersecurity?",
            "Which careers involve data analysis?",
            "Which roles focus on AI?",
            "What careers involve engineering and problem solving?",
        ],
    )


st.title("StemPATH-AI")
st.subheader("GraphRAG STEM Career Research Assistant")

st.write(
    "Explore STEM careers through O*NET data."
)


st.divider()

question = st.text_input(
    "Ask a STEM career question",
    value=example,
)

search = st.button("Search careers", type="primary")

if search and question.strip():
    with st.spinner("Searching career documents and graph context..."):
        answer, results = core.query(question)

    if not answer:
        st.error("No relevant career data found.")
        st.stop()

    top_result = results[0]
    graph = top_result.get("graph_context", {})

    st.markdown("### Generated Answer")

    with st.container(border=True):
        st.markdown(answer)

    st.divider()

    domains = graph.get("domains", [])
    skills = graph.get("skills", [])
    technologies = graph.get("technologies", [])
    tasks = graph.get("tasks", [])

    domain_text = domains[0] if domains else "Uncategorized"
    skill_text = ", ".join(skills[:4]) if skills else "No skills found"
    tech_text = ", ".join(technologies[:4]) if technologies else "No technologies found"
    task_text = tasks[0] if tasks else "No task data found"

    st.markdown("### Top Match")

    top_match_html = (
        '<div class="result-card">'
        '<div class="result-label">Matched Occupation</div>'
        f'<div class="result-title">{escape(top_result["title"])}</div>'
        '<div class="result-label">Similarity Score</div>'
        f'<div class="score">{top_result["score"]:.4f}</div>'
        '</div>'
    )

    st.markdown(top_match_html, unsafe_allow_html=True)

    st.markdown("### Career Summary")

    summary_html = (
        '<div class="result-card">'
        '<div class="result-group">'
        '<div class="result-label">Domain</div>'
        f'<div class="result-value">{escape(domain_text)}</div>'
        '</div>'
        '<div class="result-group">'
        '<div class="result-label">Relevant Skills</div>'
        f'<div class="result-value">{escape(skill_text)}</div>'
        '</div>'
        '<div class="result-group">'
        '<div class="result-label">Common Technologies</div>'
        f'<div class="result-value">{escape(tech_text)}</div>'
        '</div>'
        '<div class="result-group">'
        '<div class="result-label">Representative Task</div>'
        f'<div class="result-value">{escape(task_text)}</div>'
        '</div>'
        '</div>'
    )

    st.markdown(summary_html, unsafe_allow_html=True)

    st.divider()

    st.markdown("### Top Career Matches")

    for result in results:
        with st.container(border=True):
            st.markdown(f"**{result['title']}**")
            st.caption(f"Similarity score: {result['score']:.4f}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Skills", "Technologies", "Tasks", "Knowledge Areas", "Retrieved Document"]
    )

    with tab1:
        render_list("Related Skills", graph.get("skills", []), limit=10)

    with tab2:
        render_list("Related Technologies", graph.get("technologies", []), limit=10)

    with tab3:
        render_list("Representative Tasks", graph.get("tasks", []), limit=6)

    with tab4:
        render_list("Knowledge Areas", graph.get("knowledge", []), limit=10)

    with tab5:
        st.write(top_result["content"])