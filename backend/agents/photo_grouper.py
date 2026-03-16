"""Stage 2: Group related photo analyses and select key photos per group."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from agents.base import BaseLLMAgent
from models.schemas import PhotoAnalysis, PhotoGroup
from services import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert at organizing architectural inspection findings. "
    "Given individual photo analyses from a site visit, group them by the "
    "underlying issue they represent. Photos of the same defect from different "
    "angles or locations should be grouped together."
)

USER_PROMPT_TEMPLATE = """\
Here are individual photo analyses from a site visit. Each has a photo_id.

{analyses_json}

Group these photos by the issue they represent. For each group:
1. Give it a short descriptive label.
2. List all photo_ids that belong to the group.
3. Select the 1-3 most representative/important photo_ids as key photos.

Respond with ONLY valid JSON (no markdown):
{{
  "groups": [
    {{
      "label": "Short issue label",
      "photo_ids": ["id1", "id2"],
      "key_photo_ids": ["id1"]
    }}
  ]
}}
"""


class PhotoGrouperAgent(BaseLLMAgent):
    name = "photo_grouper"

    async def execute(
        self,
        analyses: dict[str, PhotoAnalysis],
    ) -> list[PhotoGroup]:
        summaries = [
            {
                "photo_id": a.photo_id,
                "description": a.description,
                "issues": a.issues,
                "severity": a.severity,
                "location_hint": a.location_hint,
                "tags": a.tags,
            }
            for a in analyses.values()
        ]

        prompt = USER_PROMPT_TEMPLATE.format(
            analyses_json=json.dumps(summaries, indent=2)
        )

        data = await llm_client.chat_json(
            prompt,
            system=SYSTEM_PROMPT,
            model=self.text_model,
        )

        groups: list[PhotoGroup] = []
        for g in data.get("groups", []):
            groups.append(
                PhotoGroup(
                    id=str(uuid.uuid4()),
                    label=g["label"],
                    photo_ids=g["photo_ids"],
                    key_photo_ids=g.get("key_photo_ids", g["photo_ids"][:1]),
                )
            )
        return groups
