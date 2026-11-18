USERS = {
    1: {
        "id": 1,
        "first_name": "An",
        "last_name": "Nguyen",
        "email": "an.nguyen@example.com",
    },
    2: {
        "id": 2,
        "first_name": "Binh",
        "last_name": "Tran",
        "email": "binh.tran@example.com",
    },
}


def get_user(uid):
    """Return a user dict by id, or None if not found."""
    return USERS.get(uid)
