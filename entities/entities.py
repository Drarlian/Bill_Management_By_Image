from pydantic import BaseModel
from datetime import datetime


class Upload(BaseModel):
    image: str
    customer_code: str
    measure_datetime: datetime
    measure_type: str


class ConfirmBody(BaseModel):
    measure_uuid: str
    confirmed_value: float
