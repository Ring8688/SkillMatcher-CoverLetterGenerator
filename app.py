# app.py

import os
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import streamlit.components.v1 as components
import tempfile
import pathlib
import shutil

from chains import Chain
from utils import clean_text, pdf_text_extractor, md_text_extractor, text_fields, text_to_pdf_bytes
from langchain_community.document_loaders import WebBaseLoader

# ✅ Set USER_AGENT to avoid warning
if not os.environ.get("USER_AGENT"):
    os.environ["USER_AGENT"] = "SkillMatcherBot/1.0 (+https://yourprojectsite.com)"

# Persistent upload directory
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def create_streamlit_app(llm):
    st.set_page_config(layout="wide", page_title="Skills Matcher and Cover Letter Generator", page_icon="📑")
    st.title("📄 Skill Matcher and Cover Letter Generator")

    # Select Input Method
    input_method = st.radio("Choose Job Description Input Method:", ("Job URL", "Paste Job Text"))

    url_input = ""
    text_input = ""

    if input_method == "Job URL":
        url_input = st.text_input("Enter Job URL:", value="https://www.amazon.jobs/en/jobs/2890079/software-dev-engineer-i-amazon-university-talent-acquisition")
        if not url_input:
             st.warning("Please enter a job posting URL.")
    else:
        text_input = st.text_area("Paste Job Description:", height=200, placeholder="Paste the full job description here...")
        if not text_input:
            st.warning("Please paste the job description.")


    col1, col2 = st.columns([4, 1])

    with col1:
        st.subheader("Upload New Files")
        # Changed to accept multiple files and MD files
        uploaded_files = st.file_uploader("Upload Resume/Corpus (PDF, MD)", type=['pdf', 'md'], accept_multiple_files=True)
        
        # Save uploaded files to persistent storage
        if uploaded_files:
            for uploaded_file in uploaded_files:
                file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                if not os.path.exists(file_path): # Check if already exists to avoid overwriting or just overwrite
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
            st.success(f"Files saved to {UPLOAD_DIR}")


    with col2:
        st.subheader("Stored Files")
        # List files in persistent directory
        stored_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(('.pdf', '.md'))]
        
        selected_stored_files = st.multiselect("Select stored files:", stored_files, default=stored_files)
        
    
    # Files to process = selected stored files. (Newly uploaded files are auto-saved to storage and should be in the list upon rerun, 
    # but for immediate use we might want to manually add them if st.rerun isn't called. 
    # Actually, simpler logic: Always read from disk based on selection.
    # When user uploads, we save to disk. The multiselect might need a rerun to update, 
    # but let's try to just use the files we have.)
    
    # Combined list of files to process
    files_to_process = [os.path.join(UPLOAD_DIR, f) for f in selected_stored_files]

    # Initialize session state for Files viewer toggle
    if 'show_files' not in st.session_state:
        st.session_state['show_files'] = False
        
    if st.button("View Selected Files"):
        st.session_state['show_files'] = True
    if st.button("Close View"):
        st.session_state['show_files'] = False


    # ✅ View selected files if toggled
    if st.session_state['show_files'] and files_to_process:
        st.subheader("📑 Selected Files Preview")
        for file_path in files_to_process:
            file_name = os.path.basename(file_path)
            file_extension = pathlib.Path(file_path).suffix.lower()
            
            st.markdown(f"**File:** {file_name}")

            if file_extension == '.pdf':
                try:
                    html_code = pdf_viewer(input=file_path, width=700)
                    if html_code:
                        components.html(html_code, height=600, scrolling=True)
                except Exception as e:
                    st.error(f"Error rendering PDF: {e}")
            elif file_extension == '.md':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        st.markdown(f.read())
                except Exception as e:
                    st.error(f"Error rendering MD: {e}")
            
            st.divider()

    submit_button = st.button("Check Match")
    output = None

    # ✅ Check Match button logic
    if submit_button and files_to_process:
        try:
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
                    # Apply the same cleaning to maintain consistency, or use as is
                    cleaned_text = clean_text(text_input)
                else:
                    st.error("Please paste the job description.")

            if cleaned_text:
                jobs = llm.extract_jobs(cleaned_text)

                resume_content = ""
                for file_path in files_to_process:
                    file_extension = pathlib.Path(file_path).suffix.lower()
                    
                    if file_extension == '.pdf':
                        resume_content += pdf_text_extractor(file_path) + "\n"
                    elif file_extension == '.md':
                        resume_content += md_text_extractor(file_path) + "\n"

                match = llm.write_match(jobs, resume_content)
                output = text_fields(match)

                # ✅ Save to session_state for cover letter generation
                st.session_state['jobs'] = jobs
                st.session_state['resume_content'] = resume_content

        except Exception as e:
            st.error(f"An error occurred: {e}")
    elif submit_button and not files_to_process:
        st.warning("Please select or upload at least one file.")

    # ✅ Display matching results if output available
    if output:
        st.text_area("Job Matching Score:", value=output.get('match_score', 'N/A'), height=100)
        col3, col4 = st.columns(2)

        with col3:
            st.text_area("Job Required Skills:", value="\n".join(output.get('required_skills', [])), height=200)
        with col4:
            st.text_area("Your Skills:", value="\n".join(output.get('your_skills', [])), height=200)

        st.text_area("Matching Skills:", value="\n".join(output.get('matching_skills', [])), height=150)
        st.text_area("Focus/Improve Skills:", value="\n".join(output.get('focus_skills', [])), height=150)

    # Divider
    st.divider()

    # ✅ Auto-Fill Helper Section
    if 'resume_content' in st.session_state:
        st.subheader("📋 Auto-Fill Helper")
        st.caption("Use these extracted details to quickly fill out job application forms.")
        
        if st.button("Extract Candidate Info"):
            with st.spinner("Extracting personal details..."):
                try:
                    candidate_info = llm.extract_personal_info(st.session_state['resume_content'])
                    st.session_state['candidate_info'] = candidate_info
                except Exception as e:
                    st.error(f"Error extracting info: {e}")
        
        if 'candidate_info' in st.session_state and st.session_state['candidate_info']:
            info = st.session_state['candidate_info']
            
            # Display fields in a grid
            
            # Personal Details
            st.markdown("##### Personal Details")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.text_input("Full Name", value=info.get("Full Name", ""), key="info_name")
                st.code(info.get("Full Name", ""), language=None)
            with c2:
                st.text_input("Email", value=info.get("Email", ""), key="info_email")
                st.code(info.get("Email", ""), language=None)
            with c3:
                st.text_input("Phone", value=info.get("Phone", ""), key="info_phone")
                st.code(info.get("Phone", ""), language=None)

            # Links
            st.markdown("##### Links")
            c4, c5 = st.columns(2)
            with c4:
                st.text_input("LinkedIn", value=info.get("LinkedIn URL", ""), key="info_linkedin")
                st.code(info.get("LinkedIn URL", ""), language=None)
            with c5:
                st.text_input("Portfolio", value=info.get("Portfolio/Website", ""), key="info_portfolio")
                st.code(info.get("Portfolio/Website", ""), language=None)
            
            # Professional
            st.markdown("##### Professional Info")
            c6, c7, c8 = st.columns(3)
            with c6:
                st.text_input("Current Company", value=info.get("Current Company", ""), key="info_company")
                st.code(info.get("Current Company", ""), language=None)
            with c7:
                st.text_input("Current Title", value=info.get("Current Job Title", ""), key="info_title")
                st.code(info.get("Current Job Title", ""), language=None)
            with c8:
                st.text_input("Years Exp", value=info.get("Total Years of Experience", ""), key="info_exp")
                st.code(info.get("Total Years of Experience", ""), language=None)

            # Education
            st.markdown("##### Education")
            c9, c10, c11 = st.columns(3)
            with c9:
                st.text_input("Highest Degree", value=info.get("Highest Degree", ""), key="info_degree")
                st.code(info.get("Highest Degree", ""), language=None)
            with c10:
                st.text_input("University", value=info.get("University/College", ""), key="info_uni")
                st.code(info.get("University/College", ""), language=None)
            with c11:
                st.text_input("Grad Year", value=info.get("Graduation Year", ""), key="info_grad")
                st.code(info.get("Graduation Year", ""), language=None)
            
            # Long Text
            st.markdown("##### Summary & Skills")
            st.text_area("Professional Summary", value=info.get("Professional Summary", ""), height=100, key="info_summary")
            st.code(info.get("Professional Summary", ""), language=None)
            
            st.text_area("Top Skills", value=info.get("Top 5 Skills", ""), key="info_skills")
            st.code(info.get("Top 5 Skills", ""), language=None)


    # Divider
    st.divider()

    # ✅ Cover letter generation
    if st.button("Generate Cover Letter"):
        if 'jobs' in st.session_state and 'resume_content' in st.session_state:
            try:
                # 1. Ensure we have candidate info for the header/footer
                if 'candidate_info' not in st.session_state or not st.session_state['candidate_info']:
                     with st.spinner("Extracting candidate info for header..."):
                         candidate_info = llm.extract_personal_info(st.session_state['resume_content'])
                         st.session_state['candidate_info'] = candidate_info
                
                info = st.session_state.get('candidate_info', {})
                full_name = info.get("Full Name", "Candidate Name")
                phone = info.get("Phone", "")
                email = info.get("Email", "")
                linkedin = info.get("LinkedIn URL", "")
                portfolio = info.get("Portfolio/Website", "")
                
                # Format contact line (e.g., "Phone | Email | LinkedIn")
                contact_parts = [p for p in [phone, email, linkedin, portfolio] if p]
                contact_line = " | ".join(contact_parts)

                # 2. Get Company Name
                jobs_data = st.session_state['jobs']
                company_name = "Hiring Manager"
                if isinstance(jobs_data, list) and len(jobs_data) > 0:
                    company_name = jobs_data[0].get('company', 'Hiring Manager')
                elif isinstance(jobs_data, dict):
                    company_name = jobs_data.get('company', 'Hiring Manager')
                
                # 3. Construct Header & Footer
                import datetime
                date_str = datetime.date.today().strftime("%B %d, %Y")
                
                header = f"{full_name}\n{contact_line}\n\n{date_str}\n\nHiring Manager\n{company_name}\n\n"
                
                # 4. Generate Body
                body = llm.cover_letter(st.session_state['jobs'], st.session_state['resume_content'])
                
                # 5. Construct Footer
                footer = f"\n\nSincerely,\n\n{full_name}"
                
                # 6. Combine
                final_cover_letter = header + body + footer
                
                st.session_state['cover_letter_text'] = final_cover_letter
            except Exception as e:
                st.error(f"An error occurred while generating cover letter: {e}")
        else:
            st.warning("Please run 'Check Match' first to load job description and resume.")

    # ✅ Display and download cover letter if available in session state
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
