"""Publishers. MVP ships dry-run only (spec 01 non-goals).

The dry-run checklist is concrete upload steps, not prose (spec 03).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Publisher(ABC):
    name: str = "abstract"

    @abstractmethod
    def publish(self, package: dict) -> dict:
        """package: refs + metadata. Returns a publish_result dict."""


class DryRunPublisher(Publisher):
    name = "dryrun"

    def publish(self, package: dict) -> dict:
        meta = package["metadata"]
        checklist = "\n".join(
            [
                "# Publish Checklist (dry run)",
                "",
                "Nothing was uploaded. To publish this package on YouTube:",
                "",
                f"1. Upload the video file: `{package['video_name']}`",
                f"2. Paste the title: {meta['title']}",
                "3. Paste the description from `metadata.json` (`description` key,",
                "   chapters included).",
                f"4. Add the tags from `metadata.json` ({len(meta['tags'])} tags).",
                f"5. Set the thumbnail: `{package['thumbnail_name']}`",
                f"6. Upload captions: `{package['captions_name']}` (language: "
                f"{package['language']}).",
                f"7. Category: {meta['category']}. Visibility: start with Unlisted,",
                "   review playback, then switch to Public.",
            ]
        )
        result = {
            "platform": "youtube",
            "mode": "dry_run",
            "uploaded": False,
            "video_id": None,
            "checklist": checklist,
        }
        return result
