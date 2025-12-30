#!/usr/bin/env python3
"""
Script para executar migrações manualmente
Útil para debugging ou execução fora do Docker
"""
import subprocess
import sys
import os

def run_migrations():
    """Executar migrações do Alembic"""
    print("🔄 Executando migrações do banco de dados...")
    
    os.chdir("/app")
    
    # Tentar com comando CLI
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
