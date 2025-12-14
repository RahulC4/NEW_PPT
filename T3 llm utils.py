from openai import AzureOpenAI
from utils import get_env, logger

# ============================================================
# AZURE OPENAI CLIENT (CHAT ONLY)
# ============================================================
client = AzureOpenAI(
    azure_endpoint=get_env("OPENAI_API_BASE", required=True),
    api_key=get_env("OPENAI_API_KEY", required=True),
    api_version=get_env("OPENAI_API_VERSION", required=True),
)

CHAT_MODEL = get_env("CHAT_MODEL", "gpt-5-mini")


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
):
    """
    Standard chat completion wrapper used across the app.
    """

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.exception("LLM chat completion failed")
        raise e
