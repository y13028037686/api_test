# common/test_helper.py
import json
from copy import deepcopy
from typing import Dict, Any, Optional

import allure
import pytest
from requests import Response

from common.assert_utils import assert_status_code, assert_business_code, get_json
from common.logger import logger


def replace_template(obj: Any, variables: Dict[str, Any]) -> Any:
    """
    递归替换字符串中的 {{key}} 为 variables[key] 的值。
    支持嵌套的 dict、list 和 str。
    """
    if isinstance(obj, dict):
        return {k: replace_template(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_template(item, variables) for item in obj]
    elif isinstance(obj, str):
        result = obj
        for key, val in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(val))
        return result
    else:
        return obj


def get_fixture_value(request: pytest.FixtureRequest, name: str, default: Any = None) -> Any:
    """安全获取 fixture 值，如果不存在或抛出异常则返回 default"""
    try:
        return request.getfixturevalue(name)
    except (pytest.FixtureLookupError, Exception):
        return default


def build_variables_from_preconditions(
    case: Dict, request: pytest.FixtureRequest
) -> Dict[str, Any]:
    """
    根据用例中的 preconditions 列表，自动调用对应的 fixture，
    并构建一个变量字典，用于模板替换。
    约定：
        - "logged_in"  -> 需要 logged_user fixture，提供 token
        - "other_user_logged_in" -> other_logged_user fixture，提供 other_token
        - "existing_user" -> existing_user_fixture，提供 existing_username
        - "post_exists" / "my_post_exists" -> existing_post / my_post_exists，提供 post_id
        - "other_post_exists" -> other_post_exists，提供 other_post_id
        - "multiple_posts" -> multiple_posts_fixture，可能不需要变量
        - "post_with_comments" / "post_without_comments" -> 提供 post_id
        - "my_comment_exists" / "other_comment_exists" / "comment_exists" -> 提供 comment_id
        - "already_liked" -> already_liked_post fixture，提供 post_id
        - "categories_exist" -> categories_fixture (可选)
        - "expired_token" -> expired_token_fixture，提供 expired_token
        - "deleted_post_exists" -> deleted_post_fixture，提供 deleted_post_id
    """
    variables = {}
    preconditions = case.get("preconditions", [])

    # 处理登录相关
    if "logged_in" in preconditions:
        logged = get_fixture_value(request, "logged_user")
        if logged:
            client, user_info = logged
            variables["token"] = user_info.get("token", "")
    if "other_user_logged_in" in preconditions:
        other_logged = get_fixture_value(request, "other_logged_user")
        if other_logged:
            other_client, other_info = other_logged
            variables["other_token"] = other_info.get("token", "")
            variables["other_user_id"] = other_info.get("username", "")  # 可能需要

    # 处理已存在用户
    if "existing_user" in preconditions:
        existing = get_fixture_value(request, "existing_user_fixture")
        if existing:
            username, _, _ = existing
            variables["existing_username"] = username

    # 处理文章相关
    if "post_exists" in preconditions:
        post_id = get_fixture_value(request, "existing_post")
        if post_id:
            variables["post_id"] = post_id
    if "my_post_exists" in preconditions:
        post_info = get_fixture_value(request, "my_post_exists")
        if post_info:
            variables["post_id"] = post_info.get("post_id")
            # token 可能已经在 logged_in 中提供
    if "other_post_exists" in preconditions:
        other_post = get_fixture_value(request, "other_post_exists")
        if other_post:
            variables["other_post_id"] = other_post.get("post_id")
            variables["other_token"] = other_post.get("token")
    if "deleted_post_exists" in preconditions:
        deleted_id = get_fixture_value(request, "deleted_post_fixture")
        if deleted_id:
            variables["deleted_post_id"] = deleted_id
    if "draft_post_exists" in preconditions:
        draft = get_fixture_value(request, "draft_post_fixture")
        if draft:
            variables["draft_post_id"] = draft.get("post_id")
            variables["draft_token"] = draft.get("token")

    # 处理评论相关
    if "my_comment_exists" in preconditions:
        comment_id = get_fixture_value(request, "my_comment_fixture")
        if comment_id:
            variables["comment_id"] = comment_id
    if "other_comment_exists" in preconditions:
        other_comment = get_fixture_value(request, "other_comment_fixture")
        if other_comment:
            variables["other_comment_id"] = other_comment.get("comment_id")
    if "comment_exists" in preconditions:
        comment_id = get_fixture_value(request, "existing_comment_fixture")
        if comment_id:
            variables["comment_id"] = comment_id
    if "deleted_comment_exists" in preconditions:
        deleted_comment = get_fixture_value(request, "deleted_comment_fixture")
        if deleted_comment:
            variables["deleted_comment_id"] = deleted_comment.get("comment_id")

    # 处理点赞相关
    if "already_liked" in preconditions:
        liked_post = get_fixture_value(request, "already_liked_post_fixture")
        if liked_post:
            variables["post_id"] = liked_post.get("post_id")

    # 处理多文章列表
    if "multiple_posts" in preconditions:
        # 只需要确保有足够文章，不需要变量
        get_fixture_value(request, "multiple_posts_fixture")

    # 处理带关键字的文章搜索
    if "posts_with_keyword" in preconditions:
        get_fixture_value(request, "posts_with_keyword_fixture")

    # 处理评论列表
    if "post_with_comments" in preconditions:
        post_id = get_fixture_value(request, "post_with_comments_fixture")
        if post_id:
            variables["post_id"] = post_id
    if "post_without_comments" in preconditions:
        post_id = get_fixture_value(request, "post_without_comments_fixture")
        if post_id:
            variables["post_id"] = post_id

    # 处理分类存在
    if "categories_exist" in preconditions:
        get_fixture_value(request, "categories_fixture")

    # 处理过期 token
    if "expired_token" in preconditions:
        expired = get_fixture_value(request, "expired_token_fixture")
        if expired:
            variables["expired_token"] = expired

    # 处理长字符串、超长关键字等
    if "{{long_signature}}" in str(case):
        variables["long_signature"] = "a" * 201
    if "{{long_title}}" in str(case):
        variables["long_title"] = "a" * 101
    if "{{long_keyword}}" in str(case):
        variables["long_keyword"] = "a" * 1000

    return variables


def get_api_client_from_preconditions(
    case: Dict, request: pytest.FixtureRequest, default_client_name: str = "api_client"
):
    """
    根据用例的 preconditions 返回合适的 ApiClient 实例。
    如果包含 "logged_in"，则使用 logged_user 的 client；
    否则使用 default_client_name 对应的 fixture（通常是无认证的 api_client）。
    """
    preconditions = case.get("preconditions", [])
    if "logged_in" in preconditions:
        logged = get_fixture_value(request, "logged_user")
        if logged:
            client, _ = logged
            return client
    # 未登录场景
    return get_fixture_value(request, default_client_name)


def execute_case(
    case: Dict,
    request: pytest.FixtureRequest,
    skip_status_check: bool = False,
    custom_assertions: Optional[callable] = None,
) -> Response:
    """
    执行单个 YAML 用例。
     - 根据 preconditions 构建变量字典
     - 替换请求中的模板变量
     - 获取合适的 ApiClient
     - 发送请求
     - 执行状态码断言 & 业务码断言
     - 返回 Response 对象，以便额外断言
    """
    # 1. 构建变量
    variables = build_variables_from_preconditions(case, request)

    # 2. 获取请求定义并替换模板
    raw_request = deepcopy(case["request"])
    req = replace_template(raw_request, variables)

    method = req["method"].lower()
    url = req["url"]
    headers = req.get("headers", {})
    body = req.get("body", {})
    params = req.get("params", {})

    # 3. 获取 client
    client = get_api_client_from_preconditions(case, request, "api_client")

    # 4. 发送请求
    logger.info(f"执行用例 {case['id']}: {case['description']}")
    logger.debug(f"请求: {method.upper()} {url}, headers={headers}, params={params}, body={body}")
    with allure.step(f"{case['id']}: {case['description']}"):
        if method == "get":
            resp = client.get(url, headers=headers, params=params)
        elif method == "post":
            resp = client.post(url, headers=headers, json_body=body, params=params)
        elif method == "put":
            resp = client.put(url, headers=headers, json_body=body, params=params)
        elif method == "delete":
            resp = client.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"不支持的 method: {method}")

    # 5. 断言
    expected = case["expected"]
    if not skip_status_check:
        assert_status_code(resp, expected["status_code"])

    if "ret" in expected:
        assert_business_code(resp, expected["ret"], field="ret")
    if "msg" in expected:
        json_data = get_json(resp)
        assert expected["msg"] in json_data.get("message", ""), f"错误信息不符: {json_data}"
    if "token_returned" in expected and expected["token_returned"]:
        # 确保 token 字段存在且非空
        json_data = get_json(resp)
        token = json_data.get("token") or (json_data.get("data", {}).get("token"))
        assert token, "响应中没有 token 字段"
    if "empty_list" in expected and expected["empty_list"]:
        json_data = get_json(resp)
        if isinstance(json_data.get("data"), list):
            assert len(json_data["data"]) == 0, "列表应为空"
        else:
            assert not json_data.get("data") or len(json_data["data"]) == 0
    if "list_length" in expected:
        json_data = get_json(resp)
        data = json_data.get("data") or json_data.get("items") or []
        assert len(data) == expected["list_length"], f"列表长度不符: 期望 {expected['list_length']}, 实际 {len(data)}"

    if custom_assertions:
        custom_assertions(resp, expected)

    return resp
