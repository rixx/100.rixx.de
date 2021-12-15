from pathlib import Path
import json

from aiohttp import web
from aiofile import async_open
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

async def write_data(key, interval):
    if not DATA_PATH.exists():
        raise Exception("boo")
    data = await get_data()
    data[key]["count"] += interval
    async with async_open(DATA_PATH, "w") as f:
        await f.write(json.dumps(data))
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
        data = await write_data(data["key"], interval=1 if data["direction"] == "up" else -1)
    return {"data": data, "admin": admin}



app = web.Application()
setup(app, loader=FileSystemLoader(Path(__file__).parent / "templates"))
app.add_routes([web.get("/", home), web.get("/{secret}", home), web.post("/{secret}", home_admin)])

if __name__ == "__main__":
    web.run_app(app)
