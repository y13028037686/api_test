import allure
import pytest
from pathlib import Path

from common.yaml_loader import load_yaml
from common.test_helper import execute_case

BASE_DIR = Path(__file__).resolve().parents[1]

# 加载 YAML
register_cases = load_yaml(BASE_DIR / "data" / "user_register.yaml")["user_register"]
login_cases = load_yaml(BASE_DIR / "data" / "user_login.yaml")["user_login"]
info_cases = load_yaml(BASE_DIR / "data" / "user_info.yaml")["user_info"]
update_cases = load_yaml(BASE_DIR / "data" / "user_update.yaml")["user_update"]


@allure.feature("用户模块")
class TestUser:
    @allure.story("用户注册")
    @pytest.mark.parametrize("case", register_cases, ids=lambda c: c["id"])
    def test_register(self, case, request):
        execute_case(case, request)

    @allure.story("用户登录")
    @pytest.mark.parametrize("case", login_cases, ids=lambda c: c["id"])
    def test_login(self, case, request):
        execute_case(case, request)

    @allure.story("获取个人信息")
    @pytest.mark.parametrize("case", info_cases, ids=lambda c: c["id"])
    def test_get_user_info(self, case, request):
        execute_case(case, request)

    @allure.story("修改个人信息")
    @pytest.mark.parametrize("case", update_cases, ids=lambda c: c["id"])
    def test_update_user_info(self, case, request):
        execute_case(case, request)
