from sqlalchemy import (create_engine, Text, Column, Integer, Numeric,
                        String, DateTime, ForeignKey, LargeBinary)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime

engine = create_engine('postgresql+psycopg2://postgres:3648@localhost:5432/finances_accounting')
Session = sessionmaker(autoflush=False, bind=engine)
session = Session()

Base = declarative_base()

class AccountsTable(Base):
    __tablename__ = 'accounts'

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    icon_url = Column(Text)
    description = Column(Text)

    transactions = relationship("TransactionsTable", back_populates="account", cascade="all, delete")
    transfers_from = relationship("TransfersTable", back_populates="from_account_ref",
                                  foreign_keys='TransfersTable.from_account')
    transfers_to = relationship("TransfersTable", back_populates="to_account_ref",
                                foreign_keys='TransfersTable.to_account')


class CategoriesTable(Base):
    __tablename__ = 'categories'

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(50), nullable=False, unique=True)
    transaction_type = Column(String(50), nullable=False)
    colour = Column(String(7), nullable=False, default="#144870")
    icon_url = Column(Text)

    transactions = relationship("TransactionsTable", back_populates="category")


class TransactionsTable(Base):
    __tablename__ = 'transactions'

    transaction_id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="SET NULL"))
    transaction_type = Column(String(50), nullable=False)
    transaction_date_time = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    check_photo = Column(LargeBinary)
    description = Column(Text)

    account = relationship("AccountsTable", back_populates="transactions")
    category = relationship("CategoriesTable", back_populates="transactions")


class TransfersTable(Base):
    __tablename__ = 'transfers'

    transfer_id = Column(Integer, primary_key=True)
    from_account = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    to_account = Column(Integer, ForeignKey("accounts.account_id", ondelete="CASCADE"), nullable=False)
    transfer_date_time = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    amount = Column(Numeric(10, 2), nullable=False, default=0.0)
    description = Column(Text)

    from_account_ref = relationship("AccountsTable", foreign_keys=[from_account],
                                    back_populates="transfers_from")
    to_account_ref = relationship("AccountsTable", foreign_keys=[to_account],
                                  back_populates="transfers_to")
