# chains.py

import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

import datetime

class Chain:
    def __init__(self):
         self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-pro"),
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
         )

    def extract_jobs(self,clean_text):
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
            respose = chain_extract.invoke({"page_data":clean_text})
            json_parser = JsonOutputParser()
            job_description = json_parser.parse(respose.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parser job(llm token limit:10000)")
        return job_description if isinstance(job_description,list) else [job_description]
    
    def write_match(self,job_description,resume_content):
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
        response = chain_match.invoke({"job_description":str(job_description),"resume": str(resume_content)})
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
             # Fallback or empty dict if parsing fails
            return {}
        except Exception as e:
            return {}

        return personal_info if isinstance(personal_info, dict) else {}

    def cover_letter(self, job_description, resume_content):
        prompt_coverletter = PromptTemplate.from_template(
            """
            ### ROLE
            You are an expert career coach and professional copywriter known for writing high-converting, non-generic cover letters. 
            Your goal is to write a cover letter that gets the candidate an interview by demonstrating specific value, not just stating interest.

            ### INPUTS
            JOB DESCRIPTION:
            {job_description}

            RESUME CONTENT:
            {resume}
            
            CURRENT DATE:
            {date_str}

            ### INSTRUCTIONS
            Write the **BODY** of a tailored cover letter. 
            
            **DO NOT** write the header (Name, Date, Company Address). 
            **DO NOT** write the sign-off (Sincerely, Name).
            **DO NOT** write the "Re:" line.
            
            Focus ONLY on the content paragraphs (Salutation -> Closing Call to Action).

            STRICT RULES:
            1.  **NO CLICHÉS**: Do NOT start with "I am writing to apply for..." or "I am thrilled to...". Start with a strong "hook".
            2.  **SHOW, DON'T TELL**: Use the STAR method (Situation, Task, Action, Result) with numbers/metrics.
            3.  **STRUCTURE**:
                *   **Salutation**: Dear Hiring Manager, (or specific name if found).
                *   **Opening**: Attention-grabbing hook connecting achievement to company need.
                *   **Body Paragraph 1 (Hard Skills)**: Prove mastery of top JD skills with a specific project.
                *   **Body Paragraph 2 (Soft Skills/Culture)**: Leadership/problem-solving story.
                *   **Closing**: Confident call to action.

            4.  **TONE**: Professional, confident, direct.
            5.  **LENGTH**: Keep it concise (under 300 words for the body).

            ### OUTPUT FORMAT
            Return *only* the text from "Dear Hiring Manager," down to the final sentence of the closing paragraph.
            NO markdown formatting like **bold** inside the text unless necessary for emphasis.

            ### OUTPUT FORMAT
            Return *only* the body of the cover letter (including the header).
            """
        )

        chain_coverletter = prompt_coverletter | self.llm
        coverletter = chain_coverletter.invoke({
            "job_description": job_description,
            "resume": resume_content,
            "date_str": datetime.date.today().strftime("%B %d, %Y")
        })

        return coverletter.content


if __name__ == "__main__":
    chain = Chain()
    print("Chain initialized successfully.")
