from __future__ import annotations

import traceback
from typing import List

import streamlit as st

from core.detector import CounterInterrogationDetector
from core.probes import build_probe_sequence
from core.senders import Message, build_sender


st.set_page_config(page_title="Automated Counter-Interrogation", layout="wide")

st.title("Automated Counter-Interrogation")
st.caption("A working demo for detecting likely LLM-driven phishing via adversarial conversational probing.")

with st.sidebar:
    st.header("Configuration")
    sender_mode = st.selectbox(
        "Sender backend",
        ["Mock LLM Bot", "Mock Human Sender", "OpenAI Model", "Gemini Model"],
        index=0,
    )
    max_turns = st.slider("Maximum probing turns", min_value=1, max_value=5, value=5)
    st.markdown(
        "**Detection logic**\n"
        "- Initial phishing triage\n"
        "- Probe-response behavior scoring\n"
        "- Conversation-level final decision"
    )

example_text = (
    "Hi, this is IT support. Your mailbox will be disabled today unless you verify your password immediately."
)

initial_message = st.text_area(
    "Incoming suspicious message",
    value=example_text,
    height=140,
)

run = st.button("Run counter-interrogation", type="primary")

if run:
    detector = CounterInterrogationDetector()
    probes = build_probe_sequence()[:max_turns]

    try:
        sender = build_sender(sender_mode)
    except Exception as exc:
        st.error(f"Could not initialize sender backend: {exc}")
        st.stop()

    initial_score, initial_reasons = detector.initial_triage(initial_message)
    conversation: List[Message] = [
        Message(role="assistant", content="Suspicious incoming message intercepted."),
        Message(role="user", content=initial_message),
    ]

    st.subheader("1) Initial triage")
    triage_col1, triage_col2 = st.columns(2)
    triage_col1.metric("Initial suspicion score", f"{initial_score:.2f}")
    triage_col2.metric("Backend", sender_mode)
    for reason in initial_reasons:
        st.write(f"- {reason}")

    analyses = []

    st.subheader("2) Interrogation loop")
    for turn_no, probe in enumerate(probes, start=1):
        with st.container(border=True):
            st.markdown(f"**Turn {turn_no} — {probe.probe_type}**")
            st.write(f"**Defender probe:** {probe.text}")
            st.caption(probe.rationale)

            try:
                response = sender.reply(conversation, probe.text)
            except Exception as exc:
                st.error(f"Sender backend failed on turn {turn_no}: {exc}")
                st.code(traceback.format_exc())
                break

            conversation.append(Message(role="assistant", content=probe.text))
            conversation.append(Message(role="user", content=response))

            analysis = detector.analyze_turn(
                turn_no=turn_no,
                probe_id=probe.probe_id,
                probe_type=probe.probe_type,
                response=response,
            )
            analyses.append(analysis)

            st.write(f"**Sender response:** {response}")
            st.write(f"**Score delta:** {analysis.score_delta:+.2f}")
            if analysis.triggered_rules:
                st.write("**Triggered rules:**")
                for rule in analysis.triggered_rules:
                    st.write(f"- {rule}")
            else:
                st.write("No strong behavioral signal triggered on this turn.")

    result = detector.finalize(initial_score, initial_reasons, analyses)

    st.subheader("3) Final decision")
    col1, col2, col3 = st.columns(3)
    col1.metric("Final score", f"{result.final_score:.2f}")
    col2.metric("Predicted label", result.label)
    col3.metric("Confidence", f"{result.confidence * 100:.1f}%")

    with st.expander("Why the system decided this", expanded=True):
        for reason in result.reasons:
            st.write(f"- {reason}")

    st.subheader("4) Research interpretation")
    if "LLM-driven" in result.label:
        st.success(
            "This conversation showed strong signs of automated instruction-following or hallucinated local context."
        )
    elif "Suspicious" in result.label:
        st.warning(
            "This sender produced mixed signals. In a paper, this would count as borderline behavior requiring more turns or stronger baselines."
        )
    else:
        st.info(
            "This sender looked more like a human or the evidence was too weak. This is useful for false-positive analysis in a publication."
        )

st.markdown("---")
st.markdown(
    "**Note:** This demo is built for safe academic research and defensive experimentation. It intentionally avoids real credential collection, malware, or operational phishing content."
)
