"""Full HTTP integration test against the running server."""

import json
import sys
import time
from pathlib import Path

import httpx

BASE = "http://localhost:8111/api"
PHOTO_DIR = Path.home() / "Desktop" / "site_examples"


def main():
    client = httpx.Client(timeout=120)

    # -- 1. Upload --
    print("=== UPLOAD ===")
    files = []
    for p in sorted(PHOTO_DIR.iterdir()):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
            files.append(("photos", (p.name, p.read_bytes(), mime)))

    if not files:
        print("ERROR: no image files found in", PHOTO_DIR)
        sys.exit(1)

    print(f"  Uploading {len(files)} photos...")
    r = client.post(f"{BASE}/upload", files=files)
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  Body: {r.text}")
        sys.exit(1)
    data = r.json()
    session_id = data["session_id"]
    print(f"  Session: {session_id}")
    print(f"  Photos:  {data['photo_count']}")

    # -- 2. Analyze (SSE stream) --
    print("\n=== ANALYZE (SSE stream) ===")
    with client.stream("POST", f"{BASE}/sessions/{session_id}/analyze") as resp:
        print(f"  Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  ERROR: {resp.read().decode()}")
            sys.exit(1)
        for line in resp.iter_lines():
            if line.startswith("data: "):
                evt = json.loads(line[6:])
                print(f"  [{evt['stage']}] {evt['progress']:.0%} — {evt['message']}")
                if evt.get("error"):
                    print(f"  ERROR: {evt['error']}")

    # -- 3. Get results --
    print("\n=== RESULTS ===")
    r = client.get(f"{BASE}/sessions/{session_id}/results")
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  Body: {r.text}")
        sys.exit(1)
    results = r.json()
    groups = results["groups"]
    findings = results["findings"]
    print(f"  Groups:   {len(groups)}")
    for g in groups:
        print(f"    - {g['label']} ({len(g['photo_ids'])} photos)")
    print(f"  Findings: {len(findings)}")
    for fid, f in findings.items():
        print(f"    - [{f['severity']}] {f['observation'][:60]}...")
    print(f"  Photos (b64 keys): {len(results['photos'])}")

    # -- 4. Test review endpoints --
    print("\n=== REVIEW: edit finding ===")
    if findings:
        fid = list(findings.keys())[0]
        r = client.patch(
            f"{BASE}/sessions/{session_id}/findings/{fid}",
            json={"observation": "EDITED: Test observation override"},
        )
        print(f"  Patch status: {r.status_code}")
        if r.status_code == 200:
            print(f"  Updated observation: {r.json()['observation'][:60]}...")

    # -- 5. Download ZIP --
    print("\n=== DOWNLOAD ZIP ===")
    r = client.get(f"{BASE}/sessions/{session_id}/download")
    print(f"  Status: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('content-type')}")
    print(f"  Size: {len(r.content) // 1024}KB")

    if r.status_code == 200:
        out = Path("/tmp/vitruvius_test_output.zip")
        out.write_bytes(r.content)
        print(f"  Saved to: {out}")

        import zipfile
        with zipfile.ZipFile(out) as zf:
            print(f"  ZIP contents ({len(zf.namelist())} files):")
            for name in zf.namelist():
                info = zf.getinfo(name)
                print(f"    {name} ({info.file_size // 1024}KB)")

    print("\n=== ALL TESTS PASSED ===")


if __name__ == "__main__":
    main()
