"""End-to-end test: upload photos, run pipeline, check results."""

import asyncio
import base64
import sys
from pathlib import Path

# Ensure we can import from the backend
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings
from models.schemas import PhotoMeta, Session
from services.pipeline import AnalysisPipeline


async def main():
    settings = get_settings()
    print(f"Vision model: {settings.vision_model}")
    print(f"Text model:   {settings.text_model}")
    print(f"API key set:  {bool(settings.openrouter_api_key and settings.openrouter_api_key != 'sk-or-v1-your-key-here')}")
    print()

    photo_dir = Path.home() / "Desktop" / "site_examples"
    if not photo_dir.exists():
        print(f"ERROR: {photo_dir} not found")
        return

    session = Session()

    EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    MIME_MAP = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif",
    }
    for img_path in sorted(photo_dir.iterdir()):
        if img_path.suffix.lower() not in EXTENSIONS:
            continue
        raw = img_path.read_bytes()
        b64 = base64.b64encode(raw).decode()
        mime = MIME_MAP.get(img_path.suffix.lower(), "image/jpeg")
        meta = PhotoMeta(
            filename=img_path.name,
            mime_type=mime,
            b64_data=b64,
        )
        session.photos[meta.id] = meta
        print(f"  Loaded: {img_path.name} ({len(raw) // 1024}KB)")

    print(f"\nTotal photos: {len(session.photos)}")
    print("=" * 60)

    pipeline = AnalysisPipeline(session)

    try:
        async for event in pipeline.run():
            stage = event.get("stage", "?")
            progress = event.get("progress", 0)
            message = event.get("message", "")
            error = event.get("error")
            print(f"  [{stage}] {progress:.0%} — {message}")
            if error:
                print(f"  ERROR: {error}")
    except Exception as e:
        print(f"\nPIPELINE EXCEPTION: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print(f"Groups: {len(session.groups)}")
    for g in session.groups:
        print(f"  - {g.label} ({len(g.photo_ids)} photos, {len(g.key_photo_ids)} key)")

    print(f"\nFindings: {len(session.findings)}")
    for fid, f in session.findings.items():
        print(f"  - [{f.severity}] {f.observation[:80]}...")

    print(f"\nTemplate schema: {session.template_schema}")
    print("\nSUCCESS — pipeline completed end to end.")


if __name__ == "__main__":
    asyncio.run(main())
