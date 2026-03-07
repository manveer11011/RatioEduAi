from study_coding_teacher_agent.gguf_backend import (
    TEACHER_SYSTEM_PROMPT,
    TEACHER_SYSTEM_PROMPT_SHORT,
    OFF_TOPIC_REPLY,
    STUDY_CODING_KEYWORDS,
)


def is_likely_study_or_coding(user_message: str) -> bool:
    if not user_message or not user_message.strip():
        return False
    lower = user_message.lower().strip()
    return any(kw in lower for kw in STUDY_CODING_KEYWORDS)


def get_teacher_response(
    client,
    user_message: str,
    *,
    model: str = "Qwen3-4B-Instruct-2507-Q4_K_S.gguf",
    use_short_prompt: bool = False,
    use_guard: bool = False,
) -> str:
    if use_guard and not is_likely_study_or_coding(user_message):
        return OFF_TOPIC_REPLY

    system = TEACHER_SYSTEM_PROMPT_SHORT if use_short_prompt else TEACHER_SYSTEM_PROMPT
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_message},
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
        )
        reply = (response.choices[0].message.content or "").strip()
        return reply or OFF_TOPIC_REPLY
    except Exception as e:
        return f"I couldn't get an answer right now: {e}"


def get_teacher_response_messages(
    client,
    messages: list[dict],
    *,
    model: str = "gpt-oss-20b-MXFP4",
) -> str:
    if not messages or not any(m.get("role") == "system" for m in messages):
        return OFF_TOPIC_REPLY
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
        )
        reply = (response.choices[0].message.content or "").strip()
        return reply or OFF_TOPIC_REPLY
    except Exception as e:
        return f"I couldn't get an answer right now: {e}"
