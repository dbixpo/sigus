# -*- coding: utf-8 -*-
"""Empresas Contratadas — para vincular às ações e contratos."""
from datetime import datetime
from app import db
from app.utils import prefixed_static_url


class EmpresaContratada(db.Model):
    """Empresa contratada que pode ser vinculada às ações e contratos."""
    __tablename__ = 'empresas_contratadas'

    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), nullable=False, unique=True)
    razao_social = db.Column(db.String(255), nullable=False)
    endereco = db.Column(db.Text)  # legado; preferir campos estruturados
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))  # armazenado só dígitos
    telefone = db.Column(db.String(30))  # telefone comercial (dígitos ou mascarado)
    email = db.Column(db.String(150))   # e-mail comercial
    # Ponto de Suporte Local — como a empresa é conhecida na cidade e contatos do suporte
    nome_comum = db.Column(db.String(150))  # ex: "Suporte SIS"
    telefone_suporte = db.Column(db.String(30))
    email_suporte = db.Column(db.String(150))
    logo_filename = db.Column(db.String(200))  # em static/uploads/empresas/
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    # Tipos de CNPJ para seleção em vínculos
    cnpj_estagio = db.Column(db.Boolean, nullable=False, default=False)
    cnpj_residencia = db.Column(db.Boolean, nullable=False, default=False)
    cnpj_vinculo_empregaticio_cpd = db.Column(db.Boolean, nullable=False, default=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    contratos = db.relationship('Contrato', back_populates='empresa_contratada',
                                foreign_keys='Contrato.empresa_id', lazy='dynamic')

    @property
    def foto_url(self):
        if self.logo_filename:
            return prefixed_static_url(f'/static/uploads/empresas/{self.logo_filename}')
        return None

    @staticmethod
    def _fmt_telefone(val):
        """Formata telefone para exibição: (00) 00000-0000 ou (00) 0000-0000."""
        if not val:
            return None
        d = ''.join(c for c in str(val) if c.isdigit())
        if len(d) == 11:
            return f'({d[:2]}) {d[2:7]}-{d[7:]}'
        if len(d) == 10:
            return f'({d[:2]}) {d[2:6]}-{d[6:]}'
        return val

    @staticmethod
    def _fmt_cep(val):
        """Formata CEP para exibição: 00000-000."""
        if not val:
            return None
        d = ''.join(c for c in str(val) if c.isdigit())[:8]
        if len(d) == 8:
            return f'{d[:5]}-{d[5:]}'
        return val

    @property
    def telefone_formatado(self):
        return self._fmt_telefone(self.telefone)

    @property
    def telefone_suporte_formatado(self):
        return self._fmt_telefone(self.telefone_suporte)

    @property
    def cep_formatado(self):
        return self._fmt_cep(self.cep)

    @property
    def endereco_completo(self):
        """Monta endereço a partir dos campos ou usa endereco legado."""
        partes = []
        if self.logradouro:
            partes.append(self.logradouro)
        if self.numero:
            partes.append(self.numero)
        if self.complemento:
            partes.append(self.complemento)
        if self.bairro:
            partes.append(self.bairro)
        if self.cidade:
            cid_est = self.cidade
            if self.estado:
                cid_est += f' — {self.estado}'
            partes.append(cid_est)
        if self.cep:
            partes.append(self.cep_formatado or self.cep)
        if partes:
            return ', '.join(partes)
        return self.endereco

    def __repr__(self):
        return f'<EmpresaContratada {self.razao_social}>'
