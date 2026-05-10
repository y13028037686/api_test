from pathlib import Path

from common.yaml_loader import load_yaml


BASE_DIR = Path(__file__).resolve().parents[1]


def load_settings(env: str = "dev") -> dict:
    """
    根据环境加载配置。
    支持：
    pytest --env=dev
    pytest --env=test
    """
    config_file = BASE_DIR / "config" / f"env_{env}.yaml"

    if not config_file.exists():
        raise FileNotFoundError(f"环境配置文件不存在：{config_file}")

    return load_yaml(str(config_file))
