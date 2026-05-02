import json
from pathlib import Path


TARGETS = [
    {
        "posts_dir": Path("offline_umezawa/posts"),
        "manifest": Path("offline_umezawa/manifest.json"),
    },
    {
        "posts_dir": Path("offline_3ki_relay_umezawa/posts"),
        "manifest": Path("offline_3ki_relay_umezawa/manifest.json"),
    },
]


def rebuild_manifest(posts_dir: Path, manifest_path: Path):
    records = []

    if not posts_dir.exists():
        print(f"not found: {posts_dir}")
        return

    for folder in posts_dir.iterdir():
        if not folder.is_dir():
            continue

        meta_path = folder / "metadata.json"

        if not meta_path.exists():
            print(f"skip, no metadata: {folder}")
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            records.append(meta)
        except Exception as e:
            print(f"failed: {meta_path} -> {e}")

    records.sort(key=lambda x: x.get("date", ""), reverse=True)

    manifest_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"rebuilt {manifest_path} with {len(records)} posts")


def main():
    for target in TARGETS:
        rebuild_manifest(target["posts_dir"], target["manifest"])


if __name__ == "__main__":
    main()