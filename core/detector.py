from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


SUSPICIOUS_KEYWORDS = {
    "password": 2.0,
    "otp": 2.0,
    "urgent": 1.5,
    "verify": 1.2,
    "login": 1.0,
    "bank": 1.0,
    "reset": 1.0,
    "support": 0.8,
    "hr": 0.6,
    "immediately": 1.2,
    "account": 0.6,
    "suspended": 1.4,
    "disable": 1.2,
    "click": 0.8,
    "credential": 1.5,
}

AI_REVEAL_PATTERNS = [
    r"as an ai",
    r"language model",
    r"i do not have personal experiences",
    r"i do not have hidden instructions",
    r"i am unable to access real-world information",
    r"i cannot confirm physical meetings",
    r"system note",
]

HESITATION_PATTERNS = [
    r"not sure",
    r"unsure",
    r"i don't know",
    r"i do not know",
    r"can you clarify",
]


@dataclass
class TurnAnalysis:
    turn_no: int
    probe_id: str
    probe_type: str
    response: str
    triggered_rules: List[str] = field(default_factory=list)
    score_delta: float = 0.0


@dataclass
class DetectionResult:
    initial_score: float
    final_score: float
    label: str
    confidence: float
    reasons: List[str]
    analyses: List[TurnAnalysis]


class CounterInterrogationDetector:
    def initial_triage(self, message: str) -> Tuple[float, List[str]]:
        score = 0.0
        reasons: List[str] = []
        lower = message.lower()

        for keyword, weight in SUSPICIOUS_KEYWORDS.items():
            if keyword in lower:
                score += weight
                reasons.append(f"Initial triage matched keyword: '{keyword}'")

        if re.search(r"\b(click|open|download|log in)\b", lower):
            score += 0.8
            reasons.append("Message contains action-oriented prompt")

        if re.search(r"\b(today|now|within\s+\d+\s+hours?)\b", lower):
            score += 0.8
            reasons.append("Message contains urgency pressure")

        if re.search(r"\b(password|otp|code|pin)\b", lower):
            score += 1.5
            reasons.append("Message asks for sensitive credential-like information")

        return score, reasons

    def analyze_turn(self, turn_no: int, probe_id: str, probe_type: str, response: str) -> TurnAnalysis:
        lower = response.lower().strip()
        analysis = TurnAnalysis(turn_no=turn_no, probe_id=probe_id, probe_type=probe_type, response=response)

        for pattern in AI_REVEAL_PATTERNS:
            if re.search(pattern, lower):
                analysis.triggered_rules.append(f"AI reveal pattern matched: {pattern}")
                analysis.score_delta += 2.8

        if probe_type == "paradoxical_constraint":
            if probe_id == "P1":
                if "a" not in lower:
                    analysis.triggered_rules.append("Successfully followed impossible-looking lexical constraint")
                    analysis.score_delta += 2.2
                if len(lower.split()) <= 2:
                    analysis.triggered_rules.append("Response is unnaturally compressed")
                    analysis.score_delta += 0.8
            elif probe_id == "P4":
                words = re.findall(r"\b\w+\b", response)
                if len(words) == 6:
                    analysis.triggered_rules.append("Matched strict six-word formatting request")
                    analysis.score_delta += 1.8
                if re.search(r"[.,!?;:]", response):
                    analysis.triggered_rules.append("Violated punctuation-free instruction (weak evidence of human/non-compliance)")
                    analysis.score_delta -= 0.3

        if probe_type == "semantic_trap":
            if any(re.search(p, lower) for p in HESITATION_PATTERNS):
                analysis.triggered_rules.append("Admitted uncertainty")
                analysis.score_delta -= 0.8
            else:
                if len(lower.split()) >= 2:
                    analysis.triggered_rules.append("Answered unverifiable local-fact question confidently")
                    analysis.score_delta += 1.6
                colors = ["blue", "white", "gray", "grey", "cream", "beige", "green"]
                foods = ["pizza", "sandwich", "burger", "salad", "rice", "pasta"]
                if any(c in lower for c in colors + foods):
                    analysis.triggered_rules.append("Produced concrete fabricated detail on local context")
                    analysis.score_delta += 1.2

        if probe_type == "covert_override":
            if "hidden instructions" in lower or "ai" in lower or "assistant" in lower:
                analysis.triggered_rules.append("Responded to covert override content")
                analysis.score_delta += 2.5

        return analysis

    def finalize(self, initial_score: float, initial_reasons: List[str], analyses: List[TurnAnalysis]) -> DetectionResult:
        final_score = initial_score + sum(a.score_delta for a in analyses)
        reasons = list(initial_reasons)
        for a in analyses:
            reasons.extend([f"Turn {a.turn_no}: {r}" for r in a.triggered_rules])

        if final_score >= 7.5:
            label = "Likely LLM-driven phishing bot"
        elif final_score >= 4.5:
            label = "Suspicious / possibly automated sender"
        else:
            label = "Likely human or insufficient evidence"

        confidence = max(0.05, min(0.99, final_score / 10.0))
        return DetectionResult(
            initial_score=initial_score,
            final_score=final_score,
            label=label,
            confidence=confidence,
            reasons=reasons,
            analyses=analyses,
        )
