# utils.py

import re
from langchain_community.document_loaders import PyPDFLoader
from fpdf import FPDF
from io import BytesIO

def clean_text(text):
    # Remove HTML tags
    text = re.sub(r'<[^>]*?>', '', text)

    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

    # Remove special characters (keep only alphanumeric and spaces)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s{2,}', ' ', text)

    # Trim leading and trailing whitespace
    text = text.strip()

    return text

def pdf_text_extractor(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()  
    
    resume_content = ""
    for page in pages:
        resume_content += page.page_content + '\n'
        
    return resume_content

def md_text_extractor(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def sanitize_text_for_pdf(text):
    """
    Replaces characters incompatible with latin-1 encoding with their ASCII equivalents.
    """
    replacements = {
        '\u2014': '-',   # em dash
        '\u2013': '-',   # en dash
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u2026': '...', # ellipsis
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Fallback: remove any other non-latin-1 characters
    return text.encode('latin-1', 'replace').decode('latin-1')


def text_to_pdf_bytes(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_margins(left=15, top=15, right=15) # Standard margins
    pdf.add_page()
    pdf.set_font("Arial", size=11) # Standard font size
    
    # Sanitize text before processing
    text = sanitize_text_for_pdf(text)
    
    for line in text.split('\n'):
        # If line is empty or just whitespace, add a line break to preserve spacing
        if not line.strip():
             pdf.ln(6) # 6mm height for empty line
        else:
             # multi_cell(w, h, txt)
             # w=0 means full width
             # h=6 means 6mm height per line (standard for 11-12pt font)
             pdf.multi_cell(0, 6, line)
            
    # Use 'S' to output as string (in Py3 it returns a string that needs encoding to bytes)
    # Since we already sanitized, we can safely encode to latin-1
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return BytesIO(pdf_bytes)



def text_fields(output_text):

    match_score = re.search(r"\*\*Matching score\*\*: (.+?)\n", output_text).group(1).strip()

    required_skills = re.search(r"\*\*Required skills\*\*:[\s\S]*?\*\*Your skills", output_text).group(0)
    required_skills = re.findall(r"- (.+)", required_skills)

    your_skills = re.search(r"\*\*Your skills\*\*:[\s\S]*?\*\*Matching skills", output_text).group(0)
    your_skills = re.findall(r"- (.+)", your_skills)

    matching_skills = re.search(r"\*\*Matching skills\*\*:[\s\S]*?\*\*Focus/improve skills", output_text).group(0)
    matching_skills = re.findall(r"- (.+)", matching_skills)

    focus_skills = re.search(r"\*\*Focus/improve skills\*\*:([\s\S]*)", output_text).group(1)
    focus_skills = re.findall(r"- (.+)", focus_skills)

    return {
        "match_score": match_score,
        "required_skills": required_skills,
        "your_skills": your_skills,
        "matching_skills": matching_skills,
        "focus_skills": focus_skills
    }
