from sqlalchemy import Column, Integer, String, Date, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL

Base = declarative_base()


class ExamRecord(Base):
    __tablename__ = 'exam_records'

    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50))
    health_unit = Column(String(200))
    health_unit_code = Column(String(20))
    region = Column(String(100))
    municipality = Column(String(100))
    request_date = Column(Date)
    completion_date = Column(Date)
    wait_days = Column(Integer)
    birads_category = Column(String(10))
    exam_type = Column(String(100))
    age_group = Column(String(50))
    conformity_status = Column(String(50))
    year = Column(Integer)
    month = Column(Integer)


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
