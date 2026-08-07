from fastapi import APIRouter

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


@router.get("/")
def list_opportunities():
    return {"message": "List Opportunities"}


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: int):
    return {"id": opportunity_id}


@router.post("/")
def create_opportunity():
    return {"message": "Opportunity Created"}


@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: int):
    return {"deleted": opportunity_id}
