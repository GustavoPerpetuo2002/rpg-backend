#!/usr/bin/env python3
"""
Script para inicializar o banco de dados do RPG
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app, db
from src.models.user import User
from src.models.character import Character
from src.models.npc import NPC
from src.models.game_session import GameSession

def init_database():
    """Inicializa o banco de dados criando todas as tabelas"""
    with app.app_context():
        try:
            # Remover banco existente se houver problemas
            db_path = 'rpg_database.db'
            if os.path.exists(db_path):
                print(f"Removendo banco existente: {db_path}")
                os.remove(db_path)
            
            # Criar todas as tabelas
            print("Criando tabelas do banco de dados...")
            db.create_all()
            
            print("✅ Banco de dados inicializado com sucesso!")
            print("Tabelas criadas:")
            print("- users")
            print("- characters") 
            print("- npcs")
            print("- game_sessions")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("🎲 Inicializando banco de dados do RPG...")
    success = init_database()
    if success:
        print("🎉 Pronto! O servidor pode ser iniciado agora.")
    else:
        print("💥 Falha na inicialização. Verifique os erros acima.")
        sys.exit(1)

