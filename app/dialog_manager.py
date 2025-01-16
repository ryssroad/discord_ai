import random
import time
from typing import List, Dict, Any
from .models import DialogMessage
from .db_manager import DBManager
from .logger_module import logger


class DialogManager:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager


    def classify_messages(self, 
                         messages: List[Dict[str, Any]], 
                         bot_user_id: str
    ) -> Dict[int, List[DialogMessage]]:
        logger.debug("DialogManager.classify_messages: Start classification.")
        result = {
            1: [],  
            2: [],  
            3: [],  
            4: []   
        }

        for msg_data in messages:
            msg_id = msg_data['id']
            author_id = msg_data['author']['id']
            ref = msg_data.get('referenced_message')

            if author_id == bot_user_id:
                continue

            dialog_msg = DialogMessage(
                id=msg_id,
                content=msg_data.get('content', ''),
                author_id=author_id,
                timestamp=msg_data.get('timestamp', str(time.time())),
                referenced_message_id=ref['id'] if ref else None
            )

            if ref:
                if ref['author']['id'] == bot_user_id:
                    result[1].append(dialog_msg)
                else:
                    result[3].append(dialog_msg)
            else:
                result[2].append(dialog_msg)

        logger.debug(f"DialogManager.classify_messages: result={result}")
        return result


    def select_messages_to_respond(self, classified_msgs: Dict[int, List[DialogMessage]]) -> List[DialogMessage]:
        logger.debug("DialogManager.select_messages_to_respond: Start selection.")
        p1 = classified_msgs[1]
        if p1:
            k = int(len(p1) * 0.7) or 1
            random.shuffle(p1)
            chosen = p1[:k]
            logger.debug(f"Selected priority 1, chosen={chosen}")
            return chosen

        p2 = classified_msgs[2]
        if p2:
            chosen = [random.choice(p2)]
            logger.debug(f"Selected priority 2, chosen={chosen}")
            return chosen

        p3 = classified_msgs[3]
        if p3:
            chosen = [random.choice(p3)]
            logger.debug(f"Selected priority 3, chosen={chosen}")
            return chosen

        logger.debug("No messages found for p1-p3, might do priority 4 (random).")
        return []
