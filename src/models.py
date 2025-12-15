from sqlalchemy import Column, Integer, String, Date, Float, DateTime, Text, BigInteger, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from src.config import DATABASE_URL
import hashlib
from datetime import datetime

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(50), default='viewer')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)


class ExamRecord(Base):
    __tablename__ = 'exam_records'

    id = Column(Integer, primary_key=True)
    patient_unique_id = Column(String(64), index=True)
    
    geral__emissao = Column(String(50))
    geral__hora = Column(String(20))
    geral__uf = Column(String(10))
    
    unidade_de_saude__nome = Column(String(300))
    unidade_de_saude__cnes = Column(BigInteger)
    unidade_de_saude__data_da_solicitacao = Column(Date)
    unidade_de_saude__uf = Column(String(10))
    unidade_de_saude__municipio = Column(String(200))
    distrito_sanitario = Column(String(100), index=True)
    unidade_de_saude__n_do_exame = Column(String(100))
    unidade_de_saude__n_do_protocolo = Column(String(100))
    unidade_de_saude__n_do_prontuario = Column(String(100))
    
    paciente__cartao_sus = Column(BigInteger, index=True)
    paciente__sexo = Column(String(20))
    paciente__nome = Column(String(300), index=True)
    paciente__idade = Column(Integer)
    paciente__data_do_nascimento = Column(Date)
    paciente__telefone = Column(String(50))
    paciente__mae = Column(String(300), index=True)
    paciente__bairro = Column(String(200))
    paciente__endereco = Column(String(500))
    paciente__municipio = Column(String(200))
    paciente__uf = Column(String(10))
    paciente__cep = Column(String(20))
    paciente__numero = Column(String(50))
    paciente__complemento = Column(String(200))
    
    prestador_de_servico__nome = Column(String(300))
    prestador_de_servico__cnes = Column(BigInteger)
    prestador_de_servico__cnpj = Column(String(30))
    prestador_de_servico__data_da_realizacao = Column(Date)
    prestador_de_servico__uf = Column(String(10))
    prestador_de_servico__municipio = Column(String(200))
    
    resultado_exame__indicacao__tipo_de_mamografia = Column(String(200))
    resultado_exame__indicacao__mamografia_de_rastreamento = Column(String(200))
    resultado_exame__mamografia__numero_de_filmes = Column(String(50))
    resultado_exame__mama_direita__pele = Column(String(200))
    resultado_exame__mama_direita__tipo_de_mama = Column(String(200))
    resultado_exame__linfonodos_axilares__linfonodos_axilares = Column(String(200))
    resultado_exame__linfonodos_axilares__dilatacao_ductal = Column(String(200))
    resultado_exame__achados_benignos__achados_benignos = Column(String(500))
    resultado_exame__mama_esquerda__pele = Column(String(200))
    resultado_exame__mama_esquerda__tipo_de_mama = Column(String(200))
    resultado_exame__classificacao_radiologica__mama_direita = Column(String(200))
    resultado_exame__classificacao_radiologica__mama_esquerda = Column(String(200))
    resultado_exame__recomendacoes = Column(Text)
    
    responsavel_pelo_resultado__responsavel = Column(String(300))
    responsavel_pelo_resultado__conselho = Column(String(100))
    responsavel_pelo_resultado__cns = Column(String(50))
    responsavel_pelo_resultado__data_da_liberacao = Column(Date)
    
    birads_direita = Column(String(10))
    birads_esquerda = Column(String(10))
    birads_max = Column(String(10))
    wait_days = Column(Integer)
    conformity_status = Column(String(50))
    year = Column(Integer, index=True)
    month = Column(Integer)
    
    resultado_exame__observacoes_gerais = Column(Text)
    resultado_exame__achados_benignos = Column(Text)
    resultado_exame__achados_no_exame_clinico = Column(Text)
    resultado_exame__nodulos__nodulo_01 = Column(Text)
    resultado_exame__nodulos__nodulo_02 = Column(Text)
    resultado_exame__nodulos__nodulo_03 = Column(Text)
    resultado_exame__microcalcificacoes = Column(Text)
    resultado_exame__radioterapia = Column(String(200))
    resultado_exame__cirurgias_realizadas = Column(Text)


class TermoLinkage(Base):
    __tablename__ = 'termo_linkage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cartao_sus = Column(BigInteger, index=True)
    cpf = Column(String(14))
    telefone = Column(String(50))
    data_nascimento = Column(String(20))
    data_solicitacao_esaude = Column(Date)
    data_insercao_resultado_esaude = Column(Date)
    ultima_apac_cancer = Column(Date)
    nome_esaude = Column(String(300))
    comparacao_nomes = Column(String(50))


def generate_patient_id(cartao_sus, nome, mae):
    key_string = f"{cartao_sus or ''}|{nome or ''}|{mae or ''}".upper().strip()
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]


def get_engine():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    return create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    engine = get_engine()
    Base.metadata.create_all(engine)


def drop_all_tables():
    engine = get_engine()
    Base.metadata.drop_all(engine)
