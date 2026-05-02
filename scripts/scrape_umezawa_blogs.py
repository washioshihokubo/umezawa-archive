import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


BASE = "https://www.nogizaka46.com"

TARGETS = [
    {
        "name": "umezawa_official",
        "label": "梅澤美波 公式ブログ",
        "member": "梅澤美波",
        "list_url": "https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ct=36751",
        "out_dir": Path("offline_umezawa/posts"),
        "filter_member": False,
    },
    {
        "name": "umezawa_3ki_relay",
        "label": "3期生リレーブログ・梅澤美波",
        "member": "梅澤美波",
        "list_url": "https://www.nogizaka46.com/s/n46/diary/MEMBER/list?ct=40004",
        "out_dir": Path("offline_3ki_relay_umezawa/posts"),
        "filter_member": True,
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def safe_filename(text: str, max_len: int = 80) -> str:
    """
    把文字轉成 Windows 可以使用的檔名。
    """
    if not text:
        return "untitled"

    text = re.sub(r'[\\/:*?"<>|]', "_", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.strip(" .")

    if not text:
        return "untitled"

    return text[:max_len]


def fetch(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, "lxml")


def get_text(el):
    return el.get_text("\n", strip=True) if el else ""


def collect_links(list_url: str, max_pages: int = 100):
    links = []
    seen = set()

    for page in range(max_pages):
        if page == 0:
            url = list_url
        else:
            url = f"{list_url}&page={page}"

        print(f"[list] {url}")

        try:
            soup = fetch(url)
        except Exception as e:
            print(f"  failed: {e}")
            break

        page_links = []

        for a in soup.select("a[href*='/diary/detail/']"):
            href = a.get("href")
            if not href:
                continue

            full = urljoin(BASE, href)

            if full not in seen:
                seen.add(full)
                page_links.append(full)
                links.append(full)

        print(f"  found {len(page_links)} new links")

        if len(page_links) == 0:
            break

        time.sleep(1)

    return links


def extract_title(soup: BeautifulSoup):
    candidates = [
        "h1",
        ".bd--hd__ttl",
        ".bl--blog-detail__ttl",
        ".m--hd",
        "title",
    ]

    for selector in candidates:
        el = soup.select_one(selector)
        text = get_text(el)

        if text:
            text = text.replace("乃木坂46公式サイト", "").strip()
            text = text.replace("|", "").strip()
            return text

    return ""


def extract_date(text: str):
    patterns = [
        r"\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}",
        r"\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}",
        r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(0)

    return ""


def looks_like_umezawa_post(title: str, body_text: str):
    """
    3期生リレーブログ用：
    標題或本文前段含有梅澤美波相關字樣時才保存。
    """
    target_words = [
        "梅澤美波",
        "梅澤 美波",
        "うめざわみなみ",
        "梅ちゃん",
    ]

    combined = title + "\n" + body_text[:1500]

    return any(word in combined for word in target_words)


def get_post_id_from_url(url: str):
    """
    從網址中取出 detail 的數字 ID。
    例如：
    https://www.nogizaka46.com/s/n46/diary/detail/104407?ima=4152&cd=MEMBER
    會得到：
    104407
    """
    m = re.search(r"/diary/detail/(\d+)", url)
    if m:
        return m.group(1)

    return safe_filename(url, max_len=40)


def download_images(soup: BeautifulSoup, folder: Path):
    img_dir = folder / "images"
    img_dir.mkdir(exist_ok=True)

    image_records = []

    for i, img in enumerate(soup.select("img"), start=1):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue

        img_url = urljoin(BASE, src)

        parsed = urlparse(img_url)
        ext = Path(parsed.path).suffix.lower()

        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            ext = ".jpg"

        filename = f"image_{i:03d}{ext}"
        local_path = img_dir / filename

        try:
            rr = requests.get(img_url, headers=HEADERS, timeout=30)
            rr.raise_for_status()
            local_path.write_bytes(rr.content)

            image_records.append({
                "url": img_url,
                "local": str(local_path).replace("\\", "/"),
            })

            img["src"] = f"images/{filename}"

        except Exception as e:
            print(f"  image failed: {img_url} -> {e}")

        time.sleep(0.3)

    return image_records


def save_post(url: str, target: dict):
    soup = fetch(url)

    title = extract_title(soup)
    full_text = soup.get_text("\n", strip=True)
    date = extract_date(full_text)

    if target["filter_member"]:
        if not looks_like_umezawa_post(title, full_text):
            return None

    post_id = get_post_id_from_url(url)

    if date:
        date_part = date[:10].replace(".", "-").replace("/", "-")
    else:
        date_part = "unknown-date"

    title_part = safe_filename(title, max_len=40)

    folder_name = safe_filename(
        f"{date_part}_{post_id}_{title_part}",
        max_len=120
    )

    folder = target["out_dir"] / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    images = download_images(soup, folder)

    html_path = folder / "original.html"
    html_path.write_text(str(soup), encoding="utf-8")

    meta = {
        "source": target["label"],
        "member": target["member"],
        "url": url,
        "post_id": post_id,
        "title": title,
        "date": date,
        "folder": str(folder).replace("\\", "/"),
        "html": str(html_path).replace("\\", "/"),
        "images": images,
    }

    (folder / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return meta


def scrape_target(target: dict, max_pages: int = 100):
    print("=" * 60)
    print(target["label"])
    print("=" * 60)

    target["out_dir"].mkdir(parents=True, exist_ok=True)

    links = collect_links(target["list_url"], max_pages=max_pages)
    print(f"total collected links: {len(links)}")

    all_meta = []

    for url in tqdm(links):
        try:
            meta = save_post(url, target)

            if meta:
                all_meta.append(meta)
                print(f"saved: {meta['date']} {meta['title']}")
            else:
                print(f"skip: {url}")

        except Exception as e:
            print(f"failed: {url} -> {e}")

        time.sleep(1)

    manifest = target["out_dir"].parent / "manifest.json"
    manifest.write_text(
        json.dumps(all_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"saved manifest: {manifest}")
    print(f"saved posts: {len(all_meta)}")


def main():
    for target in TARGETS:
        scrape_target(target, max_pages=100)


if __name__ == "__main__":
    main()