import logging

def setup_logger(log_level: str = "INFO"):
    print('setting up a logger')

    LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level_value = LEVELS.get(log_level.upper(), logging.INFO)

    uvicorn_logger = logging.getLogger("uvicorn.error")
    uvicorn_logger.setLevel(log_level_value)

    # Optionally, create a helper function to get this logger anywhere
    return uvicorn_logger
