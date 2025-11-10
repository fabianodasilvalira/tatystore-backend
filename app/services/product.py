"""
Serviço de Product - Lógica de Negócio
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    
    @staticmethod
    def create_product(db: Session, product_data: ProductCreate, company_id: int) -> Product:
        """Cria novo produto"""
        product = Product(
            **product_data.model_dump(),
            company_id=company_id
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product
    
    @staticmethod
    def get_by_company(db: Session, company_id: int, skip: int = 0, limit: int = 100) -> List[Product]:
        """Lista produtos da empresa"""
        return db.query(Product).filter(
            Product.company_id == company_id,
            Product.is_active == True
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, product_id: int, company_id: int) -> Product:
        """Busca produto por ID (com validação de empresa)"""
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.company_id == company_id
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado"
            )
        
        return product
    
    @staticmethod
    def update_product(db: Session, product_id: int, product_data: ProductUpdate, company_id: int) -> Product:
        """Atualiza produto"""
        product = ProductService.get_by_id(db, product_id, company_id)
        
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return product
    
    @staticmethod
    def get_low_stock(db: Session, company_id: int) -> List[Product]:
        """Lista produtos com estoque baixo"""
        return db.query(Product).filter(
            Product.company_id == company_id,
            Product.stock_quantity <= Product.min_stock,
            Product.is_active == True
        ).all()
