from sqlalchemy import Column, Integer, String, Float
from db import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    pi_id = Column(String, index=True)
    sensor_type = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(String)
