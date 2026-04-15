from pydantic import BaseModel



class SimpleMessageSchema(BaseModel):
    message: str