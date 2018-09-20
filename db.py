from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import json
import requests
import pytz
from datetime import datetime
import calendar

URL_PRICE_HISTORICAL = "https://min-api.cryptocompare.com/data/pricehistorical?fsym={}&tsyms={}&ts={}"
fiat = "USD"

engine = create_engine('sqlite:///dapm.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer(), primary_key=True, unique=True)
    name = Column(String(100))
    email = Column(String(100))
    password_hash = Column(String(100))

    transactions = relationship('Transaction', backref='user', foreign_keys='Transaction.user_id')


class Asset(Base):
    __tablename__ = 'assets'

    asset_id = Column(Integer(), primary_key=True, unique=True)
    name = Column(String(100))
    symbol = Column(String(10))

    trans_asset = relationship('Transaction', backref='asset', foreign_keys='Transaction.asset_symbol')
    trans_currency = relationship('Transaction', backref='currency', foreign_keys='Transaction.currency_symbol')
    trans_fee_currency = relationship('Transaction', backref='fee_currency', foreign_keys='Transaction.fee_currency_symbol')


class Location(Base):
    __tablename__ = 'locations'

    location_id = Column(Integer(), primary_key=True, unique=True)
    name = Column(String(100))

    sources = relationship('Transaction', backref='source', foreign_keys='Transaction.source_location')
    destinations = relationship('Transaction', backref='destination', foreign_keys='Transaction.destination_location')


class Transaction(Base):
    __tablename__ = 'transactions'

    trans_id = Column(Integer(), primary_key=True, unique=True)
    user_id = Column(Integer(), ForeignKey('users.email'))
    date_time = Column(DateTime())
    asset_symbol = Column(String(10), ForeignKey('assets.symbol'))
    action = Column(String(50))
    source_location = Column(String(100), ForeignKey('locations.name'))
    destination_location = Column(String(100), ForeignKey('locations.name'))
    volume = Column(Float())
    price = Column(Float())
    currency_symbol = Column(String(10), ForeignKey('assets.symbol'))
    fee = Column(Float())
    fee_currency_symbol = Column(String(10), ForeignKey('assets.symbol'))
    price_usd = Column(Float())
    fee_usd = Column(Float())
    cost_proceeds_usd = Column(Float())
    memo = Column(String(100))

    def calculate(self):
        session.commit()
        timestamp = "{0:.0f}".format(calendar.timegm(self.date_time.timetuple()))
        print("trans_id: {}".format(self.trans_id))
        if self.action in ['TRANSFER', 'DIVIDEND', 'OTHER']:
            historical = requests.get(URL_PRICE_HISTORICAL.format(self.asset_symbol, fiat, timestamp)).json()[self.asset_symbol][fiat]
            self.price_usd = float(self.volume) * float(historical)
        else:
            historical = requests.get(URL_PRICE_HISTORICAL.format(self.currency_symbol, fiat, timestamp)).json()[self.currency_symbol][fiat]
            self.price_usd = float(self.price) * float(self.volume) * float(historical)
        if self.fee is None or float(self.fee) == 0:
            self.fee_usd = 0
        else:
            historical = requests.get(URL_PRICE_HISTORICAL.format(self.fee_currency_symbol, fiat, timestamp)).json()[self.fee_currency_symbol][fiat]
            self.fee_usd = float(self.fee) * float(historical)
        self.cost_proceeds_usd = self.price_usd + self.fee_usd

        def get_price_usd(self):
            return self.price_usd

        def get_fee_usd(self):
            return self.fee_usd

        def get_cost_proceeds_usd(self):
            return get_cost_proceeds_usd

def start_database():
    Base.metadata.create_all(engine)

    session.commit()
    assets_added = 0
    with open('asset_list.json') as f:
        asset_list = json.load(f)
        for key in asset_list.keys():
            exists = session.query(Asset.asset_id).filter_by(asset_id=asset_list[key]['id']).scalar()
            if exists is None:
                tmp = Asset(asset_id=asset_list[key]['id'], name=asset_list[key]['name'],
                            symbol=asset_list[key]['symbol'])
                session.add(tmp)
                assets_added = assets_added + 1
    session.commit()
    print("{} NEW ASSETS ADDED TO DATABASE".format(assets_added))


def get_session():
    return session


if __name__ == "__main__":
    start_database()
