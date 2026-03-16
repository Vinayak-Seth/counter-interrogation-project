# Automated Counter-Interrogation Demo

A working research prototype that simulates **active conversational probing** for detecting likely LLM-driven phishing.

## What this project does

Instead of only classifying an incoming message, the app:
1. scores the initial message for phishing suspicion,
2. launches a short adversarial reply loop,
3. sends paradoxical / semantic / override-style probes,
4. analyzes the sender's behavior,
5. predicts whether the sender looks more like an **LLM bot** or a **human**.

## Modes

The app supports four sender backends:
- **Mock LLM Bot** — offline simulation, works with no API key
- **Mock Human Sender** — offline simulation, works with no API key
- **OpenAI Model** — requires `OPENAI_API_KEY`
- **Gemini Model** — requires `GEMINI_API_KEY`

## Quick start

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Optional API keys

Create a `.env` file from `.env.example`.

```env
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

## Suggested demo flow

1. Start the app.
2. Paste a suspicious email like:
   - "Hi, this is IT support. Your mailbox will be disabled today unless you confirm your password immediately."
3. Choose **Mock LLM Bot**.
4. Run the conversation.
5. Observe whether the model follows impossible constraints, hallucinates, or reacts to hidden override text.

## Project structure

```text
counter_interrogation_project/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
└── core/
    ├── detector.py
    ├── probes.py
    └── senders.py
```

## Important note for a paper

This is a **prototype**, not a production anti-phishing gateway. Its main value is to demonstrate a publishable research idea:
- active defense,
- behavioral detection,
- low-training-cost experimentation,
- measurable conversation-level signals.

For a stronger publication, add:
- a real phishing dataset,
- a human-subject evaluation or red-team study,
- comparisons against stronger baselines,
- false-positive analysis,
- ablation across probe types.
