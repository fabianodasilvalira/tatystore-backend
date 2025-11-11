"""
Script para criar estrutura de pastas e imagens de exemplo
Cria pastas para uploads de empresas, produtos, logos e comprovantes
"""
import os
from pathlib import Path

def create_folder_structure():
    """Cria estrutura de pastas para uploads"""
    
    # Diretório base
    base_dir = Path("uploads")
    
    # Empresas
    companies = ["taty", "carol"]
    
    # Estrutura de pastas para cada empresa
    folders = [
        "products",      # Imagens de produtos
        "company",       # Logo da empresa
        "payments"       # Comprovantes PIX
    ]
    
    print("=" * 80)
    print("CRIANDO ESTRUTURA DE PASTAS PARA UPLOADS")
    print("=" * 80)
    print()
    
    # Criar pasta base
    base_dir.mkdir(exist_ok=True)
    print(f"✓ Criado: {base_dir}/")
    
    # Criar pastas para cada empresa
    for company in companies:
        company_dir = base_dir / company
        company_dir.mkdir(exist_ok=True)
        print(f"✓ Criado: {company_dir}/")
        
        for folder in folders:
            folder_path = company_dir / folder
            folder_path.mkdir(exist_ok=True)
            print(f"  ✓ Criado: {folder_path}/")
            
            # Criar arquivo .gitkeep para manter pastas vazias no git
            gitkeep = folder_path / ".gitkeep"
            gitkeep.touch()
    
    print()
    print("=" * 80)
    print("ESTRUTURA DE PASTAS CRIADA COM SUCESSO!")
    print("=" * 80)
    print()
    print("Estrutura criada:")
    print("uploads/")
    for company in companies:
        print(f"├── {company}/")
        for i, folder in enumerate(folders):
            prefix = "└──" if i == len(folders) - 1 else "├──"
            print(f"│   {prefix} {folder}/")
    print()
    print("Agora você pode fazer upload de imagens via API:")
    print("  POST /api/v1/products/{product_id}/image")
    print("  POST /api/v1/companies/{company_id}/logo")
    print()

if __name__ == "__main__":
    create_folder_structure()
