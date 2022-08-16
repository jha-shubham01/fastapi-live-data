from typing import List

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from database import get_db
from models import ListPydanticPost, Post, PydanticPost

app = FastAPI()


html = """
<!DOCTYPE html>
<html>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <!-- CSS only -->
    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/css/bootstrap.min.css"
        rel="stylesheet"
        integrity="sha384-gH2yIJqKdNHPEq0n4Mqa/HGKIhSkIHeL5AyhkYV8i59U5AR6csBvApHHNl/vI1Bx"
        crossorigin="anonymous"
    />
    <head>
        <title>Code with SJ</title>
    </head>
    <body>
    <div id="app" class="row mt-5">
        <div class="col-1"></div>
        <div class="col-10">
            <div class="card">
            <p class="card-header">Display list of all the posts in Real-Time</p>
            <div class="card-body">
                <table class="table align-middle mb-0 bg-white">
                <thead class="bg-light">
                    <tr>
                    <th>Title</th>
                    <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="post in posts">
                    <td>
                        <p class="fw-normal mb-1">[[ post.title ]]</p>
                    </td>
                    <td>
                        <span
                        class="badge rounded-pill d-inline"
                        :class="{'bg-success': post.status !== 'Draft', 'bg-warning': post.status === 'Draft'}"
                        >
                        [[ post.status ]]
                        </span>
                    </td>
                    </tr>
                </tbody>
                </table>
            </div>
            </div>
        </div>
        </div>

        <script
        src="https://code.jquery.com/jquery-3.6.0.min.js"
        integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4="
        crossorigin="anonymous"
        ></script>
        <!-- JavaScript Bundle with Popper -->
        <script
        src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.0/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-A3rJD856KowSb7dwlZdYEkO39Gagi7vIsF0jrRAoQmDKKtQBHUuLZ9AsSv4jD4Xa"
        crossorigin="anonymous"
        ></script>
        <script src="https://cdn.jsdelivr.net/npm/vue@2.6.14"></script>
        <script>
            vueApp = new Vue({
                el: "#app",
                delimiters: ["[[", "]]"],
                data() {
                return {
                    posts: [],
                };
                },
            });

            var client_id = Date.now();
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function (e) {
                allData = JSON.parse(e.data);
                allData = JSON.parse(allData);
                vueApp.$data.posts.push(allData);
            };
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.get("/test")
async def get():
    await manager.broadcast(f"SJ said hi")
    return {"message": "Success"}


@app.get("/posts")
async def list_item(db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return ListPydanticPost(posts=posts).json()


@app.post("/posts/insert", response_model=PydanticPost)
async def create_item(data: PydanticPost, db: Session = Depends(get_db)):
    db_item = Post(**data.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    await manager.broadcast(data.json())
    return data


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_id: int, db: Session = Depends(get_db)
):
    await manager.connect(websocket)
    try:
        while True:
            posts = db.query(Post).all()
            posts = ListPydanticPost(posts=posts)
            await manager.broadcast(posts.json())
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
