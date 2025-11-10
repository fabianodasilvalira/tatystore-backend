"""
Endpoints de Integração PIX (v1)
Configuração, QR Code e comprovantes
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.company import Company
from app.models.sale import Sale

router = APIRouter()


@router.post("/config", summary="Configurar chave PIX da empresa")
async def configure_pix(
    pix_key: str,
    pix_type: str,  # cpf, cnpj, email, phone
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    **Configurar Chave PIX**
    
    Registra chave PIX da empresa para geração de QR Codes.
    
    **Requer:** Admin
    
    **Tipos de chave:**
    - `cpf`: CPF do titular
    - `cnpj`: CNPJ da empresa
    - `email`: Email cadastrado
    - `phone`: Número de telefone
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Aqui é apenas demonstrativo - em produção usar banco de dados separado ou config service
    
    return {
        "message": "Chave PIX configurada com sucesso",
        "pix_key": pix_key[:3] + "*" * (len(pix_key) - 6) + pix_key[-3:],  # Mascarar
        "pix_type": pix_type
    }


@router.get("/qrcode/{sale_id}", response_model=dict, summary="Gerar QR Code PIX para venda")
async def generate_qrcode(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Gerar QR Code PIX**
    
    Gera QR Code para pagamento PIX de uma venda.
    
    **Requer:** Admin ou Gerente
    
    **Nota:** Em produção, integrar com backend PIX real (Banco Central API)
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada"
        )
    
    # Verificar isolamento
    if sale.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    return {
        "sale_id": sale_id,
        "amount": sale.total_amount,
        "qrcode": f"00020126580014br.gov.bcb.pix...",  # Simulado
        "emv": "00020126580014br.gov.bcb.pix...",
        "message": "QR Code gerado com sucesso. Apresente ao cliente para leitura."
    }


@router.post("/receipt/{sale_id}", summary="Fazer upload de comprovante PIX")
async def upload_pix_receipt(
    sale_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Upload de Comprovante PIX**
    
    Registra comprovante de pagamento PIX para uma venda.
    Arquivo salvo em `/uploads/{company_slug}/payments/`.
    
    **Requer:** Admin ou Gerente
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venda não encontrada"
        )
    
    # Verificar isolamento
    if sale.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    allowed_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas JPG, PNG e PDF são permitidos"
        )
    
    # Criar diretório se não existir
    company = db.query(Company).filter(Company.id == sale.company_id).first()
    upload_dir = f"uploads/{company.slug}/payments"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Salvar arquivo
    filename = f"pix_receipt_{sale_id}_{datetime.utcnow().timestamp()}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(await file.read())
    
    return {
        "message": "Comprovante PIX registrado com sucesso",
        "sale_id": sale_id,
        "file": filepath
    }
