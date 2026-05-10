import allure
import pytest
from pathlib import Path

from common.yaml_loader import load_yaml
from common.test_helper import execute_case

BASE_DIR = Path(__file__).resolve().parents[1]

like_cases = load_yaml(BASE_DIR / "data" / "like.yaml")["like"]


@allure.feature("点赞功能")
class TestLike:
    @pytest.mark.parametrize("case", like_cases, ids=lambda c: c["id"])
    def test_like(self, case, request):
        execute_case(case, request)
