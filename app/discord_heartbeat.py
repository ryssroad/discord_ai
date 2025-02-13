import asyncio
import random
import time
from typing import List
import requests
from app.models import DiscordAccount
from app.ai_handler import AIHandler
from app.logger_module import logger

class DiscordHeartbeat:
    BASE_URL = "https://discord.com/api/v9"

    def __init__(self, 
                 account: DiscordAccount,
                 ai_handler: AIHandler,
                 heartbeat_interval=(300, 600)  # 5-10 минут между сообщениями
    ):
        self.account = account
        self.ai_handler = ai_handler
        self.heartbeat_interval = heartbeat_interval
        self.headers = {
            **account.headers,
            "authorization": account.token
        }
        self.proxies = None
        if account.proxy:
            self.proxies = {
                "http": account.proxy.url,
                "https": account.proxy.url
            }

    async def send_typing(self, channel_id: str, duration: float):
        typing_url = f"{self.BASE_URL}/channels/{channel_id}/typing"
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                resp = requests.post(
                    typing_url, 
                    headers=self.headers, 
                    data='',
                    timeout=10, 
                    proxies=self.proxies
                )
                resp.raise_for_status()
                
                remaining = duration - (time.time() - start_time)
                await asyncio.sleep(min(8.0, remaining))
                
            except Exception as e:
                logger.error(f"[{self.account.user_id}] Ошибка при эмуляции печатания: {e}")
                break

    async def send_message(self, content: str):
        # Эмулируем набор текста
        msg_len = len(content)
        typing_time = random.uniform(1 + msg_len / 12, 2 + msg_len / 8)
        typing_time = min(typing_time, 10.0)
        
        await self.send_typing(self.account.channel_id, typing_time)

        url = f"{self.BASE_URL}/channels/{self.account.channel_id}/messages"
        json_data = {
            "content": content,
            "tts": False,
            "flags": 0,
        }

        try:
            resp = requests.post(url, headers=self.headers, json=json_data, timeout=10, proxies=self.proxies)
            resp.raise_for_status()
            logger.debug(f"Message sent successfully: status_code={resp.status_code}")
            return resp
        except Exception as e:
            logger.error(f"[{self.account.user_id}] Error while sending message: {e}")
            return None

    def get_channel_messages(self, limit: int = 20) -> List[dict]:
        """Получаем последние сообщения из канала для контекста"""
        url = f"{self.BASE_URL}/channels/{self.account.channel_id}/messages"
        params = {"limit": limit}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10, proxies=self.proxies)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[{self.account.user_id}] Error getting channel messages: {e}")
            return []

    async def generate_message_with_context(self) -> str:
        """Генерируем сообщение с учетом контекста канала"""
        # Получаем последние сообщения
        channel_messages = self.get_channel_messages(limit=20)
        
        # Извлекаем только текст сообщений для контекста
        channel_context = [msg['content'] for msg in channel_messages]
        
        # Генерируем сообщение через AI с учетом контекста
        message = await self.ai_handler.generate_response(
            personal_history=[],
            channel_context=channel_context,
            current_message="",
            is_reply=False
        )
        
        return message

    async def start_heartbeat(self):
        logger.info(f"[{self.account.user_id}] Starting heartbeat messages")
        while True:
            try:
                # Используем новый метод генерации с контекстом
                message = await self.generate_message_with_context()
                
                # Отправляем сообщение
                await self.send_message(message)
                
                delay = random.uniform(*self.heartbeat_interval)
                logger.debug(f"Waiting {delay:.1f} seconds before next heartbeat message")
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"[{self.account.user_id}] Error in heartbeat loop: {e}")
                await asyncio.sleep(30)

# Пример использования:
async def main():
    with open("accounts.json", "r") as f:
        data = json.load(f)
    accounts_data = data.get("accounts", [])

    if not accounts_data:
        logger.error("Accounts not found | accounts.json")
        return

    tasks = []
    for acc in accounts_data:
        proxy_config = None
        if "proxy" in acc and acc["proxy"]:
            proxy_config = DiscordProxyConfig(
                host=acc["proxy"]["host"],
                port=acc["proxy"]["port"],
                username=acc["proxy"]["username"],
                password=acc["proxy"]["password"],
                protocol=acc["proxy"]["protocol"]
            )

        account = DiscordAccount(
            token=acc["token"],
            user_id=acc["user_id"],
            channel_id=acc["channel_id"],
            headers=acc["headers"],
            proxy=proxy_config
        )
        
        ai_handler = AIHandler(
            api_key=config.openai_api_key,
            model=config.openai_model,
            proxy=config.proxy_for_openai_api if config.proxy_for_openai_api != "None" else None
        )

        heartbeat = DiscordHeartbeat(
            account=account,
            ai_handler=ai_handler,
            heartbeat_interval=(300, 600)  # Настройте интервал по вашему усмотрению
        )
        tasks.append(heartbeat.start_heartbeat())

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())