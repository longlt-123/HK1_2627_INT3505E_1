class APIProblem(Exception):
    def __init__(self, status, title, detail, type_path, instance_path):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.instance_path = instance_path

        super().__init__(f"[{status}] {title}")

    def to_dict(self):
        return {
            "type": self.type_path,
            "title": self.title,
            "detail": self.detail,
            "instance": self.instance_path,
            "status": self.status
        }


class CreatePostProblem(APIProblem):
    def __init__(self, detail="Missing author_id, title or content."):
        super().__init__(
            status=400,
            title="Invalid post data",
            detail=detail,
            type_path="/probs/invalid-post-data",
            instance_path="/api/v1/posts"
        )


class GetPostDetailProblem(APIProblem):
    def __init__(self, post_id):
        super().__init__(
            status=404,
            title="Post not found",
            detail=f"Post with id {post_id} does not exist.",
            type_path="/probs/post-not-found",
            instance_path=f"/api/v1/posts/{post_id}"
        )


class GetPostCommentsProblem(APIProblem):
    def __init__(self, post_id):
        super().__init__(
            status=404,
            title="Post not found",
            detail=f"Cannot get comments because post with id {post_id} does not exist.",
            type_path="/probs/post-not-found",
            instance_path=f"/api/v1/posts/{post_id}/comments"
        )