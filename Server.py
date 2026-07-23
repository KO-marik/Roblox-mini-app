from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="RobloxGooseBot Mini App Backend")

# Разрешаем запросы из фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Временная база данных в памяти (можно легко заменить на Firebase)
db_posts: List[Dict] = []
db_friends: List[Dict] = []

class PostModel(BaseModel):
    user_id: int
    author_name: str
    text: str

class FriendRequestModel(BaseModel):
    from_user_id: int
    to_user_id: str

# 1. Создать пост в профиле
@app.post("/api/posts")
async def create_post(post: PostModel):
    post_data = post.dict()
    db_posts.append(post_data)
    return {"status": "ok", "post": post_data}

# 2. Получить посты конкретного пользователя
@app.get("/api/posts/{user_id}")
async def get_user_posts(user_id: str):
    # Фильтруем посты, привязав к конкретному профилю
    user_posts = [p for p in db_posts if str(p["user_id"]) == str(user_id)]
    return user_posts

# 3. Отправить заявку в друзья
@app.post("/api/friends/request")
async def send_friend_request(req: FriendRequestModel):
    db_friends.append(req.dict())
    return {"status": "ok", "message": "Заявка отправлена"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
  
