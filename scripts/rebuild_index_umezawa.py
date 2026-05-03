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
        return "3期生リレー", "source-3ki"
    return "N46 BLOG", "source-n46"


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

            source_label, source_class = normalize_source(item.get("source", ""))
            item["_source_label"] = source_label
            item["_source_class"] = source_class

            posts.append(item)

    posts.sort(key=lambda x: x["_datetime"], reverse=False)
    return posts


def build_html(posts):
    by_year = defaultdict(list)

    for p in posts:
        if p["_year"] != "unknown":
            by_year[p["_year"]].append(p)

    years = sorted(by_year.keys())

    year_nav = "\n".join(
        f"    <a class='year-chip' href='#year-{year}'>{year} 年</a>"
        for year in years
    )

    year_blocks = []

    for year in years:
        rows = []

        for p in by_year[year]:
            title = html.escape(p.get("title", "無題"))
            date_raw = p.get("date", "")
            date_short = html.escape(date_raw[:10].replace(".", "-").replace("/", "-"))
            source_label = html.escape(p.get("_source_label", "N46 BLOG"))
            source_class = html.escape(p.get("_source_class", "source-n46"))
            link = html.escape((p.get("readable") or p.get("html", "")).replace("\\", "/"))

            rows.append(f"""
      <div class='row'>
        <div class='col-date'>{date_short}</div>
        <div class='col-source'>
          <span class='tag-source {source_class}'>{source_label}</span>
        </div>
        <div class='col-title'>
          <a class='post-link' href='{link}'>{title}</a>
        </div>
      </div>""")

        year_blocks.append(f"""
  <div class='year-block' id='year-{year}'>
    <div class='year-title'>{year} 年</div>
    <div class='list'>
      {''.join(rows)}
    </div>
  </div>""")

    total = len(posts)
    official_count = sum(1 for p in posts if p.get("_source_class") == "source-n46")
    relay_count = sum(1 for p in posts if p.get("_source_class") == "source-3ki")

    return f"""<!DOCTYPE html>
<html lang='ja'>
<head>
  <meta charset='utf-8' />
  <title>梅澤美波　デビューから現在までの全ブログ</title>

  <style>
    * {{ box-sizing:border-box; }}

    body {{
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",
                  "Hiragino Sans","Noto Sans JP",sans-serif;
      margin:0;
      background:
        linear-gradient(rgba(2, 6, 23, 0.60), rgba(15, 23, 42, 0.65)),
        url('ume.jpg') no-repeat center center fixed;
      background-size: cover;
    }}

    .wrapper {{
      max-width:980px;
      margin:0 auto;
      padding:24px 14px 40px;
    }}

    h1 {{
      font-size:2rem;
      letter-spacing:.06em;
      margin:0 0 .3em;
      color:#fff;
    }}

    .subtitle {{
      font-size:.9rem;
      color:#d1d5db;
      margin-bottom:1.5rem;
      line-height:1.6;
    }}

    .nav-years {{
      display:flex;
      flex-wrap:wrap;
      gap:8px;
      margin-bottom:1.5rem;
      justify-content:center;
    }}

    .year-chip {{
      padding:4px 10px;
      border-radius:999px;
      border:1px solid #4b5563;
      font-size:.8rem;
      color:#e5e7eb;
      text-decoration:none;
    }}

    .year-chip:hover {{
      border-color:#c4b5fd;
      background:rgba(124,58,237,0.25);
    }}

    .year-block {{
      max-width:980px;
      margin:1.8rem auto 0;
      padding:.5rem 14px 0;
      border-top:1px solid #1f2937;
    }}

    .year-title {{
      font-size:1.2rem;
      font-weight:600;
      margin-bottom:.5rem;
      color:#f9fafb;
    }}

    .list {{
      border-radius:10px;
      background: rgba(15, 23, 42, 0.10);
      backdrop-filter: blur(2px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      overflow:hidden;
    }}

    .row {{
      display:flex;
      flex-wrap:wrap;
      align-items:center;
      padding:6px 10px;
      font-size:.86rem;
      border-bottom:1px solid #111827;
      background: rgba(15, 23, 42, 0.03);
    }}

    .row:last-child {{
      border-bottom:none;
    }}

    .row:nth-child(2n) {{
      background: rgba(15, 23, 42, 0.07);
    }}

    .col-date {{
      width:110px;
      color:#d1d5db;
    }}

    .col-source {{
      width:110px;
    }}

    .tag-source {{
      display:inline-block;
      padding:2px 8px;
      border-radius:999px;
      font-size:.72rem;
      color:#fff;
      font-weight:600;
    }}

    .col-title {{
      flex:1;
      min-width:140px;
    }}

    a.post-link {{
      color:#f3f4f6;
      text-decoration:none;
    }}

    a.post-link:hover {{
      text-decoration:underline;
      color:#ddd6fe;
    }}

    .source-n46 {{
      background:#7c3aed;
    }}

    .source-3ki {{
      background:#10b981;
    }}

    .top-links {{
      margin-top:1rem;
      font-size:.8rem;
    }}

    .top-links a {{
      color:#c4b5fd;
      text-decoration:none;
      margin-right:1rem;
    }}

    .top-links a:hover {{
      text-decoration:underline;
    }}

    .header-center {{
      text-align: center;
    }}

    .header-center .top-links {{
      display: flex;
      justify-content: center;
      gap: 1rem;
      flex-wrap: wrap;
    }}

    .header-center .subtitle {{
      margin-left: auto;
      margin-right: auto;
      line-height: 1.6;
    }}

    @media (max-width:640px){{
      .col-date {{ width:88px; }}
      .col-source {{ width:96px; margin-bottom:2px; }}
      .row {{ align-items:flex-start; }}
    }}
  </style>
</head>

<body>
  <div class='wrapper header-center'>
    <h1>梅澤美波　デビューから現在までの全ブログ</h1>

    <div class='subtitle'>
      乃木坂46公式ブログ、3期生リレーブログの記事を、日付順に並べたオフラインのタイムラインです。<br>
      各行のタイトルをクリックすると、保存したHTMLが開きます。<br>
      Total：{total} posts ／ 乃木坂46 公式ブログ：{official_count} posts ／ 3期生リレー：{relay_count} posts
    </div>

    <div class='top-links'>
      <a href='index.html'>全文タイムライン</a>
      <a href='#year-2016'>デビュー年へ</a>
    </div>
  </div>

  <div class='nav-years'>
{year_nav}
  </div>

{''.join(year_blocks)}

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