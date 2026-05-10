import json
from urllib.parse import urljoin

import allure
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from urllib3.util.retry import Retry

from common.logger import logger


class ApiClient:
    """
    企业级接口请求客户端：
    1. 多环境 base_url
    2. 默认超时
    3. 自动重试
    4. token 管理
    5. 请求响应日志
    6. Allure 请求响应附件
    7. 支持 GET / POST / PUT / PATCH / DELETE
    """

    def __init__(self, base_url: str, timeout: int = 10, retries: int = 2):
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        retry_strategy = Retry(
            total=retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            raise_on_status=False
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def set_token(self, token: str, token_type: str = "Bearer") -> None:
        if not token:
            raise ValueError("token 不能为空")

        self.session.headers.update({
            "Authorization": f"{token_type} {token}"
        })

    def clear_token(self) -> None:
        self.session.headers.pop("Authorization", None)

    def close(self) -> None:
        self.session.close()

    def build_url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint

        return urljoin(self.base_url, endpoint.lstrip("/"))

    def _attach_allure(self, title: str, content) -> None:
        try:
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False, indent=2)
            else:
                content = str(content)

            allure.attach(
                content,
                name=title,
                attachment_type=allure.attachment_type.JSON
            )
        except Exception:
            pass

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params=None,
        json_body=None,
        data=None,
        files=None,
        headers=None,
        timeout=None,
        **kwargs
    ):
        method = method.upper()
        url = self.build_url(endpoint)
        timeout = timeout or self.timeout

        request_info = {
            "method": method,
            "url": url,
            "params": params,
            "json": json_body,
            "data": data,
            "headers": headers
        }

        logger.info(f"接口请求：{request_info}")
        self._attach_allure("Request", request_info)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_body,
                data=data,
                files=files,
                headers=headers,
                timeout=timeout,
                **kwargs
            )

            logger.info(f"响应状态码：{response.status_code}")
            logger.info(f"响应内容：{response.text}")

            self._attach_allure("Response Status Code", response.status_code)
            self._attach_allure("Response Body", response.text)

            return response

        except RequestException as e:
            logger.exception(f"接口请求异常：{method} {url}")
            raise AssertionError(f"接口请求异常：{method} {url}，原因：{e}") from e

    def get(self, endpoint: str, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs):
        return self.request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs):
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        return self.request("DELETE", endpoint, **kwargs)
