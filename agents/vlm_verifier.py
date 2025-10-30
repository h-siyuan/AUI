import json
import base64
from typing import List, Dict, Any, Optional

from pathlib import Path


class VLMVerifier:
    """VLM-based screenshot verifier (B1/B2 arms)

    - Strict JSON output, no fallbacks
    - Retries: 429 errors and JSON-parse failures, up to 5
    - Supports models configured in utils.model_client.ModelClient
    - Modes:
        * screenshot_only (B1)
        * screenshot_expected (B2)
    """

    def __init__(self, model_client):
        self.model_client = model_client

    async def verify(
        self,
        vlm_model: str,
        mode: str,
        task_desc: str,
        screenshots: List[str],
        *,
        expected_text: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if mode not in ("screenshot_only", "screenshot_expected"):
            raise ValueError("mode must be 'screenshot_only' or 'screenshot_expected'")

        prompt = self._build_prompt(mode, task_desc, expected_text)

        # Prepare images per model pathway
        if vlm_model == 'gpt5':
            # GPT-5 helper expects raw base64 (it wraps into data URL internally)
            images = [self._to_base64_for_gpt5(s) for s in screenshots]
        else:
            # Other callers accept file paths or data URLs; client handles encoding
            images = list(screenshots)

        # Retry policy: 5 attempts for 429 or JSON parse issues, no fallbacks
        last_error = None
        for attempt in range(5):
            try:
                if vlm_model == 'gpt5':
                    # Keep verbosity minimal for speed and stability
                    response_text = await self.model_client.call_model_with_gpt5_params(
                        vlm_model, prompt, images, temperature=temperature, verbosity="low", reasoning_effort="minimal"
                    )
                else:
                    response_text = await self.model_client.call_model(vlm_model, prompt, images, temperature=temperature)

                parsed = self._parse_verdict_json(response_text)
                # Basic schema checks
                if parsed.get('verdict') not in ('pass', 'fail'):
                    raise ValueError("invalid verdict")
                if 'confidence' not in parsed:
                    raise ValueError("missing confidence")
                if 'reason' not in parsed:
                    raise ValueError("missing reason")
                if 'used_screenshots' not in parsed:
                    raise ValueError("missing used_screenshots")
                return parsed
            except Exception as e:
                # ModelClient already internally retries API; here we only handle parse/format
                last_error = e
                # Continue retrying up to 5 attempts
                continue

        raise last_error if last_error else RuntimeError("verifier failed after 5 attempts")

    def _build_prompt(self, mode: str, task_desc: str, expected_text: Optional[str]) -> str:
        from .prompts.verifier_prompts import (
            build_verifier_screenshot_only_prompt,
            build_verifier_screenshot_expected_prompt,
        )
        if mode == 'screenshot_only':
            return build_verifier_screenshot_only_prompt(task_desc)
        else:
            if not expected_text:
                raise ValueError("expected_text is required for screenshot_expected mode")
            return build_verifier_screenshot_expected_prompt(task_desc, expected_text)

    def _parse_verdict_json(self, text: str) -> Dict[str, Any]:
        content = text
        if '```json' in content:
            try:
                content = content.split('```json')[1].split('```')[0]
            except Exception:
                pass
        elif '```' in content:
            try:
                content = content.split('```')[1].split('```')[0]
            except Exception:
                pass
        return json.loads(content)

    def _to_base64_for_gpt5(self, img: str) -> str:
        """Normalize input to raw base64 for GPT-5 path.
        - If data URL: strip prefix and return base64 part
        - If filesystem path: read and base64-encode
        - Else assume it's already raw base64
        """
        s = img.strip()
        if s.startswith("data:image"):
            # Typical form: data:image/png;base64,<B64>
            if 'base64,' in s:
                return s.split('base64,', 1)[1]
            # Fallback to last comma split if uncommon form
            parts = s.split(',', 1)
            return parts[1] if len(parts) == 2 else s
        # Heuristic: path-like strings with separators and reasonable length
        if (("/" in s or "\\" in s) and not s.startswith(("iVBOR", "/9j", "UklG")) and len(s) < 1000):
            with open(s, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        # Assume already raw base64
        return s
