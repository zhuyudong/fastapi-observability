import os

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    app_message = os.environ.get("APP_MESSAGE", "Hello")

    return {"message": app_message}


if __name__ == "__main__":
    # update uvicorn access logger format
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
