import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE = "https://www.nogizaka46.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

TARGETS = [
    {
        "label": "梅澤美波 公式ブログ",
        "list_url": "https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ct=36751",
        "manifest": Path("offline_umezawa/manifest.json"),
        "filter_relay": False,
    },
    {
        "label": "3期生リレーブログ・梅澤美波",
        "list_url": "https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ct=40004",
        "manifest": Path("offline_3ki_relay_umezawa/manifest.json"),
        "filter_relay": True,
    },
]


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "lxml")


def get_post_id(url):
    m = re.search(r"/diary/detail/(\d+)", url)
    return m.group(1) if m else None


def extract_title_from_list_item(a):
    text = a.get_text(" ", strip=True)
    return text


def is_umezawa_relay_title(title):
    title = title.strip()
    patterns = [
        r"梅澤美波\s*$",
        r"梅澤\s*美波\s*$",
        r"うめざわみなみ\s*$",
    ]
    return any(re.search(p, title) for p in patterns)


def collect_site_posts(target, max_pages=120):
    posts = {}
    seen = set()

    for page in range(max_pages):
        url = target["list_url"] if page == 0 else f"{target['list_url']}&page={page}"
        print(f"[site] {target['label']} page {page}: {url}")

        soup = fetch(url)
        new_count = 0

        for a in soup.select("a[href*='/diary/detail/']"):
            href = a.get("href")
            if not href:
                continue

            full_url = urljoin(BASE, href)
            post_id = get_post_id(full_url)

            if not post_id or post_id in seen:
                continue

            title = extract_title_from_list_item(a)

            if target["filter_relay"]:
                if not is_umezawa_relay_title(title):
                    continue

            seen.add(post_id)
            posts[post_id] = {
                "id": post_id,
                "title": title,
                "url": full_url,
            }
            new_count += 1

        print(f"  new matched posts: {new_count}")

        if new_count == 0:
            break

        time.sleep(1)

    return posts


def load_local_posts(manifest_path):
    if not manifest_path.exists():
        return {}

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    posts = {}

    for item in data:
        post_id = str(item.get("post_id", "")).strip()
        if post_id:
            posts[post_id] = item

    return posts


def main():
    for target in TARGETS:
        print("=" * 70)
        print(target["label"])
        print("=" * 70)

        site_posts = collect_site_posts(target)
        local_posts = load_local_posts(target["manifest"])

        site_ids = set(site_posts.keys())
        local_ids = set(local_posts.keys())

        missing_ids = sorted(site_ids - local_ids)
        extra_ids = sorted(local_ids - site_ids)

        print()
        print(f"網站目前數量：{len(site_ids)}")
        print(f"本機保存數量：{len(local_ids)}")

        if len(site_ids) == len(local_ids) and not missing_ids and not extra_ids:
            print("結果：數量一致，ID 也一致。")
        else:
            print("結果：不完全一致。")

        if missing_ids:
            print()
            print("本機缺少的文章：")
            for post_id in missing_ids:
                p = site_posts[post_id]
                print(f"- {post_id}｜{p['title']}｜{p['url']}")

        if extra_ids:
            print()
            print("本機多出、但目前網站列表沒有比對到的文章：")
            for post_id in extra_ids:
                p = local_posts[post_id]
                print(f"- {post_id}｜{p.get('title', '')}｜{p.get('url', '')}")

        print()


if __name__ == "__main__":
    main()