import time

cooldowns = {}

DAILY_LIMIT = {}


def check_cooldown(user_id: int, seconds: int = 60):
    now = time.time()

    if user_id in cooldowns:
        if now - cooldowns[user_id] < seconds:
            return False

    cooldowns[user_id] = now
    return True


def check_daily_limit(user_id: int):
    today = time.strftime("%Y-%m-%d")

    if user_id not in DAILY_LIMIT:
        DAILY_LIMIT[user_id] = {"date": today, "count": 0}

    if DAILY_LIMIT[user_id]["date"] != today:
        DAILY_LIMIT[user_id] = {"date": today, "count": 0}

    if DAILY_LIMIT[user_id]["count"] >= 1:
        return False

    DAILY_LIMIT[user_id]["count"] += 1
    return True
