from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Text,
    ForeignKey,
    TIMESTAMP,
    func,
)


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()

class Product(Base):
    __tablename__ = 'product'
    id_product = Column(Integer, primary_key=True, autoincrement=True)
    name_product = Column(String(255), nullable=False)

    # Relacionamento com a tabela Offers
    offers = relationship('Offers', back_populates='product')


class Store(Base):
    __tablename__ = 'store'
    id_store = Column(Integer, primary_key=True)
    name_store = Column(String(255), nullable=False)
    insertion_date = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relacionamento com a tabela Offers
    offers = relationship('Offers', back_populates='store')


class Marketplace(Base):
    __tablename__ = 'marketplace'
    id_marketplace = Column(Integer, primary_key=True)
    name_marketplace = Column(String(255), nullable=False)

    # Relacionamento com a tabela Offers
    offers = relationship('Offers', back_populates='marketplace')


class Offers(Base):
    __tablename__ = 'offers'
    id_offer = Column(Integer, primary_key=True)
    title_offer = Column(String(255), nullable=False)
    value_offer = Column(Numeric(10, 2))
    discount_offer_decimals = Column(Numeric(5, 2))
    number_of_offer_page = Column(Integer)
    previous_value = Column(Numeric(10, 2))
    link_offer = Column(Text)
    date_time_offer = Column(TIMESTAMP, nullable=False)

    # Chaves estrangeiras
    fk_product_id_product = Column(Integer, ForeignKey('product.id_product'), nullable=False)
    fk_marketplace_id_marketplace = Column(Integer, ForeignKey('marketplace.id_marketplace'), nullable=False)
    fk_store_id_store = Column(Integer, ForeignKey('store.id_store'), nullable=False)

    # Relacionamentos
    product = relationship('Product', back_populates='offers')
    marketplace = relationship('Marketplace', back_populates='offers')
    store = relationship('Store', back_populates='offers')