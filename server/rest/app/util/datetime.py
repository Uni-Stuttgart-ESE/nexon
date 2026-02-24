from datetime import datetime


def today() -> str:
    """Return today's date as DD/MM/YYYY."""
    return datetime.now().strftime("%d/%m/%Y")
