from openai import AzureOpenAI
from utils import get_env, logger, safe_json_load

# Azure OpenAI client
chat_client = AzureOpenAI(
    azure_endpoint=get_env("OPENAI_API_BASE", required=True),
    api_key=get_env("OPENAI_API_KEY", required=True),
    api_version=get_env("OPENAI_API_VERSION", required=True),
)

CHAT_MODEL = get_env("CHAT_MODEL", required=True)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    GPT-5 SAFE call.
    NO temperature, NO sampling params.
    """

    try:
        response = chat_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        # ✅ SDK v1.x safe access
        return response.choices[0].message.content

    except Exception as e:
        logger.exception(f"LLM call failed: {e}")
        return ""
