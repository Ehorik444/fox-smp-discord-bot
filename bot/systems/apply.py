applications = []


def create_application(user_id, nickname, reason):
    app = {
        "user_id": user_id,
        "nickname": nickname,
        "reason": reason,
        "status": "pending"
    }

    applications.append(app)
    return app


def get_pending():
    return [a for a in applications if a["status"] == "pending"]


def accept(index):
    applications[index]["status"] = "accepted"
    return applications[index]


def deny(index):
    applications[index]["status"] = "denied"
    return applications[index]
