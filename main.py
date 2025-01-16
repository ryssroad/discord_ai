import asyncio
import json
from app.models import DiscordAccount, DiscordProxyConfig
from app.db_manager import DBManager
from app.ai_handler import AIHandler
from app.discord_client import DiscordChatMonitor
from app.logger_module import logger
import config


async def main():
    with open("accounts.json", "r") as f:
        data = json.load(f)
    accounts_data = data.get("accounts", [])

    if not accounts_data:
        logger.error("Accounts not found | accounts.json")
        return

    db_manager = DBManager(db_path="conversations.db")

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
        
        if config.proxy_for_openai_api != "None" and "http" in config.proxy_for_openai_api:
            ai_handler = AIHandler(
                api_key=config.openai_api_key,
                model=config.openai_model,
                proxy=config.proxy_for_openai_api
            )
        else:
            ai_handler = AIHandler(
                api_key=config.openai_api_key,
                model=config.openai_model
            )

        monitor = DiscordChatMonitor(
            account=account,
            db_manager=db_manager,
            ai_handler=ai_handler,
            poll_interval_range=(config.interval_time_from, config.interval_time_to)
        )
        tasks.append(monitor.start_monitoring())

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
