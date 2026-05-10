import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


class SensitiveFilter(logging.Filter):
    """
    日志脱敏：
    token、Authorization、password 等敏感字段不直接打印。
    """

    SENSITIVE_PATTERNS = [
        (re.compile(r'("password"\s*:\s*")[^"]+(")', re.I), r'\1******\2'),
        (re.compile(r'("token"\s*:\s*")[^"]+(")', re.I), r'\1******\2'),
        (re.compile(r'(Authorization[\'"]?\s*[:=]\s*[\'"]?Bearer\s+)[A-Za-z0-9._\-]+', re.I), r'\1******'),
    ]

    def filter(self, record):
        message = record.getMessage()
        for pattern, repl in self.SENSITIVE_PATTERNS:
            message = pattern.sub(repl, message)

        record.msg = message
        record.args = ()
        return True


def get_logger(name: str = "api_test") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_file = LOG_DIR / "api_test.log"

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    sensitive_filter = SensitiveFilter()
    console_handler.addFilter(sensitive_filter)
    file_handler.addFilter(sensitive_filter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = get_logger()
