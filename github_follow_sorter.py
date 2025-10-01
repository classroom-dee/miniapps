#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

DO_UNFOLLOW_NONFOLLOWERS = True
DO_FOLLOW_BACK = True
DRY_RUN = False

BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}

def get_all(url):
    items, page = [], 1
    while True:
        r = requests.get(url, headers=HEADERS, params={"per_page": 100, "page": page})
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        items.extend(batch)
        page += 1
    return items

def usernames(objs):
    return {o["login"] for o in objs}

def main():
    if not GITHUB_TOKEN:
        raise SystemExit("Set GITHUB_TOKEN env var (PAT with user:follow scope).")

    following = usernames(get_all(f"{BASE}/users/{GITHUB_USERNAME}/following"))
    followers = usernames(get_all(f"{BASE}/users/{GITHUB_USERNAME}/followers"))

    nonfollowers = sorted(following - followers, key=str.lower)
    to_follow_back = sorted(followers - following, key=str.lower)

    print(f"You follow: {len(following)} | Followers: {len(followers)}")
    print(f"Don't follow back: {len(nonfollowers)}")
    print(f"Followers you don't follow yet: {len(to_follow_back)}")

    if DRY_RUN:
        print("\nDRY RUN — no changes will be made.")
        if DO_UNFOLLOW_NONFOLLOWERS and nonfollowers:
            print("\nWould unfollow:")
            for u in nonfollowers: print("→", u)
        if DO_FOLLOW_BACK and to_follow_back:
            print("\nWould follow back:")
            for u in to_follow_back: print("→", u)
        return

    # Unfollow non-followers
    if DO_UNFOLLOW_NONFOLLOWERS:
        for u in nonfollowers:
            r = requests.delete(f"{BASE}/user/following/{u}", headers=HEADERS)
            if r.status_code in (204, 404):
                print(f"Unfollowed {u}")
            else:
                print(f"Failed to unfollow {u}: {r.status_code} {r.text}")

    # Follow back
    if DO_FOLLOW_BACK:
        for u in to_follow_back:
            r = requests.put(f"{BASE}/user/following/{u}", headers=HEADERS)
            if r.status_code in (204, 304):  # 204 success; 304 already following
                print(f"Followed {u}")
            else:
                print(f"Failed to follow {u}: {r.status_code} {r.text}")

if __name__ == "__main__":
    main()