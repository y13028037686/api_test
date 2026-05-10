import uuid

import pytest

from api.user_api import UserAPI
from api.post_api import PostAPI
from common.api_client import ApiClient
from common.assert_utils import assert_status_code, extract_token
from common.cleanup import CleanupManager
from config.settings import load_settings


@pytest.fixture
def api_client(settings):
    client = ApiClient(
        base_url=settings["base_url"],
        timeout=settings.get("timeout", 10),
        retries=settings.get("retries", 2)
    )

    yield client

    client.clear_token()
    client.close()


@pytest.fixture
def user_api(api_client):
    return UserAPI(api_client)


@pytest.fixture
def post_api(api_client):
    return PostAPI(api_client)


@pytest.fixture
def logged_user(settings):
    """
    独立登录用户。
    每个需要鉴权的用例单独生成 client，避免 token 串用。
    """
    client = ApiClient(
        base_url=settings["base_url"],
        timeout=settings.get("timeout", 10),
        retries=settings.get("retries", 2)
    )

    user_api = UserAPI(client)

    username = generate_username()
    password = settings["account"]["default_password"]

    register_resp = user_api.register(username, password)
    assert_status_code(register_resp, 200)

    login_resp = user_api.login(username, password)
    assert_status_code(login_resp, 200)

    token = extract_token(login_resp)
    client.set_token(token)

    user_info = {
        "username": username,
        "password": password,
        "token": token
    }

    yield client, user_info

    client.clear_token()
    client.close()


@pytest.fixture
def auth_user_api(logged_user):
    client, _ = logged_user
    return UserAPI(client)


@pytest.fixture
def auth_post_api(logged_user):
    client, _ = logged_user
    return PostAPI(client)

# ---------- 用户相关 ----------
@pytest.fixture(scope="session")
def existing_user_fixture(settings):
    """返回一个已存在的用户名，用于测试用户名已存在场景"""
    username = "existing_test_user"
    password = settings["account"]["default_password"]
    client = ApiClient(settings["base_url"])
    user_api = UserAPI(client)
    # 尝试注册，如果已存在则忽略错误
    resp = user_api.register(username, password)
    if resp.status_code == 409:
        # 用户已存在，直接使用
        pass
    else:
        assert_status_code(resp, 200)
    yield username, password, None
    # 不清理，保留用于后续测试


@pytest.fixture
def other_logged_user(settings):
    """另一个登录用户，与 logged_user 独立"""
    client = ApiClient(settings["base_url"])
    user_api = UserAPI(client)
    username = generate_username("other")
    password = settings["account"]["default_password"]
    user_api.register(username, password)
    login_resp = user_api.login(username, password)
    assert_status_code(login_resp, 200)
    token = extract_token(login_resp)
    client.set_token(token)
    yield client, {"username": username, "password": password, "token": token}
    client.clear_token()
    client.close()


# ---------- 文章相关 ----------
@pytest.fixture
def existing_post(auth_post_api, cleanup_manager):
    """创建一个普通存在的文章，返回 post_id，自动清理"""
    resp = auth_post_api.create(title="测试文章", content="内容")
    assert_status_code(resp, 200)
    post_id = get_json(resp).get("data", {}).get("id")
    if post_id:
        cleanup_manager.add(auth_post_api.delete, post_id)
    return post_id


@pytest.fixture
def my_post_exists(auth_post_api, cleanup_manager):
    """返回包含 post_id 和 token 的字典"""
    resp = auth_post_api.create(title="我的文章", content="内容")
    assert_status_code(resp, 200)
    post_id = get_json(resp).get("data", {}).get("id")
    token = auth_post_api.client.session.headers.get("Authorization", "").replace("Bearer ", "")
    cleanup_manager.add(auth_post_api.delete, post_id)
    return {"post_id": post_id, "token": token}


@pytest.fixture
def other_post_exists(settings, cleanup_manager):
    """由另一个用户创建的文章"""
    # 创建其他用户并登录
    client = ApiClient(settings["base_url"])
    user_api = UserAPI(client)
    username = generate_username("other")
    password = settings["account"]["default_password"]
    user_api.register(username, password)
    login_resp = user_api.login(username, password)
    assert_status_code(login_resp, 200)
    token = extract_token(login_resp)
    client.set_token(token)
    post_api = PostAPI(client)
    resp = post_api.create(title="他人的文章", content="内容")
    assert_status_code(resp, 200)
    post_id = get_json(resp).get("data", {}).get("id")
    cleanup_manager.add(post_api.delete, post_id)
    return {"post_id": post_id, "token": token}


@pytest.fixture
def multiple_posts_fixture(auth_post_api, cleanup_manager):
    """创建多篇文章用于分页测试"""
    for i in range(25):
        resp = auth_post_api.create(title=f"文章{i}", content=f"内容{i}")
        assert_status_code(resp, 200)
        post_id = get_json(resp).get("data", {}).get("id")
        if post_id:
            cleanup_manager.add(auth_post_api.delete, post_id)
    return True


@pytest.fixture
def posts_with_keyword_fixture(auth_post_api, cleanup_manager):
    """创建包含特定关键字的文章"""
    resp = auth_post_api.create(title="包含测试关键字的文章", content="测试内容")
    assert_status_code(resp, 200)
    post_id = get_json(resp).get("data", {}).get("id")
    if post_id:
        cleanup_manager.add(auth_post_api.delete, post_id)
    return True


@pytest.fixture
def deleted_post_fixture(auth_post_api, cleanup_manager):
    """创建一个已删除的文章，返回其 ID"""
    resp = auth_post_api.create(title="待删除", content="删除内容")
    assert_status_code(resp, 200)
    post_id = get_json(resp).get("data", {}).get("id")
    if post_id:
        auth_post_api.delete(post_id)
        # 不需要再额外清理，因为已经删除
    return post_id




# ---------- 评论相关 ----------
@pytest.fixture
def existing_comment_fixture(settings, logged_user, existing_post, cleanup_manager):
    """创建一个存在的评论"""
    client, _ = logged_user
    # 需要 CommentAPI，假设存在
    from api.comment_api import CommentAPI
    comment_api = CommentAPI(client)
    resp = comment_api.create(post_id=existing_post, content="测试评论")
    assert_status_code(resp, 200)
    comment_id = get_json(resp).get("data", {}).get("id")
    if comment_id:
        cleanup_manager.add(comment_api.delete, comment_id)
    return comment_id


@pytest.fixture
def my_comment_fixture(logged_user, existing_post, cleanup_manager):
    """我的评论"""
    client, _ = logged_user
    from api.comment_api import CommentAPI
    comment_api = CommentAPI(client)
    resp = comment_api.create(post_id=existing_post, content="我的评论")
    assert_status_code(resp, 200)
    comment_id = get_json(resp).get("data", {}).get("id")
    cleanup_manager.add(comment_api.delete, comment_id)
    return comment_id


@pytest.fixture
def other_comment_fixture(settings, cleanup_manager):
    """他人的评论"""
    # 创建其他用户
    client = ApiClient(settings["base_url"])
    user_api = UserAPI(client)
    username = generate_username("other")
    password = settings["account"]["default_password"]
    user_api.register(username, password)
    login_resp = user_api.login(username, password)
    token = extract_token(login_resp)
    client.set_token(token)

    # 创建一篇文章（用这个用户的身份）
    post_api = PostAPI(client)
    post_resp = post_api.create(title="他人文章", content="内容")
    assert_status_code(post_resp, 200)
    post_id = get_json(post_resp).get("data", {}).get("id")

    # 创建评论
    from api.comment_api import CommentAPI
    comment_api = CommentAPI(client)
    comment_resp = comment_api.create(post_id=post_id, content="他人评论")
    assert_status_code(comment_resp, 200)
    comment_id = get_json(comment_resp).get("data", {}).get("id")

    cleanup_manager.add(post_api.delete, post_id)
    return {"comment_id": comment_id}


@pytest.fixture
def deleted_comment_fixture(logged_user, existing_post):
    """已删除的评论"""
    client, _ = logged_user
    from api.comment_api import CommentAPI
    comment_api = CommentAPI(client)
    resp = comment_api.create(post_id=existing_post, content="待删除评论")
    assert_status_code(resp, 200)
    comment_id = get_json(resp).get("data", {}).get("id")
    comment_api.delete(comment_id)
    return {"comment_id": comment_id}


@pytest.fixture
def post_with_comments_fixture(settings, logged_user, cleanup_manager):
    """创建一篇文章并添加多条评论，返回 post_id"""
    client, _ = logged_user
    post_api = PostAPI(client)
    post_resp = post_api.create(title="有评论的文章", content="内容")
    assert_status_code(post_resp, 200)
    post_id = get_json(post_resp).get("data", {}).get("id")
    # 添加几条评论
    from api.comment_api import CommentAPI
    comment_api = CommentAPI(client)
    for i in range(3):
        comment_api.create(post_id=post_id, content=f"评论{i}")
    cleanup_manager.add(post_api.delete, post_id)
    return post_id


@pytest.fixture
def post_without_comments_fixture(settings, logged_user, cleanup_manager):
    """创建一篇没有评论的文章"""
    client, _ = logged_user
    post_api = PostAPI(client)
    post_resp = post_api.create(title="无评论文章", content="内容")
    assert_status_code(post_resp, 200)
    post_id = get_json(post_resp).get("data", {}).get("id")
    cleanup_manager.add(post_api.delete, post_id)
    return post_id


# ---------- 点赞相关 ----------
@pytest.fixture
def already_liked_post_fixture(logged_user, existing_post, cleanup_manager):
    """创建一篇已经被当前用户点赞的文章"""
    client, _ = logged_user
    # 点赞
    resp = client.post(f"/posts/{existing_post}/like")
    assert_status_code(resp, 200)
    # 返回文章 id
    return {"post_id": existing_post}



# ---------- 过期 token ----------
@pytest.fixture
def expired_token_fixture(settings, logged_user):
    """构造一个过期的 token（通过篡改或等待）"""
    client, user_info = logged_user
    token = user_info["token"]
    invalid_token = token[:-1] + ('A' if token[-1] != 'A' else 'B')
    return invalid_token

def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        help="运行环境：dev / test"
    )


def generate_username(prefix: str = "test_user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def settings(pytestconfig):
    env = pytestconfig.getoption("--env")
    return load_settings(env)


@pytest.fixture
def cleanup_manager():
    manager = CleanupManager()
    yield manager
    manager.run()
