import os
import requests


def post_wordpress(title: str, content: str) -> str:
    wp_url = os.getenv("WORDPRESS_URL", "").strip().rstrip("/")
    wp_user = os.getenv("WORDPRESS_USER", "").strip()
    wp_pass = os.getenv("WORDPRESS_APP_PASSWORD", "").strip()
    if not (wp_url and wp_user and wp_pass):
        return ""

    endpoint = f"{wp_url}/wp-json/wp/v2/posts"
    r = requests.post(
        endpoint,
        json={"title": title, "content": content, "status": "publish"},
        auth=(wp_user, wp_pass),
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("link", "") or ""
