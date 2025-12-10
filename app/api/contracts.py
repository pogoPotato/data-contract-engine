from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.contract_manager import ContractManager
from app.models.schemas import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractList,
    ContractSummary
)
from app.utils.exceptions import (
    DCEBaseException,
    ContractNotFoundError,
    DuplicateContractError,
    InvalidYAMLError,
    InvalidContractSchemaError
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/contracts",
    tags=["contracts"],
)


@router.post("", response_model=ContractResponse, status_code=201)
@router.post("/", response_model=ContractResponse, status_code=201)
def create_contract(
    contract_data: ContractCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"POST /contracts - Creating contract: {contract_data.name}")
    
    try:
        manager = ContractManager(db)
        contract = manager.create_contract(contract_data)
        
        return ContractResponse.from_db_model(contract)
        
    except DuplicateContractError as e:
        logger.warning(f"Duplicate contract: {contract_data.name}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except InvalidYAMLError as e:
        logger.warning(f"Invalid YAML: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except DCEBaseException as e:
        logger.error(f"Contract creation failed: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )


@router.get("", response_model=ContractList)
@router.get("/", response_model=ContractList)
def list_contracts(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    is_active: bool = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db)
):
    logger.info(
        f"GET /contracts - domain={domain}, active={is_active}, "
        f"skip={skip}, limit={limit}"
    )
    
    try:
        manager = ContractManager(db)
        contracts, total = manager.list_contracts(
            domain=domain,
            is_active=is_active,
            skip=skip,
            limit=limit
        )
        
        contract_responses = [
            ContractResponse.from_db_model(c) for c in contracts
        ]
        
        response = ContractList.paginate(
            contracts=contract_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to list contracts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract_by_id(
    contract_id: UUID = Path(..., description="Contract UUID"),
    db: Session = Depends(get_db)
):
    logger.info(f"GET /contracts/{contract_id}")
    
    try:
        manager = ContractManager(db)
        contract = manager.get_contract_by_id(contract_id)
        
        if not contract:
            raise ContractNotFoundError(contract_id=str(contract_id))
        
        return ContractResponse.from_db_model(contract)
        
    except ContractNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Failed to get contract: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )


@router.get("/by-name/{name}", response_model=ContractResponse)
def get_contract_by_name(
    name: str = Path(..., description="Contract name"),
    db: Session = Depends(get_db)
):
    logger.info(f"GET /contracts/by-name/{name}")
    
    try:
        manager = ContractManager(db)
        contract = manager.get_contract_by_name(name)
        
        if not contract:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ContractNotFoundError",
                    "message": f"Contract with name '{name}' not found"
                }
            )
        
        return ContractResponse.from_db_model(contract)
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to get contract by name: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )


@router.put("/{contract_id}", response_model=dict)
def update_contract(
    contract_id: str,
    contract_update: ContractUpdate,
    db: Session = Depends(get_db)
):
    try:
        contract_manager = ContractManager(db)
        
        contract_update.validate_contract_structure()
        
        contract, change_report = contract_manager.update_contract(
            UUID(contract_id),
            contract_update
        )
        
        return {
            "contract": ContractResponse.from_db_model(contract),
            "change_report": change_report
        }
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid UUID format"
        )
    except ContractNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidYAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidContractSchemaError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating contract: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contract: {str(e)}"
        )


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: UUID = Path(..., description="Contract UUID"),
    hard_delete: bool = Query(False, description="Permanently delete"),
    db: Session = Depends(get_db)
):
    logger.info(f"DELETE /contracts/{contract_id} (hard_delete={hard_delete})")
    
    try:
        manager = ContractManager(db)
        manager.delete_contract(contract_id, hard_delete=hard_delete)
        
        delete_type = "permanently deleted" if hard_delete else "deactivated"
        
        return {
            "message": f"Contract {delete_type} successfully",
            "contract_id": str(contract_id),
            "hard_delete": hard_delete
        }
        
    except ContractNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except DCEBaseException as e:
        logger.error(f"Contract deletion failed: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )


@router.post("/{contract_id}/activate", response_model=ContractResponse)
def activate_contract(
    contract_id: UUID = Path(..., description="Contract UUID"),
    db: Session = Depends(get_db)
):
    logger.info(f"POST /contracts/{contract_id}/activate")
    
    try:
        manager = ContractManager(db)
        contract = manager.activate_contract(contract_id)
        
        return ContractResponse.from_db_model(contract)
        
    except ContractNotFoundError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except DCEBaseException as e:
        logger.error(f"Contract activation failed: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )


@router.get("/domains/list")
def list_domains(db: Session = Depends(get_db)):
    logger.info("GET /contracts/domains/list")
    
    try:
        manager = ContractManager(db)
        domains = manager.get_domains()
        
        return {
            "domains": domains,
            "total": len(domains)
        }
        
    except Exception as e:
        logger.error(f"Failed to list domains: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalServerError", "message": str(e)}
        )