# chains.py

import os
import json
import datetime
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from config_loader import get_personal, get_cover_letter_config, get_links

load_dotenv()


class Chain:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("API_MODEL", "gpt-4o"),
            temperature=float(os.getenv("API_TEMPERATURE", "0")),
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("API_BASE_URL"),
        )

    def extract_jobs(self, clean_text):
        prompt_extract = PromptTemplate.from_template(
            """
                ### SCRAPED TEXT FROM WEBSITE
                {page_data}
                ### INSTRUCTION
                The scraped test is from the carrer's page of website.
                Your job is to extract the job posting and return them in JSON format contain the
                following keys : 'company','role','experience','skills',and 'description'.
                Only return the valid JSON.
                ### VALID JSON (NO PREAMBLE):
                """
        )
        chain_extract = prompt_extract | self.llm
        try:
            respose = chain_extract.invoke({"page_data": clean_text})
            json_parser = JsonOutputParser()
            job_description = json_parser.parse(respose.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parser job(llm token limit:10000)")
        return job_description if isinstance(job_description, list) else [job_description]

    def write_match(self, job_description, resume_content):
        prompt_match = PromptTemplate.from_template(
            """
            ### RESUME DESCRIPTION
            {resume}
            As a smart skills checker compare the skills,experience,and all required description that allign the {job_description}.
            Analyse and give the view  wiht 'Maching score', 'Required skills', 'Your skills', 'Matching skills' and 'focus/improve skills' concise and on to poin.
            Do not provide preamble
            ### Response (NO PREAMBEL):
            """
        )

        chain_match = prompt_match | self.llm
        response = chain_match.invoke({"job_description": str(job_description), "resume": str(resume_content)})
        return response.content

    def extract_personal_info(self, resume_content):
        prompt_extract_info = PromptTemplate.from_template(
            """
            ### RESUME TEXT
            {resume}

            ### INSTRUCTION
            You are a helpful assistant that extracts personal information and key details from a resume to help the candidate fill out job application forms.
            Extract the following fields from the resume text. Return a JSON object with these exact keys. If a field is not found, use an empty string "".

            Keys to extract:
            - "Full Name"
            - "Email"
            - "Phone"
            - "LinkedIn URL"
            - "Portfolio/Website"
            - "Current Company"
            - "Current Job Title"
            - "Highest Degree"
            - "University/College"
            - "Graduation Year" (YYYY)
            - "Total Years of Experience" (Numeric string, e.g., "5")
            - "Top 5 Skills" (Comma separated string)
            - "Professional Summary" (Short 2-3 sentence summary)

            ### VALID JSON (NO PREAMBLE):
            """
        )

        chain_extract_info = prompt_extract_info | self.llm
        try:
            response = chain_extract_info.invoke({"resume": str(resume_content)})
            json_parser = JsonOutputParser()
            personal_info = json_parser.parse(response.content)
        except OutputParserException:
            return {}
        except Exception:
            return {}

        return personal_info if isinstance(personal_info, dict) else {}

    def cover_letter(self, job_description, resume_content, custom_prompt=""):
        custom_section = ""
        if custom_prompt.strip():
            custom_section = f"""
            ### ADDITIONAL INSTRUCTIONS FROM CANDIDATE
            {custom_prompt}
            Please incorporate the above instructions/context into the cover letter naturally.
            """

        personal = get_personal()
        cl_config = get_cover_letter_config()
        links = get_links()

        candidate_name = personal.get("full_name", "Candidate")
        portfolio_url = links.get("portfolio", "")

        value_props = cl_config.get("value_propositions", [])
        value_props_text = "\n".join(
            f"            {i}. {vp}" for i, vp in enumerate(value_props, 1)
        )

        tone = cl_config.get("tone", "Professional and sincere")
        max_words = cl_config.get("max_words", 300)
        salutation_style = cl_config.get("salutation_style", "Dear Hiring Manager")

        prompt_coverletter = PromptTemplate.from_template(
            """
            ### ROLE
            You are a professional career assistant helping {candidate_name} write a high-impact Cover Letter (or Message) to a potential employer.

            ### INPUTS
            JOB DESCRIPTION (JD):
            {job_description}

            CANDIDATE PROFILE ({candidate_name}):
            {resume}

            CURRENT DATE:
            {date_str}

            ### CORE VALUE PROPOSITION ({candidate_name}'s Key Selling Points)
{value_props_text}

            ### INSTRUCTIONS (Tone & Style)
            1.  **Tone**: {tone}. {salutation_style}
            2.  **Structure**: Fluid paragraphs (NO bullet points). Short and punchy (under {max_words} words).
            3.  **Content Flow**:
                *   **Hook**: Who {candidate_name} is + Specific interest in this company/role (Reference the JD directly).
                *   **Proof**: Connect the candidate's key experience to the JD's requirements.
                *   **Edge**: Highlight unique differentiators from the value propositions above.
                *   **Closing**: Reiterate desire for long-term growth + Link to portfolio ({portfolio_url}).

            {custom_section}

            ### OUTPUT FORMAT
            Return *only* the body of the message (Salutation -> Body -> Closing).
            Do NOT include the header block (Name/Address/Date) or the signature block at the very end (Sincerely, {candidate_name}), as those are added by the application wrapper.
            Just the core message text.
            """
        )

        chain_coverletter = prompt_coverletter | self.llm
        coverletter = chain_coverletter.invoke({
            "candidate_name": candidate_name,
            "job_description": job_description,
            "resume": resume_content,
            "date_str": datetime.date.today().strftime("%B %d, %Y"),
            "value_props_text": value_props_text,
            "tone": tone,
            "max_words": max_words,
            "salutation_style": salutation_style,
            "portfolio_url": portfolio_url,
            "custom_section": custom_section,
        })

        return coverletter.content


if __name__ == "__main__":
    chain = Chain()
    print("Chain initialized successfully.")
