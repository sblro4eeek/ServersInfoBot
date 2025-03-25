from aiogram import Router
from app.handlers import router as handlers_router

main_router = Router()
main_router.include_router(handlers_router)