from common.api_client import ApiClient


class UserAPI:
    def __init__(self, client: ApiClient):
        self.client = client

    def register(self, username: str, password: str):
        return self.client.post(
            "/user/register",
            json_body={
                "username": username,
                "password": password
            }
        )

    def login(self, username: str, password: str):
        return self.client.post(
            "/user/login",
            json_body={
                "username": username,
                "password": password
            }
        )

    def get_info(self):
        return self.client.get("/user/info")

    def logout(self):
        return self.client.post("/user/logout")
