from common.api_client import ApiClient

class CommentAPI:
    def __init__(self, client: ApiClient):
        self.client = client

    def create(self, post_id: int, content: str):
        return self.client.post("/comments", json_body={"post_id": post_id, "content": content})

    def delete(self, comment_id: int):
        return self.client.delete(f"/comments/{comment_id}")

    def list_by_post(self, post_id: int):
        return self.client.get("/comments", params={"post_id": post_id})
