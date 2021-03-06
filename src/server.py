import json
from pathlib import Path

from aiofile import async_open
from aiohttp import web
from aiohttp_jinja2 import setup, template
from jinja2 import FileSystemLoader

CONFIG = None
DATA_PATH = Path(__file__).parent / "data.json"

with open(Path(__file__).parent / "config.json") as f:
    CONFIG = json.load(f)


async def get_data():
    if not DATA_PATH.exists():
        return {}
    async with async_open(DATA_PATH) as f:
        content = await f.read()
    return json.loads(content)


async def write_to_file(data):
    async with async_open(DATA_PATH, "w") as f:
        await f.write(json.dumps(data))


async def write_data(key, interval, reason, learned, name=None):
    if not DATA_PATH.exists():
        raise Exception("boo")
    data = await get_data()
    if key not in data:
        data[key] = {"name": name, "count": 0}
    data[key]["count"] += interval
    data[key]["reason"] = reason
    data[key]["learned"] = learned
    await write_to_file(data)
    return data


async def delete_data(key):
    data = await get_data()
    data.pop(key, None)
    await write_to_file(data)
    return data


@template("index.html")
async def home(request, data=None, admin=False):
    if not admin and request.match_info.get("secret") == CONFIG["secret_key"]:
        admin = True
    if not data:
        data = await get_data()
    return {"data": data, "admin": admin}


@template("index.html")
async def home_admin(request):
    admin = False
    if request.match_info.get("secret") == CONFIG["secret_key"]:
        admin = True
        data = await request.post()
        if data.get("action") == "delete":
            data = await delete_data(key=data["key"])
        else:
            interval = 0
            if data.get("direction") == "up":
                interval = 1
            elif data.get("direction") == "down":
                interval = -1
            data = await write_data(
                data["key"],
                interval=interval,
                reason=data["reason"],
                learned=data["learned"],
                name=data.get("name"),
            )
    return {"data": data, "admin": admin}


def web_app_wrapper():
    app = web.Application()
    setup(app, loader=FileSystemLoader(Path(__file__).parent / "templates"))
    app.add_routes(
        [
            web.get("/", home),
            web.get("/{secret}", home),
            web.post("/{secret}", home_admin),
        ]
    )
    return app


async def web_app():
    return web_app_wrapper()


if __name__ == "__main__":
    app = web_app_wrapper()
    web.run_app(app)
