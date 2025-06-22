import logging
from pathlib import Path

def get_logger(name="receipt_app"):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():  # Avoid adding handlers multiple times
        logger.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # File handler
        LOG_DIR = Path("logs")
        LOG_DIR.mkdir(exist_ok=True)
        LOG_FILE = LOG_DIR / "streamlit_info.log"
        file_handler = logging.FileHandler(LOG_FILE, mode='a')  # 'a' = append mode
        file_format = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger