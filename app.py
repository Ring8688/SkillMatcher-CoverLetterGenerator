# app.py

import os
import streamlit as st
import streamlit.components.v1 as components
import pathlib

from chains import Chain
from utils import clean_text, text_to_pdf_bytes
from langchain_community.document_loaders import WebBaseLoader
from profile_data import get_profile, get_details
from config_loader import get_app_config, get_personal

# Set USER_AGENT to avoid warning
if not os.environ.get("USER_AGENT"):
    os.environ["USER_AGENT"] = "SkillMatcherBot/1.0 (+https://yourprojectsite.com)"

def create_streamlit_app(llm):
    app_cfg = get_app_config()
    personal = get_personal()

    st.set_page_config(layout="wide", page_title=app_cfg.get("title", "Skills Matcher"), page_icon="📑")
    st.title(f"📄 {app_cfg.get('title', 'Skill Matcher and Cover Letter Generator')}")
    st.caption(app_cfg.get("caption", "Powered by Your Profile Data"))

    # Select Input Method
    input_method = st.radio("Choose Job Description Input Method:", ("Job URL", "Paste Job Text"))

    url_input = ""
    text_input = ""

    if input_method == "Job URL":
        url_input = st.text_input(
            "Enter Job URL:",
            value=app_cfg.get("default_job_url", ""),
        )
        if not url_input:
             st.warning("Please enter a job posting URL.")
    else:
        text_input = st.text_area("Paste Job Description:", height=200, placeholder="Paste the full job description here...")
        if not text_input:
            st.warning("Please paste the job description.")

    # Custom prompt textarea
    st.text_area(
        "Additional Instructions (Optional):",
        key="custom_prompt",
        height=100,
        placeholder="Add any specific instructions or context you'd like included in the cover letter, e.g. 'Emphasize my leadership experience' or 'Mention I'm relocating to Sydney'..."
    )

    st.divider()

    # Auto-Fill Helper Section (Always Visible)
    st.subheader("📋 Auto-Fill Helper (Quick Copy)")
    st.caption("Use these details to quickly fill out job application forms.")

    # Load structured details directly from profile_data
    info = get_details()
    st.session_state['candidate_info'] = info  # Store for cover letter use if needed

    # Display fields in a grid

    # Personal Details
    st.markdown("##### Personal Details")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.text("First Name")
        st.code(info["Personal"]["First Name"], language=None)
    with c2:
        st.text("Last Name")
        st.code(info["Personal"]["Last Name"], language=None)
    with c3:
        st.text("Full Name")
        st.code(info["Personal"]["Full Name"], language=None)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.text("Email")
        st.code(info["Personal"]["Email"], language=None)
    with c5:
        st.text("Phone")
        st.code(info["Personal"]["Phone"], language=None)
    with c6:
        st.text("Location")
        st.code(info["Personal"]["Location"], language=None)

    # Links
    st.markdown("##### Links")
    l1, l2, l3 = st.columns(3)
    with l1:
        st.text("LinkedIn")
        st.code(info["Links"]["LinkedIn"], language=None)
    with l2:
        st.text("Portfolio")
        st.code(info["Links"]["Portfolio"], language=None)
    with l3:
        st.text("GitHub")
        st.code(info["Links"]["GitHub"], language=None)

    # Education & Experience
    st.markdown("##### Education & Experience")
    e1, e2 = st.columns(2)
    with e1:
        st.text("University")
        st.code(info["Education"]["University"], language=None)
        st.text("Degree")
        st.code(info["Education"]["Degree"], language=None)
        st.text("Graduation")
        st.code(info["Education"]["Graduation"], language=None)
    with e2:
        st.text("Current Role")
        st.code(info["Experience"]["Current Role"], language=None)
        st.text("Current Company")
        st.code(info["Experience"]["Current Company"], language=None)
        st.text("Key Tech Stack")
        st.code(info["Experience"]["Key Tech Stack"], language=None)

    # Long Text
    st.markdown("##### Summaries")
    st.text("Experience Summary")
    st.code(info["Experience"]["Summary"], language=None)


    # Divider
    st.divider()

    # Cover letter generation
    if st.button("Generate Cover Letter"):
        try:
            # 1. Extract job description from input
            cleaned_text = ""
            if input_method == "Job URL":
                if url_input:
                    loader = WebBaseLoader([url_input])
                    data = loader.load()
                    cleaned_text = clean_text(data[0].page_content)
                else:
                    st.error("Please enter a URL.")
            else:
                if text_input:
                    cleaned_text = clean_text(text_input)
                else:
                    st.error("Please paste the job description.")

            if cleaned_text:
                with st.spinner("Extracting Job Details & Generating Cover Letter..."):
                    jobs = llm.extract_jobs(cleaned_text)
                    resume_content = get_profile()

                    # Store for PDF download use
                    st.session_state['jobs'] = jobs
                    st.session_state['resume_content'] = resume_content

                    # 2. Ensure we have candidate info for the header/footer
                    if 'candidate_info' not in st.session_state or not st.session_state['candidate_info']:
                        st.session_state['candidate_info'] = get_details()

                    info = st.session_state.get('candidate_info', {})

                    full_name = info.get("Personal", {}).get("Full Name", personal.get("full_name", "Candidate"))
                    phone = info.get("Personal", {}).get("Phone", "")
                    email = info.get("Personal", {}).get("Email", "")
                    linkedin = info.get("Links", {}).get("LinkedIn", "")
                    portfolio = info.get("Links", {}).get("Portfolio", "")

                    contact_parts = [p for p in [phone, email, linkedin, portfolio] if p]
                    contact_line = " | ".join(contact_parts)

                    # 3. Get Company Name
                    company_name = "Hiring Manager"
                    if isinstance(jobs, list) and len(jobs) > 0:
                        company_name = jobs[0].get('company', 'Hiring Manager')
                    elif isinstance(jobs, dict):
                        company_name = jobs.get('company', 'Hiring Manager')

                    # 4. Construct Header
                    import datetime
                    date_str = datetime.date.today().strftime("%B %d, %Y")
                    header = f"{full_name}\n{contact_line}\n\n{date_str}\n\nHiring Manager\n{company_name}\n\n"

                    # 5. Generate Body (with optional custom prompt)
                    custom_prompt = st.session_state.get('custom_prompt', '')
                    body = llm.cover_letter(jobs, resume_content, custom_prompt=custom_prompt)

                    # 6. Construct Footer & Combine
                    footer = f"\n\nSincerely,\n\n{full_name}"
                    final_cover_letter = header + body + footer

                    st.session_state['cover_letter_text'] = final_cover_letter
        except Exception as e:
            st.error(f"An error occurred while generating cover letter: {e}")

    # Display and download cover letter if available in session state
    if 'cover_letter_text' in st.session_state:
        st.text_area("Generated Cover Letter:", st.session_state['cover_letter_text'], height=500)

        # Determine filename based on company name
        company_name = "Company"
        jobs_data = st.session_state.get('jobs', [])

        if isinstance(jobs_data, list) and len(jobs_data) > 0:
            company_name = jobs_data[0].get('company', 'Company')
        elif isinstance(jobs_data, dict):
            company_name = jobs_data.get('company', 'Company')

        # Sanitize filename
        safe_company_name = "".join([c for c in company_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        if not safe_company_name:
            safe_company_name = "Company"

        pdf_filename = f"cover_letter_{safe_company_name}.pdf"

        if st.button("Download as PDF"):
            pdf_bytes = text_to_pdf_bytes(st.session_state['cover_letter_text'])
            st.download_button(
                f"📥 Click to Download PDF ({pdf_filename})",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf"
            )


if __name__ == "__main__":
    chain = Chain()
    create_streamlit_app(chain)
