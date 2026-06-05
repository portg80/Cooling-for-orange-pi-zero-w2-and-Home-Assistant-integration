from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
import os, json, asyncio

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.join(BASE_DIR, "templates")

# --- Статика ---
if not os.path.isdir(WEB_DIR):
    print(f"[ERROR] Папка templates не найдена: {WEB_DIR}")
else:
    print(f"[INIT] Статика сервируется из: {WEB_DIR}")
    app.mount("/static", StaticFiles(directory=WEB_DIR, html=True), name="templates")

# --- Хранилище подключенных клиентов ---
clients = set()
global_assistant = None


def run_ws_server(assistant_instance):
    """Запускает FastAPI сервер с WS"""
    global global_assistant
    global_assistant = assistant_instance
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Обрабатывает подключения фронтенда"""
    await ws.accept()
    clients.add(ws)
    print(f"[WS] Подключился клиент. Всего: {len(clients)}")

    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("action") == "toggle_mic":
                if global_assistant:
                    global_assistant.wakeword_engine.toggle_pause()

            elif msg.get("action") == "start_command":
                if global_assistant:
                    global_assistant.handle_command()

    except Exception as e:
        print("[WS] Ошибка / отключение:", e)
    finally:
        clients.discard(ws)
        print(f"[WS] Клиент отключен. Осталось: {len(clients)}")


async def push_state(state: dict):
    if not clients:
        return

    msg = json.dumps(state)
    dead_clients = set()

    for ws in clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead_clients.add(ws)

    for dead in dead_clients:
        clients.discard(dead)


# Ссылка на event loop используется для отправки событий из других потоков.
main_loop = asyncio.get_event_loop()
