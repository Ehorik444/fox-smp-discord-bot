import asyncio
import traceback

def safe_task(name):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    print(f"[{name}] ERROR:", e)
                    traceback.print_exc()
                    await asyncio.sleep(3)  # не падаем, а ждём и продолжаем
        return wrapper
    return decorator
