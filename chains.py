# chains.py

import os
import json
import datetime
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from config_loader import get_personal, get_cover_letter_config, get_links, get_prompts

load_dotenv()


def _create_llm():
    """Create LLM instance based on API_TYPE env var (anthropic or openai)."""
    api_type = os.getenv("API_TYPE", "anthropic").lower()
    model = os.getenv("API_MODEL", "claude-sonnet-4-6")
    temperature = float(os.getenv("API_TEMPERATURE", "0"))
    api_key = os.getenv("API_KEY")
    base_url = os.getenv("API_BASE_URL")

    if api_type == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            max_tokens=4096,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
        )


class Chain:
    def __init__(self):
        self.llm = _create_llm()
        self.prompts = get_prompts()

    def extract_jobs(self, clean_text):
        prompt_extract = PromptTemplate.from_template(self.prompts["extract_jobs"])
        chain_extract = prompt_extract | self.llm
        try:
            respose = chain_extract.invoke({"page_data": clean_text})
            json_parser = JsonOutputParser()
            job_description = json_parser.parse(respose.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parser job(llm token limit:10000)")
        return job_description if isinstance(job_description, list) else [job_description]

    def write_match(self, job_description, resume_content):
        prompt_match = PromptTemplate.from_template(self.prompts["write_match"])
        chain_match = prompt_match | self.llm
        response = chain_match.invoke({"job_description": str(job_description), "resume": str(resume_content)})
        return response.content

    def extract_personal_info(self, resume_content):
        prompt_extract_info = PromptTemplate.from_template(self.prompts["extract_personal_info"])
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

        prompt_coverletter = PromptTemplate.from_template(self.prompts["cover_letter"])

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
