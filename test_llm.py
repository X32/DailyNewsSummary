from summarize import get_llm_client
import os

client = get_llm_client()
resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL"),
    messages=[{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    stream=False
)
print("模型:", resp.model)
print("回复:", resp.choices[0].message.content)
