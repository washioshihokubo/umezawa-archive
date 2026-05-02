import json
import html
import re
import os
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString, Tag


TARGETS = [
    Path("offline_umezawa/posts"),
    Path("offline_3ki_relay_umezawa/posts"),
]


def parse_date(date_text):
    for fmt in ["%Y.%m.%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(date_text, fmt)
        except Exception:
            pass
    return datetime.min


def clean_soup(soup):
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    return soup


def is_noise_text(text):
    if not text:
        return True

    noise_words = [
        "ニュース",
        "スケジュール",
        "メンバー",
        "ブログ",
        "ディスコグラフィー",
        "ムービー",
        "ゲームアプリ",
        "ミート＆グリート",
        "ライブ",
        "乃木坂工事中",
        "グッズ",
        "JASRAC",
        "©乃木坂46LLC",
        "購入・ダウンロード",
        "ストリーミング",
        "メンバーを選択",
        "決定する",
        "FAQ",
        "CONTACT",
        "COPIED",
        "English",
        "简体中文",
        "繁體中文",
        "한국어",
        "Bahasa",
    ]

    return any(word in text for word in noise_words)


def find_article_area(soup):
    selectors = [
        "article",
        ".bd--edit",
        ".bl--blog-detail__txt",
        ".bl--blog-detail",
        ".blog-detail",
        ".entrybody",
        ".entry-body",
        ".diary",
        "main",
    ]

    for selector in selectors:
        el = soup.select_one(selector)
        if el and len(el.get_text(strip=True)) > 50:
            return el

    return soup.body if soup.body else soup


def simplify_content(article_area, meta):
    title = meta.get("title", "").strip()
    date = meta.get("date", "").strip()

    output = []
    started = False

    for node in article_area.descendants:
        if isinstance(node, NavigableString):
            text = str(node).strip()
            if not text:
                continue

            if title and title in text:
                started = True
                continue

            if date and date in text:
                started = True
                continue

            if not started and len(text) >= 8 and not is_noise_text(text):
                started = True

            if not started:
                continue

            if is_noise_text(text):
                continue

            if text == title or text == date:
                continue

            if re.search(r"前の記事|次の記事|公式ブログ|年月|日 月 火 水 木 金 土", text):
                continue

            escaped = html.escape(text)
            output.append(f"<p>{escaped}</p>")

        elif isinstance(node, Tag) and node.name == "img":
            src = node.get("src") or node.get("data-src")
            if not src:
                continue

            alt = html.escape(node.get("alt", ""))
            output.append(f'<figure><img src="{html.escape(src)}" alt="{alt}"></figure>')

    if len(output) < 3:
        return str(article_area)

    return "\n".join(output)


def collect_all_posts():
    posts = []

    for posts_dir in TARGETS:
        if not posts_dir.exists():
            continue

        for folder in posts_dir.iterdir():
            if not folder.is_dir():
                continue

            meta_path = folder / "metadata.json"
            original_path = folder / "original.html"

            if not meta_path.exists() or not original_path.exists():
                continue

            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            meta["_folder"] = folder
            meta["_readable_path"] = folder / "readable.html"
            meta["_datetime"] = parse_date(meta.get("date", ""))

            posts.append(meta)

    posts.sort(key=lambda x: x["_datetime"], reverse=False)
    return posts


def relative_path(from_folder: Path, target_path: Path):
    return os.path.relpath(target_path, start=from_folder).replace("\\", "/")


def make_nav_link(current_folder, post, label):
    if not post:
        return f'<span class="disabled">{label}</span>'

    target = post["_readable_path"]
    href = html.escape(relative_path(current_folder, target))
    title = html.escape(post.get("title", "無題"))
    date = html.escape(post.get("date", "")[:10].replace(".", "-").replace("/", "-"))

    return f'''
    <a class="article-nav-link" href="{href}">
      <span class="nav-label">{label}</span>
      <span class="nav-title">{title}</span>
      <span class="nav-date">{date}</span>
    </a>
    '''


def make_readable(meta, prev_post=None, next_post=None):
    folder = meta["_folder"]
    original_path = folder / "original.html"

    soup = BeautifulSoup(
        original_path.read_text(encoding="utf-8", errors="ignore"),
        "lxml"
    )
    soup = clean_soup(soup)

    article_area = find_article_area(soup)
    content_html = simplify_content(article_area, meta)

    title = html.escape(meta.get("title", "無題"))
    date = html.escape(meta.get("date", ""))
    source = html.escape(meta.get("source", ""))
    url = html.escape(meta.get("url", ""))

    if "3期生" in source:
        source_short = "3期生リレーブログ"
        source_class = "relay"
    else:
        source_short = "乃木坂46 公式ブログ"
        source_class = "official"

    source_short = html.escape(source_short)

    index_href = html.escape(relative_path(folder, Path("index.html")))

    prev_link = make_nav_link(folder, prev_post, "← 前の記事")
    next_link = make_nav_link(folder, next_post, "次の記事 →")

    readable = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * {{
      box-sizing: border-box;
    }}

    html {{
      scroll-behavior: smooth;
    }}

    body {{
      margin: 0;
      font-family: "Yu Gothic", "Hiragino Sans", "Meiryo", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(190, 160, 255, 0.18), transparent 34%),
        linear-gradient(180deg, #fbf9ff 0%, #ffffff 46%, #f7f3ff 100%);
      color: #26212f;
      line-height: 2;
      letter-spacing: 0.02em;
    }}

    .page {{
      max-width: 900px;
      margin: 0 auto;
      padding: 34px 18px 90px;
    }}

    .top-nav {{
      margin-bottom: 22px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .top-nav a {{
      display: inline-block;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.88);
      border: 1px solid rgba(105, 80, 160, 0.18);
      color: #5b478c;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
      box-shadow: 0 5px 16px rgba(80, 60, 120, 0.06);
    }}

    .article-card {{
      background: rgba(255, 255, 255, 0.94);
      border: 1px solid rgba(105, 80, 160, 0.16);
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 14px 36px rgba(80, 60, 120, 0.10);
    }}

    .article-header {{
      padding: 42px 42px 30px;
      background:
        linear-gradient(135deg, rgba(96, 72, 150, 0.96), rgba(204, 185, 255, 0.92));
      color: white;
    }}

    .source {{
      display: inline-block;
      padding: 5px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: rgba(255, 255, 255, 0.22);
      border: 1px solid rgba(255, 255, 255, 0.34);
      margin-bottom: 16px;
    }}

    h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.45;
      letter-spacing: 0.05em;
      font-weight: 700;
    }}

    .date {{
      margin-top: 16px;
      font-size: 15px;
      opacity: 0.92;
      font-weight: 600;
    }}

    .body {{
      padding: 40px 42px 52px;
      font-size: 16px;
    }}

    .body p {{
      margin: 0 0 1.1em;
      white-space: pre-wrap;
    }}

    .body figure {{
      margin: 30px auto;
      text-align: center;
    }}

    .body img {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
      border-radius: 14px;
      box-shadow: 0 10px 24px rgba(50, 40, 80, 0.10);
    }}

    .original {{
      margin-top: 38px;
      padding-top: 22px;
      border-top: 1px solid rgba(105, 80, 160, 0.16);
      font-size: 13px;
      color: #777;
      word-break: break-all;
    }}

    .original a {{
      color: #6b4fa3;
    }}

    .article-nav {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
      margin-top: 26px;
    }}

    .article-nav-link,
    .disabled {{
      display: block;
      min-height: 92px;
      padding: 16px 18px;
      border-radius: 18px;
      text-decoration: none;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid rgba(105, 80, 160, 0.16);
      box-shadow: 0 8px 22px rgba(80, 60, 120, 0.07);
    }}

    .article-nav-link:hover {{
      background: #f3edff;
    }}

    .disabled {{
      color: #aaa;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .nav-label {{
      display: block;
      font-size: 13px;
      color: #6b4fa3;
      font-weight: 700;
      margin-bottom: 5px;
    }}

    .nav-title {{
      display: block;
      color: #282132;
      font-weight: 700;
      line-height: 1.55;
    }}

    .nav-date {{
      display: block;
      margin-top: 5px;
      color: #777;
      font-size: 12px;
    }}

    .bottom-nav {{
      margin-top: 28px;
      text-align: center;
    }}

    .bottom-nav a {{
      display: inline-block;
      padding: 10px 18px;
      border-radius: 999px;
      background: #6b4fa3;
      color: #fff;
      text-decoration: none;
      font-weight: 700;
      box-shadow: 0 8px 22px rgba(80, 60, 120, 0.22);
    }}

    @media (max-width: 720px) {{
      .page {{
        padding: 20px 12px 70px;
      }}

      .article-header {{
        padding: 30px 24px 24px;
      }}

      h1 {{
        font-size: 26px;
      }}

      .body {{
        padding: 28px 24px 40px;
        font-size: 15px;
      }}

      .article-nav {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="top-nav">
      <a href="{index_href}">← タイムラインに戻る</a>
      <a href="{url}" target="_blank">Original URL</a>
    </div>

    <article class="article-card">
      <header class="article-header">
        <div class="source {source_class}">{source_short}</div>
        <h1>{title}</h1>
        <div class="date">{date}</div>
      </header>

      <main class="body">
        {content_html}

        <div class="original">
          Source：{source}<br>
          Original：<a href="{url}" target="_blank">{url}</a>
        </div>
      </main>
    </article>

    <nav class="article-nav">
      {prev_link}
      {next_link}
    </nav>

    <div class="bottom-nav">
      <a href="{index_href}">タイムラインに戻る</a>
    </div>
  </div>
</body>
</html>
"""

    readable_path = folder / "readable.html"
    readable_path.write_text(readable, encoding="utf-8")

    meta["readable"] = str(readable_path).replace("\\", "/")

    meta_for_json = dict(meta)
    meta_for_json.pop("_folder", None)
    meta_for_json.pop("_readable_path", None)
    meta_for_json.pop("_datetime", None)

    meta_path = folder / "metadata.json"
    meta_path.write_text(
        json.dumps(meta_for_json, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return True


def main():
    posts = collect_all_posts()

    total = 0

    for i, meta in enumerate(posts):
        prev_post = posts[i - 1] if i > 0 else None
        next_post = posts[i + 1] if i < len(posts) - 1 else None

        if make_readable(meta, prev_post, next_post):
            total += 1

    print(f"created readable.html for {total} posts")


if __name__ == "__main__":
    main()