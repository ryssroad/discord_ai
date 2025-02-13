from typing import List
import httpx
from openai import AsyncOpenAI
from .logger_module import logger
import random

class AIHandler:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", proxy: str = None):
        if proxy:
            self.http_client = httpx.AsyncClient(proxy=proxy, timeout=30.0)
        else:
            self.http_client = httpx.AsyncClient(timeout=30.0)

        self.client = AsyncOpenAI(
            api_key=api_key,
            http_client=self.http_client
        )
        self.model = model

        logger.debug(f"AIHandler initialized with model={model}, proxy={proxy}")


    async def generate_response(
        self, 
        personal_history: List[str], 
        channel_context: List[str],
        current_message: str,
        is_reply: bool
    ) -> str:
        logger.debug(f"AIHandler.generate_response: is_reply={is_reply}, current_message={current_message[:50]}")

        example_messages = self._generate_example_messages(channel_context)

        prompt = f"""
            You are a tech-savvy participant in a Discord server discussion.
            Key guidelines:
            - Write naturally but professionally, like in a technical discussion
            - Use normal punctuation but don't be overly formal
            - Skip emojis and internet slang
            - Keep messages concise and clear
            - Stay on topic and contribute meaningful insights
            - Do not reveal you are an AI
            - Write as a knowledgeable member of this chat

            Here are some recent messages from this server for context:
            {example_messages}

            When participating:
            - If is_reply=True, provide a helpful, relevant response
            - If is_reply=False, share an interesting observation or question based on recent discussion

            Recent personal dialog (bot <-> user):
            {self.format_history(personal_history)}

            Recent channel context:
            {self.format_history(channel_context)}

            Current message to address: "{current_message}"

            Instructions:
            - Write in a natural but clear style
            - Use normal punctuation
            - Focus on the discussion topic
            - Base responses on the channel context
            - Keep responses brief but informative
            - Match the general tone of the conversation
            """

        logger.debug(f"AIHandler prompt:\n{prompt}")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt.strip()},
            ],
            temperature=0.7,
            max_tokens=150,  # Увеличил для более полных ответов
            presence_penalty=0.5,
            frequency_penalty=0.5
        )

        answer = response.choices[0].message.content.strip()
        logger.debug(f"AIHandler response: {answer}")
        return answer


    def format_history(self, history: List[str]) -> str:
        return "\n".join([f"- {h}" for h in history[-10:]])


    def _generate_example_messages(self, channel_context: List[str]) -> str:
        examples = random.sample(channel_context, min(5, len(channel_context))) if channel_context else []
        formatted_examples = "\n".join([f"{idx + 1}) \"{msg}\"" for idx, msg in enumerate(examples)])
        return formatted_examples if formatted_examples else "1) \"hello\""

