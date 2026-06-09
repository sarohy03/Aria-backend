from pydantic import BaseModel


class ConnectResponse(BaseModel):
    redirect_url: str
    connection_id: str
    toolkit: str
