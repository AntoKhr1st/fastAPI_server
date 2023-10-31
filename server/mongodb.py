import uuid
from datetime import time

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from bson import ObjectId


class NotificationKeyEnum(str, Enum):
    registration = "registration"
    new_message = "new_message"
    new_post = "new_post"
    new_login = "new_login"


class Notification(BaseModel):
    id: Optional[str] = None
    timestamp: int
    is_new: bool = False
    key: NotificationKeyEnum
    target_id: Optional[str] = None
    data: Optional[dict] = None


class User(BaseModel):
    user_id: str
    notifications: List[Notification] = []


class Request(BaseModel):
    user_id: str
    key: NotificationKeyEnum
    target_id: Optional[str] = None
    data: Optional[dict] = None


class MongoDBManager:
    def __init__(self, connection_string: str, db_name: str, collection_name: str):
        self.client = AsyncIOMotorClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    async def add_notification(self, user_id: str, notification: Notification):
        document_id = ObjectId(user_id)
        user = await self.collection.find_one({"_id": document_id})
        if user is None:
            user = {"_id": document_id, "notifications": []}
            await self.collection.insert_one(user)
        new_not = notification.model_dump()
        update = {
            "$push": {
                "notifications": new_not
            }
        }
        await self.collection.update_one(
            {"_id": document_id},
            update
        )

    async def update_notification(self, user_id: str, notification_id: str, updated_data: dict):
        await self.collection.update_one(
            {"id": user_id, "notifications.id": notification_id},
            {"$set": {"notifications.$.data": updated_data}}
        )

    def close_connection(self):
        self.client.close()

    async def get_notifications(self, user_id, skip=0, limit=10):
        document_id = ObjectId(user_id)
        user = await self.collection.find_one({"_id": document_id})

        if not user:
            return None

        notifications = user.get("notifications", [])
        total_notifications = len(notifications)
        new_notifications = sum(1 for notification in notifications if notification.get("is_new", False))

        filtered_notifications = notifications[skip: skip + limit]

        return {
            "elements": total_notifications,
            "new": new_notifications,
            "request": {
                "user_id": user_id,
                "skip": skip,
                "limit": limit,
            },
            "list": filtered_notifications,
        }

    async def mark_notification_as_read(self, user_id: str, notification_id: str):
        document_id = ObjectId(user_id)
        filter_ = {"_id": document_id, "id": notification_id}
        update = {"$set": {"is_new": False}}
        result = await self.collection.update_one(filter_, update)

        return True

        # if result.modified_count == 1:
        #     return True
        # else:
        #     return False


# Пример использования:
if __name__ == "__main__":
    import asyncio


    async def main():
        manager = MongoDBManager("mongodb://localhost:27017", "users", "users")

        user_id = "user123"
        new_notification = Notification(key=NotificationKeyEnum.new_message, data={"message": "Hello!1"})

        # await manager.add_notification(user_id, new_notification)

        updated_data = {"message": "Updated message!"}
        notification_id = new_notification.id
        print(new_notification)
        await manager.update_notification(user_id, notification_id, updated_data)

        manager.close_connection()


    asyncio.run(main())
