import os
from config_loader import get_personal, get_links, get_education, get_experience, get_resources


def get_profile():
    """
    Loads the user's profile data including contact info and resource files.
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

    for res in get_resources():
        path = res.get("path", "")
        label = res.get("label", path)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    profile_content += f"# {label}\n{f.read()}\n\n"
            except Exception as e:
                print(f"Error reading {path}: {e}")
                profile_content += f"Error reading {path}: {e}\n"
        else:
            profile_content += f"{label} file not found ({path}).\n"

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
