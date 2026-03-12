import re
from io import BytesIO

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

from utils.agent_utils import run_compliance_agent


st.set_page_config(
    page_title="AI Compliance Dashboard",
    page_icon="🛡️",
    layout="wide"
)


def extract_score(text):
    match = re.search(r"Overall Compliance Score:\s*([0-9]+)%", text)
    if match:
        return int(match.group(1))
    return None


def extract_section(text, section_name):
    pattern = rf"{section_name}:\s*(.*?)(?=\n[A-Z][A-Za-z\s\-]+:|\Z)"
    match = re.search(pattern, text, re.S)
    if match:
        return match.group(1).strip()
    return ""


def count_bullets(section_text):
    if not section_text:
        return 0
    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    return sum(1 for line in lines if line.startswith("-") or line.startswith("•"))


def get_status(score):
    if score is None:
        return "Not Available"
    if score >= 80:
        return "High Compliance"
    if score >= 60:
        return "Moderate Compliance"
    return "Low Compliance"


def render_score_bar(score):
    if score is None:
        st.progress(0)
        return
    st.progress(score / 100)


def generate_pdf_report(
    score,
    status,
    summary,
    compliant,
    partially_compliant,
    non_compliant,
    recommendations,
    full_report
):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        spaceAfter=16
    )

    section_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        spaceBefore=12,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        leading=16,
        spaceAfter=6
    )

    story = []

    story.append(Paragraph("AI Internal Audit Compliance Report", title_style))
    story.append(Paragraph(f"<b>Overall Compliance Score:</b> {score}%" if score is not None else "<b>Overall Compliance Score:</b> N/A", body_style))
    story.append(Paragraph(f"<b>Status:</b> {status}", body_style))
    story.append(Spacer(1, 12))

    sections = [
        ("Summary", summary),
        ("Compliant Areas", compliant),
        ("Partially Compliant Areas", partially_compliant),
        ("Non-Compliant Areas", non_compliant),
        ("Recommendations", recommendations),
        ("Full Compliance Report", full_report),
    ]

    for title, content in sections:
        story.append(Paragraph(title, section_style))
        if content:
            for line in content.split("\n"):
                line = line.strip()
                if line:
                    story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph("No content available.", body_style))
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer


st.markdown(
    """
    <style>
    .main-title {
        font-size: 36px;
        font-weight: 800;
        margin-bottom: 6px;
        text-align: center;
    }

    .sub-title {
        color: #9ca3af;
        font-size: 16px;
        margin-bottom: 26px;
        text-align: center;
    }

    .card {
        background-color: #0f172a;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 18px;
        margin-bottom: 16px;
    }

    .result-box {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.20);
    }

    .small-note {
        color: #9ca3af;
        font-size: 13px;
    }

    .section-title {
        text-align: center;
        font-size: 22px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    .white-line {
        height: 3px;
        background-color: #e5e7eb;
        border-radius: 999px;
        margin: 8px 0 18px 0;
        width: 100%;
    }

    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 14px;
        border-radius: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="main-title">🛡️ AI Internal Audit Compliance Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Compare a mother policy against an internal policy, retrieve relevant evidence, and generate a structured compliance report.</div>',
    unsafe_allow_html=True
)

st.markdown("<div class='section-title'>Workflow</div>", unsafe_allow_html=True)
st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

wf1, wf2, wf3 = st.columns(3)

with wf1:
    st.info("**1. Upload Policies**\n\nUpload the mother policy and the internal policy in PDF format.")

with wf2:
    st.info("**2. Analyze Compliance**\n\nThe system extracts text, chunks content, retrieves relevant internal sections, and compares them.")

with wf3:
    st.info("**3. Review Dashboard**\n\nGet compliance score, findings, recommendations, and supporting evidence.")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Upload Policy Documents</div>", unsafe_allow_html=True)
st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    mother_file = st.file_uploader("Upload Mother Policy", type=["pdf"], key="mother_file")
    st.markdown('<div class="small-note">Reference framework, regulation, parent policy, or standard.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    internal_file = st.file_uploader("Upload Internal Policy", type=["pdf"], key="internal_file")
    st.markdown('<div class="small-note">Internal policy that will be assessed against the mother policy.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Advanced Settings"):
    query = st.text_area(
        "Retrieval Query",
        value="data retention, incident response, compliance monitoring, governance roles, access control, policy requirements",
        help="Used to retrieve the most relevant internal policy chunks."
    )
    top_k = st.slider("Number of Retrieved Chunks", min_value=3, max_value=10, value=5)
    mother_max_chars = st.slider("Mother Policy Max Characters", min_value=4000, max_value=20000, value=12000, step=1000)
    internal_max_chars = st.slider("Internal Context Max Characters", min_value=4000, max_value=20000, value=12000, step=1000)

run_clicked = st.button("Run Compliance Analysis", use_container_width=True)

if run_clicked:
    if not mother_file or not internal_file:
        st.warning("Please upload both PDF files before running the analysis.")
    else:
        with st.spinner("Analyzing policies and building dashboard..."):
            try:
                result = run_compliance_agent(
                    mother_file=mother_file,
                    internal_file=internal_file,
                    query=query,
                    top_k=top_k,
                    mother_max_chars=mother_max_chars,
                    internal_max_chars=internal_max_chars
                )

                analysis_text = result["analysis_result"]

                score = extract_score(analysis_text)
                status = get_status(score)

                summary = extract_section(analysis_text, "Summary")
                compliant = extract_section(analysis_text, "Compliant Areas")
                partially_compliant = extract_section(analysis_text, "Partially Compliant Areas")
                non_compliant = extract_section(analysis_text, "Non-Compliant Areas")
                recommendations = extract_section(analysis_text, "Recommendations")

                compliant_count = count_bullets(compliant)
                partial_count = count_bullets(partially_compliant)
                non_compliant_count = count_bullets(non_compliant)
                recommendation_count = count_bullets(recommendations)

                processed = result["processed_data"]
                retrieved_chunks = result["retrieved_chunks"]

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Executive Dashboard</div>", unsafe_allow_html=True)
                st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    st.metric("Compliance Score", f"{score}%" if score is not None else "N/A")
                with k2:
                    st.metric("Status", status)
                with k3:
                    st.metric("Non-Compliant Items", non_compliant_count)
                with k4:
                    st.metric("Retrieved Chunks", len(retrieved_chunks))

                st.markdown("<div class='section-title'>Compliance Score Overview</div>", unsafe_allow_html=True)
                st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                render_score_bar(score)

                c1, c2 = st.columns([1.2, 1])

                with c1:
                    st.markdown("<div class='section-title'>Summary</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.markdown(summary if summary else "No summary available.")

                with c2:
                    st.markdown("<div class='section-title'>Findings Overview</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.write(f"Compliant Areas: **{compliant_count}**")
                    st.write(f"Partially Compliant Areas: **{partial_count}**")
                    st.write(f"Non-Compliant Areas: **{non_compliant_count}**")
                    st.write(f"Recommendations: **{recommendation_count}**")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Detailed Findings</div>", unsafe_allow_html=True)
                st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

                d1, d2 = st.columns(2)

                with d1:
                    st.markdown("<div class='section-title'>Compliant Areas</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.markdown(compliant if compliant else "- No compliant areas identified.")

                    st.markdown("<div class='section-title'>Partially Compliant Areas</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.markdown(partially_compliant if partially_compliant else "- No partially compliant areas identified.")

                with d2:
                    st.markdown("<div class='section-title'>Non-Compliant Areas</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.markdown(non_compliant if non_compliant else "- No non-compliant areas identified.")

                    st.markdown("<div class='section-title'>Recommendations</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.markdown(recommendations if recommendations else "- No recommendations available.")

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<div class='section-title'>Full Compliance Report</div>", unsafe_allow_html=True)
                st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

                pdf_file = generate_pdf_report(
                    score=score,
                    status=status,
                    summary=summary,
                    compliant=compliant,
                    partially_compliant=partially_compliant,
                    non_compliant=non_compliant,
                    recommendations=recommendations,
                    full_report=analysis_text
                )

                st.download_button(
                    label="⬇️ Download Full Compliance Report (PDF)",
                    data=pdf_file,
                    file_name="compliance_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                tab1, tab2, tab3 = st.tabs(["Retrieved Evidence", "Model Context", "Processing Details"])

                with tab1:
                    st.markdown("<div class='section-title'>Retrieved Internal Policy Evidence</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    if retrieved_chunks:
                        for i, chunk in enumerate(retrieved_chunks, start=1):
                            page_number = chunk.get("page_number", "N/A")
                            score_value = round(chunk.get("score", 0), 4)
                            with st.expander(f"Chunk {i} | Page {page_number} | Similarity {score_value}"):
                                st.write(chunk.get("text", ""))
                    else:
                        st.info("No retrieved evidence available.")

                with tab2:
                    st.markdown("<div class='section-title'>Internal Context Sent to the Model</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
                    st.text_area(
                        "Context",
                        value=result["internal_context"],
                        height=300
                    )

                with tab3:
                    st.markdown("<div class='section-title'>Processing Details</div>", unsafe_allow_html=True)
                    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

                    p1, p2 = st.columns(2)

                    with p1:
                        st.markdown("#### Mother Policy")
                        st.write("Pages:", len(processed["mother_policy"]["pages"]))
                        st.write("Chunks:", len(processed["mother_policy"]["chunks"]))

                    with p2:
                        st.markdown("#### Internal Policy")
                        st.write("Pages:", len(processed["internal_policy"]["pages"]))
                        st.write("Chunks:", len(processed["internal_policy"]["chunks"]))

                st.success("Compliance dashboard generated successfully.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
