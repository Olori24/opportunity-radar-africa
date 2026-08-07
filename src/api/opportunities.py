from fastapi import APIRouter

router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"],
)


@router.get("/")
def list_opportunities():
    return {
        "operation": "list",
        "status": "success"
    }


@router.get("/{opportunity_id}")
def get_opportunity(opportunity_id: int):
    return {
        "operation": "get",
        "id": opportunity_id,
    }


@router.post("/")
def create_opportunity():
    return {
        "operation": "create",
        "status": "created"
    }


@router.put("/{opportunity_id}")
def update_opportunity(opportunity_id: int):
    return {
        "operation": "update",
        "id": opportunity_id,
    }


@router.delete("/{opportunity_id}")
def delete_opportunity(opportunity_id: int):
    return {
        "operation": "delete",
        "id": opportunity_id,
    }
