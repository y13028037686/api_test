import allure
import pytest
from pathlib import Path

from common.yaml_loader import load_yaml
from common.test_helper import execute_case

BASE_DIR = Path(__file__).resolve().parents[1]

comment_create_cases = load_yaml(BASE_DIR / "data" / "comment_create.yaml")["comment_create"]
comment_delete_cases = load_yaml(BASE_DIR / "data" / "comment_delete.yaml")["comment_delete"]
comment_list_cases = load_yaml(BASE_DIR / "data" / "comment_list.yaml")["comment_list"]


@allure.feature("评论模块")
class TestComment:
    @allure.story("发表评论")
    @pytest.mark.parametrize("case", comment_create_cases, ids=lambda c: c["id"])
    def test_create_comment(self, case, request):
        execute_case(case, request)

    @allure.story("删除评论")
    @pytest.mark.parametrize("case", comment_delete_cases, ids=lambda c: c["id"])
    def test_delete_comment(self, case, request):
        execute_case(case, request)

    @allure.story("评论列表")
    @pytest.mark.parametrize("case", comment_list_cases, ids=lambda c: c["id"])
    def test_list_comments(self, case, request):
        execute_case(case, request)
