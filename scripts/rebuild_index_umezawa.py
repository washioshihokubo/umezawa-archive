import json
import html
from pathlib import Path
from datetime import datetime
from collections import defaultdict


MANIFESTS = [
    Path("offline_umezawa/manifest.json"),
    Path("offline_3ki_relay_umezawa/manifest.json"),
]

OUT = Path("index.html")


def parse_date(date_text):
    for fmt in ["%Y.%m.%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M"]:
        try:
            return datetime.strptime(date_text, fmt)
        except Exception:
            pass
    return datetime.min


def normalize_source(source):
    if "3期生" in source:
        return "3期生リレー"
    return "乃木坂46 公式ブログ"


def source_class_name(source_short):
    if source_short == "3期生リレー":
        return "relay"
    return "official"


def load_posts():
    posts = []

    for manifest in MANIFESTS:
        if not manifest.exists():
            print(f"not found: {manifest}")
            continue

        data = json.loads(manifest.read_text(encoding="utf-8"))

        for item in data:
            dt = parse_date(item.get("date", ""))
            item["_datetime"] = dt
            item["_year"] = dt.year if dt != datetime.min else "unknown"
            item["_source_short"] = normalize_source(item.get("source", ""))
            item["_source_class"] = source_class_name(item["_source_short"])
            posts.append(item)

    # 古い → 新しい。新しい順にしたい場合は reverse=True に変更
    posts.sort(key=lambda x: x["_datetime"], reverse=False)
    return posts


def build_html(posts):
    by_year = defaultdict(list)

    for p in posts:
        by_year[p["_year"]].append(p)

    years = sorted([y for y in by_year.keys() if y != "unknown"])

    year_nav = "\n".join(
        f'<a class="year-chip" href="#year-{year}">{year} 年</a>'
        for year in years
    )

    official_count = sum(1 for p in posts if p["_source_short"] == "乃木坂46 公式ブログ")
    relay_count = sum(1 for p in posts if p["_source_short"] == "3期生リレー")

    sections = []

    for year in years:
        items = []

        for p in by_year[year]:
            title = html.escape(p.get("title", "無題"))
            date_raw = p.get("date", "")
            date_short = html.escape(date_raw[:10].replace(".", "-").replace("/", "-"))
            source = html.escape(p.get("_source_short", ""))
            source_class = html.escape(p.get("_source_class", "official"))
            link = html.escape((p.get("readable") or p.get("html", "")).replace("\\", "/"))

            items.append(f"""
            <article class="timeline-item" data-source="{source_class}">
              <div class="date">{date_short}</div>
              <div class="source {source_class}">{source}</div>
              <a class="title" href="{link}" target="_blank">{title}</a>
            </article>
            """)

        sections.append(f"""
        <section class="year-section" id="year-{year}">
          <h2>{year} 年</h2>
          <div class="items">
            {''.join(items)}
          </div>
        </section>
        """)

    total = len(posts)

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>梅澤美波 全文タイムライン</title>
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
        radial-gradient(circle at top left, rgba(180, 150, 255, 0.22), transparent 32%),
        linear-gradient(180deg, #fbf9ff 0%, #ffffff 52%, #f7f3ff 100%);
      color: #25212d;
      line-height: 1.8;
    }}

    header {{
      padding: 72px 24px 46px;
      text-align: center;
      color: #fff;
      background:
        linear-gradient(135deg, rgba(80, 55, 130, 0.94), rgba(180, 155, 235, 0.92));
      box-shadow: 0 10px 30px rgba(70, 50, 120, 0.18);
    }}

    header h1 {{
      margin: 0;
      font-size: 38px;
      letter-spacing: 0.08em;
      font-weight: 700;
    }}

    header p {{
      margin: 16px auto 0;
      max-width: 780px;
      font-size: 15px;
      opacity: 0.94;
    }}

    .summary {{
      margin-top: 18px;
      font-size: 14px;
      opacity: 0.95;
    }}

    nav {{
      max-width: 980px;
      margin: 26px auto 0;
      padding: 0 20px;
      text-align: center;
    }}

    .source-nav {{
      margin-bottom: 18px;
    }}

    .filter-btn {{
      display: inline-block;
      margin: 4px 6px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid rgba(110, 82, 160, 0.18);
      color: #5b478c;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      font-family: inherit;
      box-shadow: 0 4px 12px rgba(80, 60, 120, 0.06);
    }}

    .filter-btn:hover,
    .filter-btn.active {{
      background: #6b4fa3;
      color: #fff;
    }}

    .year-nav {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 8px;
    }}

    .year-chip {{
      display: inline-block;
      padding: 7px 12px;
      border-radius: 999px;
      background: #ffffff;
      border: 1px solid rgba(110, 82, 160, 0.18);
      color: #5b478c;
      font-size: 13px;
      text-decoration: none;
      box-shadow: 0 4px 12px rgba(80, 60, 120, 0.06);
    }}

    .year-chip:hover {{
      background: #f0e9ff;
    }}

    main {{
      max-width: 980px;
      margin: 34px auto 90px;
      padding: 0 20px;
    }}

    .year-section {{
      margin-bottom: 48px;
      scroll-margin-top: 24px;
    }}

    .year-section h2 {{
      font-size: 30px;
      margin: 0 0 18px;
      padding-bottom: 8px;
      color: #4f3c82;
      border-bottom: 2px solid rgba(110, 82, 160, 0.22);
      letter-spacing: 0.05em;
    }}

    .items {{
      display: grid;
      gap: 12px;
    }}

    .timeline-item {{
      display: grid;
      grid-template-columns: 110px 150px 1fr;
      gap: 14px;
      align-items: center;
      padding: 15px 18px;
      background: rgba(255, 255, 255, 0.86);
      border: 1px solid rgba(110, 82, 160, 0.13);
      border-radius: 16px;
      box-shadow: 0 8px 22px rgba(80, 60, 120, 0.06);
      backdrop-filter: blur(8px);
    }}

    .date {{
      font-size: 14px;
      color: #655a72;
      font-weight: 700;
      white-space: nowrap;
    }}

    .source {{
      display: inline-block;
      width: fit-content;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}

    .source.official {{
      background: #eee7ff;
      color: #5b478c;
    }}

    .source.relay {{
      background: #f6e9ff;
      color: #7b4fa1;
    }}

    .title {{
      color: #2a2433;
      font-size: 16px;
      font-weight: 700;
      text-decoration: none;
    }}

    .title:hover {{
      color: #6b4fa3;
      text-decoration: underline;
    }}

    .back-top {{
      position: fixed;
      right: 18px;
      bottom: 18px;
      width: 44px;
      height: 44px;
      border-radius: 999px;
      background: #6b4fa3;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      text-decoration: none;
      box-shadow: 0 8px 20px rgba(80, 60, 120, 0.24);
      font-weight: bold;
    }}

    @media (max-width: 720px) {{
      header h1 {{
        font-size: 28px;
      }}

      .timeline-item {{
        grid-template-columns: 1fr;
        gap: 4px;
      }}

      .date {{
        font-size: 13px;
      }}

      .title {{
        font-size: 15px;
      }}
    }}
  </style>
</head>

<body id="top">
  <header>
    <h1>梅澤美波 全文タイムライン</h1>
    <p>乃木坂46公式ブログ、3期生リレーブログの記事を、日付順に並べたオフラインアーカイブです。</p>
    <div class="summary">
      Total：{total} posts ／ 乃木坂46 公式ブログ：{official_count} posts ／ 3期生リレー：{relay_count} posts
    </div>
  </header>

  <nav>
    <div class="source-nav">
      <button type="button" class="filter-btn active" data-filter="all">すべて</button>
      <button type="button" class="filter-btn" data-filter="official">乃木坂46 公式ブログ</button>
      <button type="button" class="filter-btn" data-filter="relay">3期生リレー</button>
    </div>

    <div class="year-nav">
      {year_nav}
    </div>
  </nav>

  <main>
    {''.join(sections)}
  </main>

  <a class="back-top" href="#top">↑</a>

  <script>
    const buttons = document.querySelectorAll('.filter-btn');
    const items = document.querySelectorAll('.timeline-item');
    const sections = document.querySelectorAll('.year-section');

    function applyFilter(filter) {{
      items.forEach(item => {{
        const matched = filter === 'all' || item.dataset.source === filter;
        item.style.display = matched ? 'grid' : 'none';
      }});

      sections.forEach(section => {{
        const visibleItems = Array.from(section.querySelectorAll('.timeline-item'))
          .filter(item => item.style.display !== 'none');

        section.style.display = visibleItems.length > 0 ? 'block' : 'none';
      }});

      buttons.forEach(btn => {{
        btn.classList.toggle('active', btn.dataset.filter === filter);
      }});
    }}

    buttons.forEach(btn => {{
      btn.addEventListener('click', () => {{
        applyFilter(btn.dataset.filter);
      }});
    }});
  </script>
</body>
</html>
"""


def main():
    posts = load_posts()
    html_text = build_html(posts)
    OUT.write_text(html_text, encoding="utf-8")
    print(f"rebuilt {OUT} with {len(posts)} posts")


if __name__ == "__main__":
    main()