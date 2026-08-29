"""Adiciona colunas tipo_folga, natureza, numero_decreto, link_decreto em feriados."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

SQL = """
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS tipo_folga VARCHAR(20) NOT NULL DEFAULT 'feriado';
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS natureza VARCHAR(20) NOT NULL DEFAULT 'nacional';
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS numero_decreto VARCHAR(50);
ALTER TABLE feriados ADD COLUMN IF NOT EXISTS link_decreto VARCHAR(500);
"""

def main():
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    with app.app_context():
        for stmt in SQL.strip().split(';'):
            stmt = stmt.strip()
            if stmt:
                try:
                    db.session.execute(db.text(stmt))
                    db.session.commit()
                    print('OK:', stmt[:60] + '...')
                except Exception as e:
                    print('Erro:', e)
                    db.session.rollback()
    print('Migração feriados concluída.')

if __name__ == '__main__':
    main()
