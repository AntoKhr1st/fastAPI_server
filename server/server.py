import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from mail_sender import send_email
from mongodb import Notification, MongoDBManager, Request

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
# load_dotenv()


# Подключение к контейнеру MongoDB

# DB_URI = os.environ.get("DB_URI")
# mongo_client = AsyncIOMotorClient(DB_URI)
# mongo_client = AsyncIOMotorClient("mongodb://mongodb_container:27017")
# db = mongo_client.get_database('users')
# users_collection = db.get_collection("notifications")
manager = MongoDBManager("mongodb://localhost:27017", "users", "users")


@app.post("/create", response_model=dict)
async def create_notification(request: Request):
    notification = Notification(
        id=str(uuid.uuid4()),
        timestamp=int(time.time()),
        is_new=True,
        key=request.key,
        target_id=request.target_id,
        data=request.data
    )
    await manager.add_notification(request.user_id, notification)

    # отправляем сообщение на почту пользователя использует переменную окружения EMAIL

    # send_email(notification["key"], os.environ.get("EMAIL"))

    return JSONResponse(content={"success": True}, status_code=201)


# Обработчик листинга уведомлений
@app.get("/list", )
async def list_notifications(
        user_id: str = Query(..., description="Идентификатор пользователя"),
        skip: int = Query(0, description="Кол-во уведомлений, которые следует пропустить"),
        limit: int = Query(10, description="Кол-во уведомлений, которые следует вернуть"),
):
    notifications = await manager.get_notifications(user_id, skip, limit)
    if notifications is not None:
        return {
            "success": True,
            "data": notifications
        }
    else:
        return {
            "success": False,
            "error": "User not found",
        }


# Обработчик отметки уведомления как прочтенного
@app.post("/read")
async def mark_notification(
        user_id: str = Query(..., title="User ID", description="Идентификатор пользователя"),
        notification_id: str = Query(..., title="Notification ID", description="Идентификатор уведомления"),
):
    result = await manager.mark_notification_as_read(user_id, notification_id)
    if result:
        return JSONResponse(content={"success": True}, status_code=200)
    else:
        return JSONResponse(content={"success": False}, status_code=500)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
