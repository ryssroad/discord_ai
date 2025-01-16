import asyncio
import random
import time
from typing import List
import requests

from .models import DiscordAccount, DialogMessage, DialogContext
from .db_manager import DBManager
from .dialog_manager import DialogManager
from .ai_handler import AIHandler
from .logger_module import logger


class DiscordMessageSender:
    BASE_URL = "https://discord.com/api/v9"

    def __init__(self, account: DiscordAccount):
        self.account = account
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
            logger.debug(f"Using proxy: {account.proxy.host}:{account.proxy.port}")
        logger.debug(f"DiscordMessageSender initialized for user_id={account.user_id}. Proxies={self.proxies}")


    def get_channel_messages(self, limit: int = 50) -> List[dict]:
        logger.debug(f"get_channel_messages: requesting last {limit} messages.")
        url = f"{self.BASE_URL}/channels/{self.account.channel_id}/messages"
        params = {"limit": limit}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10, proxies=self.proxies)
            resp.raise_for_status()
            data = resp.json()
            logger.debug(f"Received {len(data)} messages from Discord.")
            return data
        except Exception as e:
            logger.error(f"[{self.account.user_id}] Error while getting the messages: {e}")
            return []


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
                logger.debug(f"Typing emulated in channel_id={channel_id}, status_code={resp.status_code}")
                
                remaining = duration - (time.time() - start_time)
                await asyncio.sleep(min(8.0, remaining))
                
            except Exception as e:
                logger.error(f"[{self.account.user_id}] Ошибка при эмуляции печатания: {e}")
                break


    async def send_message(self, content: str, reply_to: dict = None):
        logger.debug(f"send_message: content={content[:50]}, reply_to={reply_to}")
            
        msg_len = len(content)
        typing_time = random.uniform(1 + msg_len / 12, 2 + msg_len / 8)
        typing_time = min(typing_time, 10.0)

        await self.send_typing(self.account.channel_id, typing_time)

        msg_len = len(content)
        typing_time = random.uniform(1 + msg_len / 12, 2 + msg_len / 8)
        typing_time = min(typing_time, 10.0)

        logger.debug(f"Simulating typing for ~{typing_time:.1f} seconds (message length={msg_len}).")
        await asyncio.sleep(typing_time)

        url = f"{self.BASE_URL}/channels/{self.account.channel_id}/messages"
        json_data = {
            "content": content,
            "tts": False,
            "flags": 0,
        }
        if reply_to:
            json_data["message_reference"] = reply_to

        try:
            resp = requests.post(url, headers=self.headers, json=json_data, timeout=10, proxies=self.proxies)
            resp.raise_for_status()
            logger.debug(f"send_message successful: status_code={resp.status_code}")
            return resp
        except Exception as e:
            logger.error(f"[{self.account.user_id}] Error while sending the message: {e}")
            return None


class DiscordChatMonitor:
    def __init__(self, 
                 account: DiscordAccount, 
                 db_manager: DBManager, 
                 ai_handler: AIHandler,
                 poll_interval_range=(60, 240)
    ):
        self.account = account
        self.db = db_manager
        self.ai_handler = ai_handler
        self.sender = DiscordMessageSender(account)
        self.dialog_manager = DialogManager(self.db)
        self.poll_interval_range = poll_interval_range

        self.processed_messages = set()
        logger.debug(f"DiscordChatMonitor initialized for user_id={account.user_id}")


    async def start_monitoring(self):
        logger.info(f"[{self.account.user_id}] Start monitoring loop.")
        while True:
            try:
                delay = random.uniform(*self.poll_interval_range)
                logger.debug(f"Global sleep for {delay:.1f} seconds.")
                await asyncio.sleep(delay)

                raw_msgs = self.sender.get_channel_messages(limit=50)
                if not raw_msgs:
                    logger.debug("No messages received from Discord.")
                    continue

                new_msgs = [m for m in raw_msgs if m['id'] not in self.processed_messages]
                logger.debug(f"Filtered {len(new_msgs)} new messages out of {len(raw_msgs)} total.")

                classified = self.dialog_manager.classify_messages(new_msgs, self.account.user_id)

                to_respond = self.dialog_manager.select_messages_to_respond(classified)
                logger.debug(f"Messages selected to respond: {to_respond}")

                if not to_respond:
                    pass

                for dialog_msg in to_respond:
                    self.db.save_message(self.account.user_id, dialog_msg, is_bot=False)

                    personal_ctx = self.db.get_user_dialog_context(
                        account_id=self.account.user_id,
                        user_id=dialog_msg.author_id,
                        limit=10
                    )
                    if personal_ctx is None:
                        logger.error("personal_ctx is None! Creating empty DialogContext.")
                        personal_ctx = DialogContext(user_id=dialog_msg.author_id, messages=[])

                    personal_texts = [m.content for m in personal_ctx.messages]
                    channel_context = [msg['content'] for msg in raw_msgs[-20:]]

                    reply_text = await self.ai_handler.generate_response(
                        personal_history=personal_texts,
                        channel_context=channel_context,
                        current_message=dialog_msg.content,
                        is_reply=True
                    )

                    reply_payload = {
                        "message_id": dialog_msg.id,
                        "channel_id": self.account.channel_id
                    }
                    await self.sender.send_message(reply_text, reply_to=reply_payload)

                    bot_msg_id = f"bot_{time.time()}"
                    self.db.save_message(
                        self.account.user_id, 
                        DialogMessage(
                            id=bot_msg_id,
                            content=reply_text,
                            author_id=self.account.user_id,
                            timestamp=str(time.time()),
                            referenced_message_id=dialog_msg.id
                        ),
                        is_bot=True
                    )

                    self.db.save_log(
                        self.account.user_id, 
                        f"[SEND] Replied to user {dialog_msg.author_id}, msgId={dialog_msg.id}\nContent={reply_text}"
                    )

                    self.processed_messages.add(dialog_msg.id)

                    inter_delay = random.uniform(60, 120)
                    logger.debug(f"Inter-response sleep for {inter_delay:.1f} seconds.")
                    await asyncio.sleep(inter_delay)

                if not to_respond:
                    if random.random() < 0.05:
                        logger.debug("Randomly decided to post a 'no-reply' message (priority 4).")
                        channel_context = [msg['content'] for msg in raw_msgs[-20:]]
                        reply_text = await self.ai_handler.generate_response(
                            personal_history=[],  
                            channel_context=channel_context,
                            current_message="",
                            is_reply=False
                        )
                        await self.sender.send_message(reply_text, reply_to=None)

                        bot_msg_id = f"bot_{time.time()}"
                        self.db.save_message(
                            self.account.user_id,
                            DialogMessage(
                                id=bot_msg_id,
                                content=reply_text,
                                author_id=self.account.user_id,
                                timestamp=str(time.time()),
                                referenced_message_id=None
                            ),
                            is_bot=True
                        )
                        self.db.save_log(
                            self.account.user_id,
                            f"[SEND] Random chat message.\nContent={reply_text}"
                        )

            except Exception as e:
                logger.error(f"[{self.account.user_id}] Ошибка при мониторинге чата: {e}")
                await asyncio.sleep(30)
