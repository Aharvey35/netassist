from pathlib import Path
import yaml

# === File paths ===
RANK_SCHEMA_FILE = Path("data/rank_schema.yaml")
USER_PROFILES_FILE = Path("data/user_profiles.yaml")

# === YAML Helpers ===
def load_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

# === Core Functions ===
def load_user(username):
    ranks = load_yaml(RANK_SCHEMA_FILE)["ranks"]
    users = load_yaml(USER_PROFILES_FILE)

    if username not in users:
        users[username] = create_default_user(ranks[0])
        save_yaml(USER_PROFILES_FILE, users)

    return users[username]

def save_user(username, profile):
    users = load_yaml(USER_PROFILES_FILE)
    users[username] = profile
    save_yaml(USER_PROFILES_FILE, users)

def create_default_user(rank):
    return {
        "xp": 0,
        "title": rank["title"],
        "level": rank["level"],
        "badge": rank["badge"]
    }

def get_rank(xp, ranks):
    for rank in reversed(ranks):
        if xp >= rank["xp_required"]:
            return rank
    return ranks[0]

def award_xp(username, amount):
    ranks = load_yaml(RANK_SCHEMA_FILE)["ranks"]
    users = load_yaml(USER_PROFILES_FILE)

    if username not in users:
        users[username] = create_default_user(ranks[0])

    users[username]["xp"] += amount
    new_rank = get_rank(users[username]["xp"], ranks)

    users[username]["title"] = new_rank["title"]
    users[username]["level"] = new_rank["level"]
    users[username]["badge"] = new_rank["badge"]

    save_yaml(USER_PROFILES_FILE, users)
    return users[username]

def get_rank_info(level):
    ranks = load_yaml(RANK_SCHEMA_FILE)["ranks"]
    for rank in ranks:
        if rank["level"] == level:
            return rank
    return ranks[0]
