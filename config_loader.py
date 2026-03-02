import sys
import yaml

_config_cache = None


def load_config(path="config.yml"):
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    try:
        with open(path, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
    except FileNotFoundError:
        print(
            "ERROR: config.yml not found.\n"
            "  cp config.yml.example config.yml   # then fill in your details",
            file=sys.stderr,
        )
        sys.exit(1)

    _validate_config(_config_cache)
    return _config_cache


def _validate_config(cfg):
    required_sections = ["personal", "links", "education", "experience", "cover_letter", "app", "prompts"]
    for section in required_sections:
        if section not in cfg:
            raise ValueError(f"Missing required config section: '{section}'")

    personal_keys = ["first_name", "last_name", "full_name", "email"]
    for key in personal_keys:
        if key not in cfg["personal"]:
            raise ValueError(f"Missing required personal field: '{key}'")

    required_prompts = ["extract_jobs", "write_match", "extract_personal_info", "cover_letter"]
    for key in required_prompts:
        if key not in cfg["prompts"]:
            raise ValueError(f"Missing required prompt: '{key}'")


def get_personal():
    return load_config()["personal"]


def get_links():
    return load_config()["links"]


def get_education():
    return load_config()["education"]


def get_experience():
    return load_config()["experience"]


def get_cover_letter_config():
    return load_config()["cover_letter"]


def get_resources():
    return load_config().get("resources", [])


def get_app_config():
    return load_config()["app"]


def get_prompts():
    return load_config()["prompts"]
