import sys
import os
from unittest.mock import MagicMock
from fastapi import HTTPException

# Simula estrutura básica necessárias
class User:
    def __init__(self, role_name):
        self.role = MagicMock()
        self.role.name = role_name

# Copia exata da lógica do deps.py
ROLE_MAPPING = {
    # Aliases em minúsculo -> Nomes completos no banco
    "super_admin": ["Super Admin"],  # Alias exclusivo para rotas críticas
    "admin": ["Super Admin", "Administrador", "admin", "Admin"], # Super Admin herda poderes de Admin
    "gerente": ["Gerente", "gerente", "Manager"],
    "vendedor": ["Vendedor", "vendedor", "Seller"],
    "usuario": ["usuario", "User"],
}

def verify_role_logic(user_role_name, allowed_roles):
    """
    Simula a função interna de require_role do deps.py
    Retorna True se passar, False se falhar (lançaria HTTPException)
    """
    for allowed_role in allowed_roles:
        allowed_role_lower = allowed_role.lower()
        
        # Obter lista de nomes possíveis para este alias
        possible_names = ROLE_MAPPING.get(allowed_role_lower, [allowed_role])
        
        # Verificar se o role do usuário corresponde a qualquer nome possível (case-insensitive)
        for possible_name in possible_names:
            if user_role_name.lower() == possible_name.lower():
                return True
    
    return False

def run_tests():
    print("🧪 Iniciando Testes de Lógica de Permissão (TDD)...\n")
    
    # Cenário 1: Super Admin acessando rota de Super Admin (ex: Deletar empresa)
    print("1️⃣  Super Admin acessando Delete Company (require 'super_admin')...")
    result = verify_role_logic("Super Admin", ["super_admin"])
    if result:
        print("✅ PASSOU: Super Admin tem acesso a 'super_admin'.")
    else:
        print("❌ FALHOU: Super Admin deveria ter acesso.")

    # Cenário 2: Super Admin acessando rota comum de Admin (ex: Criar Produto)
    print("\n2️⃣  Super Admin acessando Criar Produto (require 'admin')...")
    result = verify_role_logic("Super Admin", ["admin"])
    if result:
        print("✅ PASSOU: Super Admin HERDA acesso de 'admin' (Correto).")
    else:
        print("❌ FALHOU: Super Admin deveria herdar acesso de Admin.")

    # Cenário 3: Admin Comum acessando rota de Super Admin (ex: Deletar empresa)
    print("\n3️⃣  Administrador acessando Delete Company (require 'super_admin')...")
    result = verify_role_logic("Administrador", ["super_admin"])
    if not result:
        print("✅ PASSOU: Administrador NÃO conseguiu acessar rota de 'super_admin'.")
    else:
        print("❌ FALHOU: ALERTA DE SEGURANÇA! Admin comum acessou rota de Super Admin.")

    # Cenário 4: Admin Comum acessando rota de Admin (ex: Criar Produto)
    print("\n4️⃣  Administrador acessando Criar Produto (require 'admin')...")
    result = verify_role_logic("Administrador", ["admin"])
    if result:
        print("✅ PASSOU: Administrador tem acesso a rotas de 'admin'.")
    else:
        print("❌ FALHOU: Administrador deveria ter acesso.")
        
    print("\n🏁 Fim dos Testes.")

if __name__ == "__main__":
    run_tests()
