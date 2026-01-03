"""
GeminiBot: wrapper for Google Generative AI (Gemini) Python SDK

This module calls the official `google-generativeai` SDK using
the chat completions API when available, falling back to text generation.
It attempts to be defensive about different SDK response shapes.
"""

import os
import time
from typing import List, Dict, Optional, Any

try:
    import google.generativeai as genai
except Exception:
    genai = None


class GeminiBot:
    """
    Wrapper around Google Generative AI (Gemini) Python SDK.

    Usage:
        bot = GeminiBot(api_key="...")
        prompt = bot.build_prompt(memories, user_input, persona_desc="...")
        text = bot.generate_response(prompt)
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-1.5"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set. Please set it in environment or pass api_key")

        if genai is None:
            raise ImportError(
                "google.generativeai SDK is not installed or failed to import. Run: pip install google-generativeai"
            )

        # Configure SDK (different SDK versions expose different init methods)
        try:
            if hasattr(genai, "configure"):
                genai.configure(api_key=self.api_key)
            elif hasattr(genai, "init"):
                genai.init(api_key=self.api_key)
            else:
                # Some SDKs read env var
                os.environ.setdefault("GEMINI_API_KEY", self.api_key)
        except Exception:
            os.environ.setdefault("GEMINI_API_KEY", self.api_key)

    def build_prompt(self, memories: List[Dict[str, Any]], user_input: str, persona_desc: str = "") -> str:
        """
        Build an in-context prompt from memories and user input.
        Simple strategy: take last N messages and prepend persona description.
        """
        MAX_EXAMPLES = 6
        chosen = memories[-MAX_EXAMPLES:] if memories else []
        lines: List[str] = []
        if persona_desc:
            lines.append(f"Personality: {persona_desc}\n")
        lines.append("Conversation history (most recent first):")
        for m in reversed(chosen):
            sender = m.get("sender", "Unknown")
            content = m.get("content", "")
            lines.append(f"{sender}: {content}")
        lines.append("\nUser: " + user_input)
        lines.append("Assistant:")
        return "\n".join(lines)

    def _call_chat_api(self, prompt: str, max_output_tokens: int, temperature: float) -> Any:
        """Call the chat completions API if available.

        Returns the raw response object from the SDK.
        """
        # Build simple message list: system (optional persona) + user
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Typical SDK call (adjust kwargs as needed by SDK version)
        return genai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    def _call_text_api(self, prompt: str, max_output_tokens: int, temperature: float) -> Any:
        """Call the older text generation API if chat API isn't present."""
        return genai.generate_text(
            model=self.model,
            prompt=prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )

    def _extract_text(self, response: Any) -> str:
        """Attempt to extract text from several common response shapes."""
        # 1) genai.chat.completions.create typical shape: response.choices[0].message.content
        try:
            # attribute access
            if hasattr(response, "choices") and response.choices:
                first = response.choices[0]
                # message may be a dict-like or object
                if hasattr(first, "message") and hasattr(first.message, "get"):
                    # dict-like
                    return first.message.get("content") or str(first.message)
                elif hasattr(first, "message") and hasattr(first.message, "content"):
                    return first.message.content
                elif hasattr(first, "text"):
                    return first.text
        except Exception:
            pass

        # 2) genai.generate_text typical shape: response.candidates[0].output or .content
        try:
            if hasattr(response, "candidates") and response.candidates:
                cand = response.candidates[0]
                if hasattr(cand, "output"):
                    return cand.output
                if hasattr(cand, "content"):
                    return cand.content
                if hasattr(cand, "text"):
                    return cand.text
        except Exception:
            pass

        # 3) dict-like responses
        try:
            if isinstance(response, dict):
                # chat responses may contain choices -> message -> content
                choices = response.get("choices")
                if choices and len(choices) > 0:
                    first = choices[0]
                    if isinstance(first, dict):
                        msg = first.get("message") or first.get("delta") or first
                        if isinstance(msg, dict):
                            return msg.get("content") or msg.get("text") or str(msg)
                # try candidates
                cands = response.get("candidates") or response.get("outputs")
                if cands and len(cands) > 0:
                    first = cands[0]
                    if isinstance(first, dict):
                        return first.get("content") or first.get("output") or first.get("text") or str(first)
        except Exception:
            pass

        # 4) fallback to str
        return str(response)

    def generate_response(self, prompt: str, max_output_tokens: int = 512, temperature: float = 0.7, retry: int = 2) -> str:
        """Call the Gemini model and return text response.

        The method will try chat completions first (if available on the SDK), then
        fallback to text generation. It retries on exceptions using a small backoff.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(retry + 1):
            try:
                # Prefer chat API when available
                if genai and hasattr(genai, "chat") and hasattr(genai.chat, "completions"):
                    resp = self._call_chat_api(prompt, max_output_tokens, temperature)
                else:
                    resp = self._call_text_api(prompt, max_output_tokens, temperature)

                if resp is None:
                    raise RuntimeError("Empty response from model")

                text = self._extract_text(resp)
                return text

            except Exception as e:
                last_exc = e
                # simple exponential-ish backoff
                time.sleep(min(10, 1 + attempt * 2))
                continue

        raise RuntimeError(f"Model call failed after retries: {last_exc}")


if __name__ == "__main__":
    example_mem = [{"sender": "Alice", "content": "你今天怎么样？"}]
    bot = GeminiBot(api_key=os.getenv("GEMINI_API_KEY", ""), model="models/gemini-1.5")
    prompt = bot.build_prompt(example_mem, "介绍一下你自己", persona_desc="说话温柔，带幽默感")
    try:
        print("Prompt:\n", prompt)
        print("\nResponse:\n", bot.generate_response(prompt))
    except Exception as err:
        print("Error:", err)