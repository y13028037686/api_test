from common.api_client import ApiClient


class PostAPI:
    def __init__(self, client: ApiClient):
        self.client = client

    def create(self, title: str, content: str):
        return self.client.post(
            "/post",
            json_body={
                "title": title,
                "content": content
            }
        )

    def update(self, post_id: int, title: str, content: str):
        return self.client.put(
            f"/post/{post_id}",
            json_body={
                "title": title,
                "content": content
            }
        )

    def detail(self, post_id: int):
        return self.client.get(f"/post/{post_id}")

    def delete(self, post_id: int):
        return self.client.delete(f"/post/{post_id}")
