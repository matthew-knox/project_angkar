from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from .database import SessionLocal, engine
from .models import SensorData
import logging
import uvicorn

# Create the database tables
SensorData.metadata.create_all(bind=engine)

app = FastAPI(title="Central Command Pi API")

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pydantic schema
class SensorDataSchema(BaseModel):
    pi_id: str
    sensor_type: str
    value: float
    timestamp: str

    class Config:
        orm_mode = True

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Key authentication
API_KEY = "mysecureapikey123"

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# API to fetch all sensor data
@app.get("/sensor-data/", response_model=List[SensorDataSchema], dependencies=[Depends(verify_api_key)])
def read_sensor_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logging.info(f"Fetching data with skip={skip} and limit={limit}")
    data = db.query(SensorData).offset(skip).limit(limit).all()
    return data

# API to fetch sensor data by Pi ID
@app.get("/sensor-data/pi/{pi_id}", response_model=List[SensorDataSchema], dependencies=[Depends(verify_api_key)])
def read_sensor_data_by_pi(pi_id: str, db: Session = Depends(get_db)):
    logging.info(f"Fetching data for Pi ID: {pi_id}")
    data = db.query(SensorData).filter(SensorData.pi_id == pi_id).all()
    return data

# API to fetch sensor data by sensor type
@app.get("/sensor-data/type/{sensor_type}", response_model=List[SensorDataSchema], dependencies=[Depends(verify_api_key)])
def read_sensor_data_by_type(sensor_type: str, db: Session = Depends(get_db)):
    logging.info(f"Fetching data for sensor type: {sensor_type}")
    data = db.query(SensorData).filter(SensorData.sensor_type == sensor_type).all()
    return data

if __name__ == "__main__":
    logging.info("Starting Central Command Pi FastAPI Server...")
    uvicorn.run("central_pi_server:app", host="0.0.0.0", port=8000, reload=True)
