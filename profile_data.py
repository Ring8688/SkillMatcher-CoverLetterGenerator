import os
from config_loader import get_personal, get_links, get_education, get_experience, get_resources
from utils import pdf_text_extractor, md_text_extractor

DATA_DIR = "data"


def _load_file(path, label):
    """Load a single file using the appropriate extractor based on extension."""
    if not os.path.exists(path):
        return f"{label} file not found ({path}).\n"
    try:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".pdf":
            content = pdf_text_extractor(path)
        elif ext == ".md":
            content = md_text_extractor(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        return f"# {label}\n{content}\n\n"
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return f"Error reading {path}: {e}\n"


def get_profile():
    """
    Loads the user's profile data including contact info and resource files.
    Reads config resources first, then auto-discovers additional .pdf/.md files in data/.
    """
    personal = get_personal()
    links = get_links()

    contact_info = f"""
    Name: {personal.get('full_name', '')}
    Phone: {personal.get('phone', '')}
    Email: {personal.get('email', '')}
    LinkedIn: {links.get('linkedin', '')}
    Portfolio: {links.get('portfolio', '')}
    GitHub: {links.get('github', '')}
    Location: {personal.get('location', '')}
    """

    profile_content = f"# Contact Information\n{contact_info}\n\n"

    # Track loaded paths to avoid duplicates
    loaded_paths = set()

    # 1. Load files explicitly listed in config resources
    for res in get_resources():
        path = res.get("path", "")
        label = res.get("label", path)
        abs_path = os.path.abspath(path)
        loaded_paths.add(abs_path)
        profile_content += _load_file(path, label)

    # 2. Auto-discover additional .pdf/.md files in data/
    if os.path.isdir(DATA_DIR):
        for filename in sorted(os.listdir(DATA_DIR)):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".pdf", ".md"):
                continue
            filepath = os.path.join(DATA_DIR, filename)
            abs_path = os.path.abspath(filepath)
            if abs_path in loaded_paths:
                continue
            loaded_paths.add(abs_path)
            label = os.path.splitext(filename)[0].replace("-", " ").replace("_", " ").title()
            profile_content += _load_file(filepath, label)

    return profile_content


def get_details():
    """
    Returns structured data for auto-filling forms.
    """
    personal = get_personal()
    links = get_links()
    education = get_education()
    experience = get_experience()

    return {
        "Personal": {
            "First Name": personal.get("first_name", ""),
            "Last Name": personal.get("last_name", ""),
            "Full Name": personal.get("full_name", ""),
            "Email": personal.get("email", ""),
            "Phone": personal.get("phone", ""),
            "Location": personal.get("location", ""),
        },
        "Links": {
            "LinkedIn": links.get("linkedin", ""),
            "Portfolio": links.get("portfolio", ""),
            "GitHub": links.get("github", ""),
        },
        "Education": {
            "University": education.get("university", ""),
            "Degree": education.get("degree", ""),
            "Graduation": education.get("graduation", ""),
            "GPA": education.get("gpa", ""),
        },
        "Experience": {
            "Current Role": experience.get("current_role", ""),
            "Current Company": experience.get("current_company", ""),
            "Key Tech Stack": experience.get("key_tech_stack", ""),
            "Summary": experience.get("summary", ""),
        },
    }
