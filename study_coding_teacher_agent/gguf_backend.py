# Neutral system prompt (no topic restriction)
TEACHER_SYSTEM_PROMPT = "You are a helpful assistant."
TEACHER_SYSTEM_PROMPT_SHORT = TEACHER_SYSTEM_PROMPT
OFF_TOPIC_REPLY = "No response."
STUDY_CODING_KEYWORDS = []  # unused when guard disabled


def is_likely_study_or_coding(user_message: str) -> bool:
    return True  # guard disabled by default; no filtering


DEFAULT_MAX_TOKENS = 8192


def get_teacher_response_gguf(
    llm,
    user_message: str,
    *,
    use_short_prompt: bool = False,
    use_guard: bool = False,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.5,
) -> str:
    if use_guard and not is_likely_study_or_coding(user_message):
        return OFF_TOPIC_REPLY

    system = TEACHER_SYSTEM_PROMPT_SHORT if use_short_prompt else TEACHER_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]

    try:
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choices = response.get("choices") or []
        if not choices:
            return OFF_TOPIC_REPLY
        msg = choices[0].get("message") or choices[0].get("delta") or {}
        reply = (msg.get("content") or "").strip()
        return reply or OFF_TOPIC_REPLY
    except Exception as e:
        return f"I couldn't get an answer right now: {e}"


def get_teacher_response_gguf_messages(
    llm,
    messages: list[dict],
    *,
    use_short_prompt: bool = False,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.5,
) -> str:
    if not messages or not any(m.get("role") == "system" for m in messages):
        return OFF_TOPIC_REPLY
    try:
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choices = response.get("choices") or []
        if not choices:
            return OFF_TOPIC_REPLY
        msg = choices[0].get("message") or choices[0].get("delta") or {}
        reply = (msg.get("content") or "").strip()
        return reply or OFF_TOPIC_REPLY
    except Exception as e:
        return f"I couldn't get an answer right now: {e}"
