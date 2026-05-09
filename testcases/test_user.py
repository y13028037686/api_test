import allure
import pytest
from pathlib import Path
from copy import deepcopy

from common.yaml_loader import load_yaml
from common.assert_utils import assert_status_code, get_json, assert_business_code
from common.logger import logger

BASE_DIR = Path(__file__).resolve().parents[1]

# 加载各模块的 YAML
register_cases = load_yaml(BASE_DIR / "data" / "user_register.yaml")["user_register"]
login_cases = load_yaml(BASE_DIR / "data" / "user_login.yaml")["user_login"]
info_cases = load_yaml(BASE_DIR / "data" / "user_info.yaml")["user_info"]
update_cases = load_yaml(BASE_DIR / "data" / "user_update.yaml")["user_update"]


def replace_template(obj, variables):
    """递归替换字符串中的 {{key}}"""
    if isinstance(obj, dict):
        return {k: replace_template(v, variables) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_template(i, variables) for i in obj]
    if isinstance(obj, str):
        for k, v in variables.items():
            obj = obj.replace(f"{{{{{k}}}}}", str(v))
        return obj
    return obj


@allure.feature("用户模块")
class TestUser:

    @allure.story("用户注册")
    @pytest.mark.parametrize("case", register_cases)
    def test_register(self, case, request, existing_user_fixture):
        variables = {}
        if "existing_user" in case["preconditions"]:
            # existing_user_fixture 返回 (username, password, user_id)
            username, _, _ = existing_user_fixture
            variables["existing_username"] = username
            variables["username"] = username  # 注册时使用已存在的用户名
        else:
            # 生成随机用户名，但保留模板中的 {{username}} 需要实际值
            from conftest import generate_username
            variables["username"] = generate_username("testuser")

        # 处理长字符串
        if "{{long_signature}}" in str(case):
            variables["long_signature"] = "a" * 201

        req = replace_template(deepcopy(case["request"]), variables)
        method = req["method"].lower()
        url = req["url"]
        headers = req.get("headers", {})
        body = req.get("body", {})
        params = req.get("params", {})

        # 获取未认证的 client（注册不需要登录）
        from conftest import api_client_fixture
        client = api_client_fixture(request)  # 需要从 request 获取 fixture，简便起见直接调用 fixture 函数
        # 实际更规范的是在 fixture 参数中声明 api_client，但由于数据驱动，这里简化：直接使用 request.getfixturevalue
        api_client = request.getfixturevalue("api_client")

        # 发送请求
        if method == "post":
            resp = api_client.post(url, json_body=body, headers=headers, params=params)
        else:
            raise ValueError(f"不支持 method: {method}")

        expected = case["expected"]
        assert_status_code(resp, expected["status_code"])
        if "ret" in expected:
            assert_business_code(resp, expected["ret"], field="ret")
        # 可检查 msg
        if "msg" in expected:
            json_data = get_json(resp)
            assert expected["msg"] in json_data.get("message", ""), f"错误信息不符: {json_data}"

    @allure.story("用户登录")
    @pytest.mark.parametrize("case", login_cases)
    def test_login(self, case, request, existing_user_fixture):
        # 类似实现，根据 preconditions 提供 existing_username 等
        ...

    @allure.story("获取个人信息")
    @pytest.mark.parametrize("case", info_cases)
    def test_get_user_info(self, case, request, logged_user):
        # 需要根据 preconditions 决定使用 logged_user 还是普通 client
        ...

    @allure.story("修改个人信息")
    @pytest.mark.parametrize("case", update_cases)
    def test_update_user_info(self, case, request, logged_user, other_logged_user):
        ...
