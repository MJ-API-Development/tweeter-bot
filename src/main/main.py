from os import path
import asyncio
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from src.config import config_instance
from src.tasks.schedulers import TaskScheduler

settings = config_instance().APP_SETTINGS
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    terms_of_service=settings.TERMS,
    contact={
        "name": settings.CONTACT_NAME,
        "url": settings.CONTACT_URL,
        "email": settings.CONTACT_EMAIL
    },
    license_info={
        "name": settings.LICENSE_NAME,
        "url": settings.LICENSE_URL,
    },
    docs_url=settings.DOCS_URL,
    openapi_url=settings.OPENAPI_URL,
    redoc_url=settings.REDOC_URL
)


def static_folder() -> str:
    return path.join(path.dirname(path.abspath(__file__)), '../../static')


def template_folder() -> str:
    return path.join(path.dirname(path.abspath(__file__)), '../../templates')


app.mount("/static", StaticFiles(directory=static_folder()), name="static")
templates = Jinja2Templates(directory=template_folder())

scheduler = TaskScheduler()

# this allows me to send 30 tweets over a period of 24 hours
FIFTY_MINUTES = 1500


async def scheduled_task():
    while True:
        await scheduler.run()
        await asyncio.sleep(delay=FIFTY_MINUTES)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduled_task())


@app.get("/")
def get_home(request: Request):
    context = dict(title=settings.TITLE, description=settings.DESCRIPTION, request=request)
    # return templates.TemplateResponse("index.html", context)
