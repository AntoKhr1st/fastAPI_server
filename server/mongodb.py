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
        result = await self.collection.update_one(
            {"_id": document_id, "notifications.id": notification_id},
            {"$set": {"notifications.$.is_new": False}}
        )

        if result.matched_count > 0:
            print("Уведомление успешно обновлено")
            return True
        else:
            print("Уведомление не найдено или не было обновлено")
            return False
