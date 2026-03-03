import logging
from pathlib import Path


def setup_logger():
    Path("logs").mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("logs/contactor.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger("contactor")
