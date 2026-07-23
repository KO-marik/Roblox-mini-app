import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI(title="RobloxGooseBot Mini App Backend")

# Разрешаем запросы со всех источников (для GitHub Pages и Telegram Mini App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = "8894865754:AAGpuwBq0eMIP2nCBZMignos9ctaqAtAemc"
CHANNEL_ID = "@Gooseroblox67"

# База данных в памяти
db_posts: List[Dict] = []
db_friends: List[Dict] = []

class PostModel(BaseModel):
    user_id: int
    author_name: str
    text: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None


# --- WEBHOOK: АВТО-ПРИЕМ ПОСТОВ ИЗ КАНАЛА 24/7 ---
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        
        # Проверяем публикацию в канале
        if "channel_post" in data:
            post = data["channel_post"]
            chat_username = post.get("chat", {}).get("username", "")

            # Фильтруем только посты из @Gooseroblox67
            if chat_username.lower() == "gooseroblox67":
                text = post.get("text") or post.get("caption") or ""
                
                # Проверяем хештег
                if "#новость" in text.lower() or "#news" in text.lower():
                    media_url = None
                    media_type = None

                    # Если есть фото
                    if "photo" in post:
                        file_id = post["photo"][-1]["file_id"]
                        file_res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
                        if file_res.get("ok"):
                            file_path = file_res["result"]["file_path"]
                            media_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                            media_type = "image"
                    
                    # Если есть видео
                    elif "video" in post:
                        file_id = post["video"]["file_id"]
                        file_res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
                        if file_res.get("ok"):
                            file_path = file_res["result"]["file_path"]
                            media_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                            media_type = "video"

                    # Сохраняем новость в ленту
                    db_posts.append({
                        "user_id": 0,
                        "author_name": "Администрация",
                        "text": text,
                        "media_url": media_url,
                        "media_type": media_type
                    })
    except Exception as e:
        print(f"Ошибка при обработке Webhook: {e}")

    return {"ok": True}


# --- ПРОВЕРКА АДМИНА КАНАЛА ---
@app.get("/api/check-admin/{user_id}")
async def check_admin(user_id: int):
    # Твой личный Telegram ID (всегда админ)
    if user_id == 6122432326:
        return {"is_admin": True}

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
    params = {"chat_id": CHANNEL_ID, "user_id": user_id}
    
    try:
        res = requests.get(url, params=params).json()
        if res.get("ok"):
            status = res["result"]["status"]
            if status in ["creator", "administrator"]:
                return {"is_admin": True}
    except Exception as e:
        print(f"Ошибка проверки админа: {e}")

    return {"is_admin": False}


# --- МАРШРУТЫ ПОСТОВ ---
@app.get("/api/posts")
async def get_all_posts():
    return db_posts

@app.get("/api/posts/{user_id}")
async def get_user_posts(user_id: str):
    return [p for p in db_posts if str(p["user_id"]) == str(user_id)]

@app.post("/api/posts")
async def create_post(post: PostModel):
    post_data = post.dict()
    db_posts.append(post_data)
    return {"status": "ok", "post": post_data}

@app.delete("/api/posts/{post_index}")
async def delete_post(post_index: int):
    if 0 <= post_index < len(db_posts):
        deleted = db_posts.pop(post_index)
        return {"status": "ok", "message": "Удалено", "deleted": deleted}
    raise HTTPException(status_code=404, detail="Пост не найден")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
