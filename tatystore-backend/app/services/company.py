"""
Serviço de Company - Lógica de Negócio
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
import re

from app.models.company import Company
from app.models.user import User
from app.models.role import Role
from app.core.security import get_password_hash
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.core.database import SessionLocal

class CompanyService:
    
    @staticmethod
    def create_slug(name: str) -> str:
        """Cria slug a partir do nome"""
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    @staticmethod
    async def create_company(company_data) -> dict:
        """Cria nova empresa e usuário admin automaticamente"""
        db = SessionLocal()
        
        try:
            # Verificar CNPJ duplicado
            existing = db.query(Company).filter(Company.document == company_data.document).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CNPJ já cadastrado"
                )
            
            # Criar slug
            slug = CompanyService.create_slug(company_data.name)
            
            # Verificar slug duplicado
            counter = 1
            original_slug = slug
            while db.query(Company).filter(Company.slug == slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Criar empresa
            company = Company(
                name=company_data.name,
                document=company_data.document,
                email=company_data.email,
                phone=company_data.phone,
                slug=slug,
                is_active=True
            )
            
            db.add(company)
            db.flush()
            
            # Buscar role admin
            admin_role = db.query(Role).filter(Role.name == "admin").first()
            if not admin_role:
                # Criar role se não existir
                admin_role = Role(name="admin", description="Administrador")
                db.add(admin_role)
                db.flush()
            
            # Criar usuário admin
            admin_user = User(
                name=company_data.admin_name,
                email=company_data.admin_email,
                password_hash=get_password_hash(company_data.admin_password),
                company_id=company.id,
                role_id=admin_role.id,
                is_active=True
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(company)
            
            return {
                "id": company.id,
                "name": company.name,
                "slug": company.slug,
                "document": company.document,
                "email": company.email,
                "phone": company.phone,
                "admin_email": admin_user.email,
                "admin_password": company_data.admin_password
            }
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar empresa: {str(e)}"
            )
        finally:
            db.close()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        """Lista todas as empresas"""
        return db.query(Company).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_by_id(db: Session, company_id: int) -> Company:
        """Busca empresa por ID"""
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada"
            )
        return company
    
    @staticmethod
    async def update_company(company_id: int, company_data) -> dict:
        """Atualiza empresa"""
        db = SessionLocal()
        
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            
            if not company:
                return None
            
            update_data = company_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(company, field, value)
            
            db.commit()
            db.refresh(company)
            
            return {
                "id": company.id,
                "name": company.name,
                "slug": company.slug,
                "document": company.document,
                "email": company.email,
                "phone": company.phone,
                "is_active": company.is_active
            }
            
        finally:
            db.close()
