import asyncio
import json
from app.models import DiscordAccount, DiscordProxyConfig
from app.discord_heartbeat import DiscordHeartbeat  # Новый импорт
from app.ai_handler import AIHandler
from app.logger_module import logger
import config

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

        # Используем новый класс DiscordHeartbeat вместо DiscordChatMonitor
        heartbeat = DiscordHeartbeat(
            account=account,
            ai_handler=ai_handler
        )
        tasks.append(heartbeat.start_heartbeat())

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())