
from jsonschema import validate, ValidationError


def get_json(response):
    try:
        return response.json()
    except Exception as e:
        raise AssertionError(f"响应不是合法 JSON，响应内容：{response.text}") from e


def assert_status_code(response, expected: int):
    assert response.status_code == expected, (
        f"HTTP 状态码断言失败：期望 {expected}，实际 {response.status_code}，"
        f"响应内容：{response.text}"
    )


def assert_business_code(response, expected=200, field="code"):
    """
    业务状态码断言。
    常见响应：
    {
        "code": 200,
        "message": "success",
        "data": {}
    }
    """
    data = get_json(response)
    actual = data.get(field)

    assert actual == expected, (
        f"业务状态码断言失败：字段 {field}，期望 {expected}，实际 {actual}，完整响应：{data}"
    )


def assert_json_key_exists(response, key: str):
    data = get_json(response)

    assert key in data, (
        f"JSON 字段不存在：{key}，完整响应：{data}"
    )


def assert_json_value(response, key: str, expected):
    data = get_json(response)
    actual = data.get(key)

    assert actual == expected, (
        f"JSON 字段值断言失败：字段 {key}，期望 {expected}，实际 {actual}，完整响应：{data}"
    )


def assert_schema(response, schema: dict):
    data = get_json(response)

    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise AssertionError(f"JSON Schema 校验失败：{e.message}，完整响应：{data}") from e


def extract_token(response):
    """
    兼容两类返回结构：
    1. {"token": "..."}
    2. {"data": {"token": "..."}}
    """
    data = get_json(response)

    token = data.get("token")

    if not token and isinstance(data.get("data"), dict):
        token = data["data"].get("token")

    if not token:
        raise AssertionError(f"登录成功但未提取到 token，响应内容：{data}")

    return token
