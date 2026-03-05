import streamlit as st
import httpx

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="CodeAtlas",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* Hide sidebar */
    [data-testid="stSidebar"] { display: none; }
    section[data-testid="stSidebarNav"] { display: none; }

    /* Black background */
    .stApp { background-color: #0a0a0f; }
    header[data-testid="stHeader"] { background-color: #0a0a0f; }

    /* ── Headings ── */
    .hero-title {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: 2px;
        background: linear-gradient(135deg, #7c6bf0 0%, #a855f7 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 0.1rem;
        margin-bottom: -1rem;
        line-height: 1.1;
    }
    .hero-subtitle {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 2px;
        background: linear-gradient(135deg, #7c6bf0 0%, #a855f7 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: -1rem;
        margin-bottom: 0.3rem;
    }
    .hero-desc {
        text-align: center;
        color: #ffffff;
        font-size: 0.95rem;
        margin-bottom: 2.5rem;
    }

    /* ── Search bar area ── */
    .search-container {
        max-width: 750px;
        margin: 0 auto 2rem auto;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .stTextInput > div > div > input {
        background-color: #12121a !important;
        color: #ccc !important;
        border: 1px solid #2a2a40 !important;
        border-radius: 30px !important;
        padding: 0.8rem 1.2rem 0.8rem 2.8rem !important;
        font-size: 0.95rem !important;
    }

    /* Ingest button styling */
    button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899) !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    /* ── Feature Buttons (styled as animated cards) ── */
    .feature-btn-row button {
        background: linear-gradient(145deg, #13131f, #1a1a2e) !important;
        border: 1px solid #2a2a40 !important;
        border-radius: 16px !important;
        color: #e0e0f0 !important;
        padding: 2rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        min-height: 180px !important;
        white-space: pre-line !important;
        line-height: 1.8 !important;
    }
    .feature-btn-row button:hover {
        border-color: #555 !important;
        transform: translateY(-4px) !important;
        box-shadow: 0 8px 30px rgba(100, 100, 200, 0.15) !important;
    }
    .feature-btn-row button p {
        font-size: 1rem !important;
        white-space: pre-line !important;
    }

    /* ── Content area ── */
    pre {
        background-color: #0d1117 !important;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
    }
    .status-success {
        background: #1a3a2a; color: #4ade80;
        padding: 0.5rem 1.2rem; border-radius: 20px;
        display: inline-block; font-size: 0.9rem;
    }
    .status-error {
        background: #3a1a1a; color: #f87171;
        padding: 0.5rem 1.2rem; border-radius: 20px;
        display: inline-block; font-size: 0.9rem;
    }
    .stTextArea textarea {
        background-color: #12121a !important;
        color: #e0e0ff !important;
        border: 1px solid #2a2a40 !important;
        border-radius: 12px;
    }
    div[data-testid="stExpander"] {
        background: #12121a;
        border: 1px solid #2a2a40;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

API_BASE = "http://localhost:8000"

# ── Session state ────────────────────────────────────────────
if "active_view" not in st.session_state:
    st.session_state.active_view = None
if "ingested" not in st.session_state:
    st.session_state.ingested = False
if "repo_name" not in st.session_state:
    st.session_state.repo_name = ""

# ── Hero Heading ─────────────────────────────────────────────
st.markdown('<h1 class="hero-title">CodeAtlas</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Intelligent Codebase Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="hero-desc">Analyze any GitHub repository with AI-powered insights</p>', unsafe_allow_html=True)

# ── Search Bar ───────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        label_visibility="collapsed",
    )
with col_btn:
    ingest_clicked = st.button("🔗 Ingest", use_container_width=True, type="primary")

# ── Handle ingestion ─────────────────────────────────────────
if ingest_clicked and repo_url:
    with st.spinner("Ingesting repository... This may take a minute for large repos."):
        try:
            resp = httpx.post(
                f"{API_BASE}/ingest",
                json={"repo_url": repo_url},
                timeout=300.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.ingested = True
                st.session_state.repo_name = data.get("repo", "")
                st.markdown(
                    f'<span class="status-success">✅ Successfully ingested '
                    f'<b>{data["repo"]}</b> — {data["files_processed"]} files, '
                    f'{data["chunks_created"]} chunks</span>',
                    unsafe_allow_html=True,
                )
            else:
                err = resp.json().get("detail", resp.text)
                st.markdown(f'<span class="status-error">❌ {err}</span>', unsafe_allow_html=True)
        except httpx.ConnectError:
            st.markdown(
                '<span class="status-error">❌ Cannot connect to backend. '
                'Make sure FastAPI is running on port 8000.</span>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.markdown(f'<span class="status-error">❌ {e}</span>', unsafe_allow_html=True)

# ── Feature Buttons (styled as animated cards) ────────────────
st.markdown("")
st.markdown('<div class="feature-btn-row">', unsafe_allow_html=True)
b1, b2, b3, b4 = st.columns(4)
with b1:
    if st.button("🔍\n\nAsk Question\n\nGet answers to\ncode-related queries", use_container_width=True, key="btn_qa"):
        st.session_state.active_view = "qa"
with b2:
    if st.button("🏗️\n\nArchitecture Map\n\nVisualize the structure\nof the repository", use_container_width=True, key="btn_arch"):
        st.session_state.active_view = "architecture"
with b3:
    if st.button("🔗\n\nDependency Graph\n\nExplore the relationships\nbetween files", use_container_width=True, key="btn_dep"):
        st.session_state.active_view = "dependencies"
with b4:
    if st.button("📝\n\nSummaries\n\nGenerate summaries at\nmultiple levels", use_container_width=True, key="btn_sum"):
        st.session_state.active_view = "summaries"
st.markdown('</div>', unsafe_allow_html=True)


# ── Content Area ─────────────────────────────────────────────
st.markdown("")
view = st.session_state.active_view

# ────────── Q&A View ──────────
if view == "qa":
    st.markdown("### 🔍 Ask a Question About the Codebase")
    question = st.text_area(
        "Your question",
        placeholder="e.g. Where is authentication implemented?",
        height=100,
        label_visibility="collapsed",
    )
    if st.button("Get Answer", key="qa_submit"):
        if not st.session_state.ingested:
            st.warning("Please ingest a repository first.")
        elif question:
            with st.spinner("Thinking..."):
                try:
                    resp = httpx.post(
                        f"{API_BASE}/query",
                        json={"question": question},
                        timeout=120.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown("#### 💡 Answer")
                        st.markdown(data["answer"])
                        if data.get("sources"):
                            st.markdown("#### 📁 Relevant Files")
                            for src in data["sources"]:
                                st.code(src, language="text")
                    else:
                        st.error(resp.json().get("detail", "Error"))
                except Exception as e:
                    st.error(f"Error: {e}")

# ────────── Architecture Map View ──────────
elif view == "architecture":
    st.markdown("### 🏗️ Repository Architecture Map")
    if not st.session_state.ingested:
        st.info("Ingest a repository to see its architecture.")
    else:
        try:
            resp = httpx.get(
                f"{API_BASE}/architecture/{st.session_state.repo_name}",
                timeout=30.0,
            )
            if resp.status_code == 200:
                tree_str = resp.json().get("tree", "")
                st.code(tree_str, language="text")
            else:
                st.error(resp.json().get("detail", "Error"))
        except Exception as e:
            st.error(f"Error: {e}")

# ────────── Dependency Graph View ──────────
elif view == "dependencies":
    st.markdown("### 🔗 Dependency Graph")
    if not st.session_state.ingested:
        st.info("Ingest a repository to see the dependency graph.")
    else:
        try:
            resp = httpx.get(
                f"{API_BASE}/dependencies/{st.session_state.repo_name}",
                timeout=30.0,
            )
            if resp.status_code == 200:
                graph_data = resp.json().get("graph", {})
                nodes = graph_data.get("nodes", [])
                edges = graph_data.get("edges", [])

                if nodes:
                    import plotly.graph_objects as go
                    import networkx as nx
                    import os

                    G = nx.DiGraph()
                    for n in nodes:
                        G.add_node(n["id"])
                    for e in edges:
                        G.add_edge(e["source"], e["target"])

                    pos = nx.spring_layout(G, k=2, seed=42)
                    edge_x, edge_y = [], []
                    for u, v in G.edges():
                        x0, y0 = pos[u]
                        x1, y1 = pos[v]
                        edge_x.extend([x0, x1, None])
                        edge_y.extend([y0, y1, None])

                    edge_trace = go.Scatter(
                        x=edge_x, y=edge_y,
                        line=dict(width=1, color="#667eea"),
                        hoverinfo="none", mode="lines",
                    )
                    node_x = [pos[n][0] for n in G.nodes()]
                    node_y = [pos[n][1] for n in G.nodes()]
                    node_text = [os.path.basename(n) for n in G.nodes()]
                    conns = [G.degree(n) for n in G.nodes()]

                    node_trace = go.Scatter(
                        x=node_x, y=node_y,
                        mode="markers+text",
                        text=node_text,
                        textposition="top center",
                        textfont=dict(size=10, color="white"),
                        hovertext=list(G.nodes()),
                        hoverinfo="text",
                        marker=dict(
                            size=12, color=conns,
                            colorscale="Viridis",
                            colorbar=dict(title="Connections"),
                            line=dict(width=1, color="#333"),
                        ),
                    )

                    fig = go.Figure(
                        data=[edge_trace, node_trace],
                        layout=go.Layout(
                            showlegend=False, hovermode="closest",
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            plot_bgcolor="#0a0a0f",
                            paper_bgcolor="#0a0a0f",
                            font=dict(color="white"),
                            margin=dict(l=20, r=20, t=20, b=20),
                            height=600,
                        ),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No dependency connections found.")
            else:
                st.error(resp.json().get("detail", "Error"))
        except Exception as e:
            st.error(f"Error: {e}")

# ────────── Summaries View ──────────
elif view == "summaries":
    st.markdown("### 📝 Multi-Level Code Summaries")
    if not st.session_state.ingested:
        st.info("Ingest a repository to see summaries.")
    else:
        try:
            resp = httpx.get(
                f"{API_BASE}/summaries/{st.session_state.repo_name}",
                timeout=30.0,
            )
            if resp.status_code == 200:
                sums = resp.json().get("summaries", {})

                st.markdown("#### 🏛️ Repository Summary")
                st.info(sums.get("repo", "N/A"))

                st.markdown("#### 📂 Folder Summaries")
                for folder, summary in sums.get("folders", {}).items():
                    with st.expander(f"📁 {folder}/"):
                        st.write(summary)

                st.markdown("#### 📄 File Summaries")
                for file, summary in sums.get("files", {}).items():
                    with st.expander(f"📄 {file}"):
                        st.write(summary)

                st.markdown("#### ⚙️ Function Summaries")
                for func, summary in sums.get("functions", {}).items():
                    with st.expander(f"⚙️ {func}"):
                        st.write(summary)
            else:
                st.error(resp.json().get("detail", "Error"))
        except Exception as e:
            st.error(f"Error: {e}")
