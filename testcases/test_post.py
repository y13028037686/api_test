import allure
import pytest
from pathlib import Path

from common.yaml_loader import load_yaml
from common.test_helper import execute_case

BASE_DIR = Path(__file__).resolve().parents[1]

post_create_cases = load_yaml(BASE_DIR / "data" / "post_create.yaml")["post_create"]
post_edit_cases = load_yaml(BASE_DIR / "data" / "post_edit.yaml")["post_edit"]
post_delete_cases = load_yaml(BASE_DIR / "data" / "post_delete.yaml")["post_delete"]
post_detail_cases = load_yaml(BASE_DIR / "data" / "post_detail.yaml")["post_detail"]
post_list_cases = load_yaml(BASE_DIR / "data" / "post_list.yaml")["post_list"]
post_search_cases = load_yaml(BASE_DIR / "data" / "post_search.yaml")["post_search"]


@allure.feature("文章模块")
class TestPost:
    @allure.story("发布文章")
    @pytest.mark.parametrize("case", post_create_cases, ids=lambda c: c["id"])
    def test_create_post(self, case, request):
        execute_case(case, request)

    @allure.story("编辑文章")
    @pytest.mark.parametrize("case", post_edit_cases, ids=lambda c: c["id"])
    def test_edit_post(self, case, request):
        execute_case(case, request)

    @allure.story("删除文章")
    @pytest.mark.parametrize("case", post_delete_cases, ids=lambda c: c["id"])
    def test_delete_post(self, case, request):
        execute_case(case, request)

    @allure.story("文章详情")
    @pytest.mark.parametrize("case", post_detail_cases, ids=lambda c: c["id"])
    def test_post_detail(self, case, request):
        execute_case(case, request)

    @allure.story("分页列表")
    @pytest.mark.parametrize("case", post_list_cases, ids=lambda c: c["id"])
    def test_post_list(self, case, request):
        execute_case(case, request)

    @allure.story("搜索文章")
    @pytest.mark.parametrize("case", post_search_cases, ids=lambda c: c["id"])
    def test_search_posts(self, case, request):
        execute_case(case, request)
