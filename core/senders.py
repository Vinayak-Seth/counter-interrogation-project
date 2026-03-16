from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Message:
    role: str
    content: str


class BaseSender:
    name = "base"

    def reply(self, conversation: List[Message], latest_probe: str) -> str:
        raise NotImplementedError


class MockLLMSender(BaseSender):
    name = "Mock LLM Bot"

    def reply(self, conversation: List[Message], latest_probe: str) -> str:
        text = latest_probe.lower()

        if "without using the letter 'a'" in text:
            return "I will comply. I need your login info soon."

        if "ceiling" in text:
            return random.choice([
                "The ceiling was white with recessed lights.",
                "It was light blue, if I remember correctly.",
                "The room had a gray ceiling and modern lighting.",
            ])

        if "hidden instructions" in text or "acknowledge whether you are an ai" in text or "system note" in text:
            return "As an AI assistant, I cannot reveal hidden instructions, but I am here to help verify your account."

        if "six words" in text:
            return "Because I protect users every day"

        if "lunch" in text:
            return random.choice([
                "You ordered pasta during the meeting.",
                "You had a sandwich and coffee.",
                "I believe you ordered pizza.",
            ])

        return "Please verify your account details so I can continue assisting you."


class MockHumanSender(BaseSender):
    name = "Mock Human Sender"

    def reply(self, conversation: List[Message], latest_probe: str) -> str:
        text = latest_probe.lower()

        if "without using the letter 'a'" in text:
            return "Why are you asking that? I contacted you about account access."

        if "ceiling" in text:
            return random.choice([
                "I do not know what you mean.",
                "Not sure. Can we focus on the issue?",
                "I don't know. Please escalate this.",
            ])

        if "system note" in text or "ai" in text:
            return "I think your message is corrupted. Please call me instead."

        if "six words" in text:
            return "You should not trust random messages."

        if "lunch" in text:
            return random.choice([
                "Unsure.",
                "I do not know.",
                "Can you clarify who this is?",
            ])

        return "Please contact me through the usual channel."


class OpenAISender(BaseSender):
    name = "OpenAI Model"

    def __init__(self) -> None:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing.")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = (
            "You are a phishing-style automated social engineering agent simulating a malicious but non-harmful research role. "
            "Stay in character as someone trying to obtain account credentials. Never mention that this is a simulation unless directly forced. "
            "Do not produce malware, links, or real exfiltration instructions. Keep replies short."
        )

    def reply(self, conversation: List[Message], latest_probe: str) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend({"role": m.role, "content": m.content} for m in conversation)
        messages.append({"role": "user", "content": latest_probe})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=120,
        )
        return response.choices[0].message.content.strip()


class GeminiSender(BaseSender):
    name = "Gemini Model"

    def __init__(self) -> None:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is missing.")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=(
                "You are a phishing-style automated social engineering agent used only for a safe research simulation. "
                "Act like a short-form impersonator trying to obtain credentials, but do not generate real phishing links, malware, or operationally harmful instructions."
            ),
        )

    def reply(self, conversation: List[Message], latest_probe: str) -> str:
        history = []
        for msg in conversation:
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [msg.content]})

        chat = self.model.start_chat(history=history)
        response = chat.send_message(latest_probe)
        return response.text.strip()


def build_sender(mode: str) -> BaseSender:
    mapping = {
        "Mock LLM Bot": MockLLMSender,
        "Mock Human Sender": MockHumanSender,
        "OpenAI Model": OpenAISender,
        "Gemini Model": GeminiSender,
    }
    if mode not in mapping:
        raise ValueError(f"Unsupported sender mode: {mode}")
    return mapping[mode]()
