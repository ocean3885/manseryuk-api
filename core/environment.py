"""Load deployment configuration from the project root without overriding the host."""
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[1] / '.env'


def load_environment():
    """Missing .env is allowed; existing process variables always take precedence."""
    return load_dotenv(dotenv_path=ENV_FILE, override=False, encoding='utf-8')
