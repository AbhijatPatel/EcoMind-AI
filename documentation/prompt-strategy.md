# Prompt Strategy — EcoMind AI

## 1. System prompt

The full system prompt lives in `backend/app/ai/prompts.py` as `SYSTEM_PROMPT`
so it stays version-controlled and testable alongside the code that uses it,
rather than duplicated in a doc that can drift out of sync. Its structure:

1. **Persona** — "You are EcoMind AI, an environmental sustainability expert..."
2. **Responsibilities** — understand lifestyle context, give specific and
   actionable suggestions, frame estimates as estimates, explain reasoning
   briefly, encourage without shaming.
3. **Safety instructions** — no medical/legal/financial advice, no fabricated
   statistics, no guaranteed-outcome claims, no moralizing, redirect
   off-topic requests back to sustainability.

## 2. User prompt template

There is no separate "user prompt template" string — the user's raw message
is sent as-is as the final message in the conversation. Structure is instead
enforced by `build_messages()` in `prompts.py`, which assembles:

```
[few-shot example 1 (user)]
[few-shot example 1 (assistant)]
[few-shot example 2 (user)]
[few-shot example 2 (assistant)]
[...real conversation history, if any...]
[new user message]
```

This keeps tone-setting (the few-shot examples) separate from the dynamic
conversation, so history can grow without needing to re-inject instructions.

## 3. Few-shot examples

Two examples are currently included, chosen to demonstrate the two most
common question shapes:

- A **quantifiable habit** ("I use my car 20km daily") -> response gives a
  concrete, hedged suggestion with an estimated (not guaranteed) improvement.
- A **values-laden question** ("is that really that bad?") -> response avoids
  judgment, gives a realistic incremental step, and explicitly reassures
  rather than criticizes.

Both examples model the same shape: acknowledge -> quantify or contextualize
-> suggest one realistic next step -> invite follow-up.

## 4. Safety instructions

Encoded directly in the system prompt (see above). The two instructions
worth calling out specifically:

- **No fabricated statistics.** The model is told to describe direction and
  rough scale rather than invent a precise number it isn't confident in.
  This matters because carbon/sustainability figures are exactly the kind of
  plausible-sounding number an LLM can generate confidently and incorrectly.
- **No guaranteed-outcome claims.** Real households vary too much for "this
  will save you $X" to be honest; the prompt requires estimate framing.

## 5. Testing notes

Because the LLM call itself is non-deterministic and requires a live API
key, the test suite (`tests/test_chat.py`) does not call Anthropic's API at
all. Instead, `stream_chat_response` is monkeypatched with fake async
generators representing:

- a normal successful stream,
- a stream that fails partway through.

This tests our own routing, error-handling, and persistence logic in
isolation from the AI provider's actual behavior — which is the right
boundary, since prompt *quality* (does the tone match the few-shot examples
in practice) is a separate, ongoing evaluation concern, not a unit test.

## 6. Open iteration items (not yet resolved)

- **Conversation windowing.** `build_messages()` currently appends all
  passed-in history with no truncation. This was flagged during the Phase 1
  performance review as a cost/latency risk for long conversations and
  still needs a windowing or summarization strategy before chat history
  persistence (already wired via `ChatLog`) is surfaced back into future
  requests.
- **Prompt regression testing.** There's no automated check yet that the
  model's actual tone matches the few-shot examples over time (i.e. a
  golden-response eval). Worth adding once there's a real API key to test
  against.
