"""Wyoming Porcupine v3 wake word detection module."""
import logging
import pathlib

_LOGGER = logging.getLogger(__name__)
_DIR = pathlib.Path(__file__).parent

try:
    with open(_DIR / "VERSION", "r", encoding="utf-8") as version_file:
        __version__ = version_file.read().strip()
except Exception:
    __version__ = "0.0.0" 