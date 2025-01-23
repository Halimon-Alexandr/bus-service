from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, timedelta
import pytz
from BusTrafficService import Tracking

app = FastAPI()

# Додавання підтримки CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://mog-pod.pp.ua",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tracking = Tracking()

@app.get("/bus/info/")
async def get_bus_info(bus_stop_name: Optional[str] = "", offset: Optional[int] = 0):
    try:
        tracking.offset = offset
        result = tracking.get_bus_schedule(bus_stop_name)
        if "stops" in result:
            return result
        return {"next_bus_info": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
