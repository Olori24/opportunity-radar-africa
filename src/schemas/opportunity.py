from pydantic import BaseModel


class OpportunityCreate(BaseModel):
    title: str
    organization: str
    country: str
    category: str
    deadline: str
    url: str
    description: str


class OpportunityRead(OpportunityCreate):
    id: int
