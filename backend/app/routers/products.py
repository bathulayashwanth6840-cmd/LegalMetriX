from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models, auth, database, audit

router = APIRouter(
    prefix="/api/products",
    tags=["Products"]
)

@router.post("/", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product: schemas.ProductCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_product = models.Product(
        name=product.name,
        category=product.category,
        uploaded_by_user_id=current_user.id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Audit log (though usually we focus audit on Scans/Reports, logging Product creation is good practice)
    audit.log_audit(db, current_user.id, "CREATE_PRODUCT", "product", new_product.id)
    
    return new_product

@router.get("/", response_model=List[schemas.ProductResponse])
def get_products(
    skip: int = 0, limit: int = 100, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Depending on role, we might want to restrict who sees what, but for now we list all products
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(
    product_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
