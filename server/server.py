import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from enum import Enum

from mail_sender import send_email


class NotificationKeyEnum(str, Enum):
    registration = "registration"
    new_message = "new_message"
    new_post = "new_post"
    new_login = "new_login"


class Notification(BaseModel):
    id: Optional[str] = None
    user_id: str
    target_id: Optional[str] = None
    key: NotificationKeyEnum
    data: Optional[dict] = None


description = """
Notifications database API helps you to deal with users notifications.

"""
app = FastAPI(title="Notifications database",
              description=description,
              summary="This app can find create, filter and modify notifications",
              contact={
                  "name": "Anton Khr",
                  "email": "antokhrist@gmail.com",
              }, )
load_dotenv()
# Подключение к контейнеру MongoDB

# DB_URI = os.environ.get("DB_URI")
# mongo_client = AsyncIOMotorClient(DB_URI)
mongo_client = AsyncIOMotorClient("mongodb://mongodb_container:27017")
db = mongo_client.get_database('users')
users_collection = db.get_collection("notifications")


@app.post("/create")
async def create_notification(notification: Notification):
    # Задаем timestamp
    timestamp = int(datetime.now().timestamp())
    # генерирую уникальный id для уведомления
    unique_value = str(uuid4())

    # Создаем запись для вставки в MongoDB
    new_notification = {
        "id": unique_value,
        "timestamp": timestamp,
        "is_new": True,
        "user_id": notification.user_id,
        "key": notification.key,
        "target_id": notification.target_id,
        "data": notification.data
    }
    users_collection.insert_one(new_notification)

    #  отправляем сообщение на почту пользователя использует переменную окружения EMAIL

    send_email(new_notification["key"], os.environ.get("EMAIL"))

    return JSONResponse(content={"success": True}, status_code=201)


# Обработчик листинга уведомлений
@app.get("/list", )
async def list_notifications(
        user_id: str = Query(..., description="Идентификатор пользователя"),
        skip: int = Query(0, description="Кол-во уведомлений, которые следует пропустить"),
        limit: int = Query(10, description="Кол-во уведомлений, которые следует вернуть"),
):
    user = await users_collection.find_one({"user_id": user_id})

    if not user:
        return {
            "success": False,
            "error": "User not found",
        }
    else:
        count_all_notifications = await users_collection.count_documents({"user_id": user_id})
        count_new_notifications = await users_collection.count_documents({"user_id": user_id, "is_new": True})
        # листинг уведомлений пользователя
        filter = {"user_id": user_id}
        sort_order = [("timestamp", -1)]  # Упорядочиваем по времени в убывающем порядке

        documents = users_collection.find(filter).sort(sort_order).skip(skip).limit(limit)

        documents_list = await documents.to_list(length=limit)
        doc_list = []
        for doc in documents_list:
            doc_list.append({'id': doc['id'],
                             'timestamp': doc['timestamp'],
                             'is_new': doc['is_new'],
                             'user_id': doc['user_id'],
                             'key': doc['key'],
                             'target_id': doc['target_id'],
                             'data': doc['data']})

    return {
        "success": True,
        "data": {
            "elements": count_all_notifications,
            "new": count_new_notifications,
            "request": {
                "user_id": user_id,
                "skip": skip,
                "limit": limit,
            },
            "list": doc_list,
        },
    }


# Обработчик отметки уведомления как прочтенного
@app.post("/read")
async def mark_notification_as_read(
        user_id: str = Query(..., title="User ID", description="Идентификатор пользователя"),
        notification_id: str = Query(..., title="Notification ID", description="Идентификатор уведомления"),
):
    # Проверка наличия пользователя в базе данных
    user = users_collection.find_one({"user_id": user_id})
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Поиск и обновление уведомления
    result = users_collection.update_one(
        {"user_id": user_id, "id": notification_id},
        {"$set": {"is_new": False}}
    )
    # проверка корректной работы обновления поля is_new
    document = await users_collection.find_one({"user_id": user_id, "id": notification_id})
    if document and document["is_new"] == False:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="не обновлено")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
