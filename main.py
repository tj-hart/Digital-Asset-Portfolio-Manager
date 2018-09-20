from login_register import login_register, get_user, get_session
from pandas import DataFrame
from db import Asset, Location, Transaction
import requests
from tabulate import tabulate
from sqlalchemy import or_
from pprint import pprint

URL_PRICE = "https://min-api.cryptocompare.com/data/price?fsym={}&tsyms={}"
fiat = "USD"

login_register()
session = get_session()

def get_asset_by_symbol(symbol):
    return session.query(Asset).filter(Asset.symbol == symbol).first()


def get_location_by_name(name):
    return session.query(Location).filter(Location.name == name).first()


print("1) Portfolio Overview\n2) Transaction List\n3) Add Transaction\n4) Edit/Delete Transaction\n5) Add Location\n6) Edit/Delete Location")

response = '0'
while response not in ['1', '2', '3', '4', '5', '6']:
    response = input("--> ")

print()
if response is '1':
    user = get_user()

    asset_symbols_seen = set()
    for t in user.transactions:
        asset_symbols_seen.add(t.asset_symbol)

    assets_seen = set()
    for asset_symbol in asset_symbols_seen:
        assets_seen.add(get_asset_by_symbol(asset_symbol))

    portfolio = []
    for asset in assets_seen:
        # PRICE
        price = float(requests.get(url=URL_PRICE.format(asset.symbol, fiat)).json()[fiat])

        quantity = 0
        net_cost = 0
        avg_buy_price = 0
        avg_sell_price = 0
        denominator_buy = 0
        numerator_buy = 0
        denominator_sell = 0
        numerator_sell = 0
        delta = 0
        profit_calc = 0
        profit = 0

        # QUANTITY
        asset_transactions = session.query(Transaction).filter(or_(Transaction.asset_symbol == asset.symbol, Transaction.currency_symbol == asset.symbol, Transaction.fee_currency_symbol == asset.symbol)).all()
        for t in asset_transactions:
            if t.asset_symbol == asset.symbol and t.action == "DIVIDEND":
                quantity = quantity + float(t.volume)
            if t.asset_symbol == asset.symbol and t.action == "BUY":
                quantity = quantity + float(t.volume)
            if t.asset_symbol == asset.symbol and t.action == "SELL":
                quantity = quantity - float(t.volume)
            if t.action == "BUY" and t.currency_symbol == asset.symbol:
                quantity = quantity - (float(t.volume)*float(t.price))
            if t.action == "BUY" and t.fee_currency_symbol == asset.symbol:
                quantity = quantity - float(t.fee)
            if t.action == "SELL" and t.currency_symbol == asset.symbol:
                quantity = quantity + (float(t.volume)*float(t.price))
            if t.action == "SELL" and t.fee_currency_symbol == asset.symbol:
                quantity = quantity - float(t.fee)
            if t.action == "TRANSFER" and t.asset_symbol == asset.symbol:
                quantity = quantity - float(t.fee)
            if t.action == "OTHER" and t.asset_symbol == asset.symbol:
                quantity = quantity - float(t.fee)

            # NET COST
            cost_proceeds_usd, = session.query(Transaction.cost_proceeds_usd).filter(Transaction.trans_id == t.trans_id).first()
            price_usd, = session.query(Transaction.price_usd).filter(Transaction.trans_id == t.trans_id).first()
            fee_usd, = session.query(Transaction.fee_usd).filter(Transaction.trans_id == t.trans_id).first()
            if t.asset_symbol == asset.symbol and t.action == "BUY":
                net_cost = net_cost + cost_proceeds_usd
            if t.asset_symbol == asset.symbol and t.action == "SELL":
                net_cost = net_cost - cost_proceeds_usd
            if t.currency_symbol == asset.symbol and t.action == "BUY" and t.asset_symbol != asset.symbol:
                net_cost = net_cost - price_usd
            if t.fee_currency_symbol == asset.symbol and t.action == "BUY" and t.asset_symbol != asset.symbol:
                net_cost = net_cost - fee_usd
            if t.currency_symbol == asset.symbol and t.action == "SELL" and t.asset_symbol != asset.symbol:
                net_cost = net_cost + price_usd

            # AVG BUY PRICE
            if t.currency_symbol == asset.symbol and t.action == "SELL" and t.asset_symbol != asset.symbol:
                denominator_buy = denominator_buy + (t.price * t.volume)
            if t.asset_symbol == asset.symbol and t.action == "BUY":
                denominator_buy = denominator_buy + t.volume
            if t.currency_symbol == asset.symbol and t.action == "SELL" and t.asset_symbol != asset.symbol:
                numerator_buy = numerator_buy + price_usd
            if t.asset_symbol == asset.symbol and t.action == "BUY":
                numerator_buy = numerator_buy + price_usd

            # AVG SELL PRICE
            if t.currency_symbol == asset.symbol and t.action == "BUY" and t.asset_symbol != asset.symbol:
                denominator_sell = denominator_sell + (t.price * t.volume)
            if t.asset_symbol == asset.symbol and t.action == "SELL":
                denominator_sell = denominator_sell + t.volume
            if t.currency_symbol == asset.symbol and t.action == "BUY" and t.asset_symbol != asset.symbol:
                numerator_sell = numerator_sell + price_usd
            if t.asset_symbol == asset.symbol and t.action == "SELL":
                numerator_sell = numerator_sell + price_usd

            # PROFIT
            if t.asset_symbol == asset.symbol and t.action == "BUY":
                profit_calc = profit_calc + cost_proceeds_usd
            if t.asset_symbol == asset.symbol and t.action == "SELL":
                profit_calc = profit_calc - cost_proceeds_usd
            if t.currency_symbol == asset.symbol and t.action == "BUY" and t.asset_symbol != asset.symbol:
                profit_calc = profit_calc - price_usd
            if t.fee_currency_symbol == asset.symbol and t.action == "BUY" and t.asset_symbol != asset.symbol:
                profit_calc = profit_calc + fee_usd
            if t.currency_symbol == asset.symbol and t.action == "SELL" and t.asset_symbol != asset.symbol:
                profit_calc = profit_calc + price_usd

        quantity = "{0:.8f}".format(round(quantity, 8))
        price = "{0:.2f}".format(round(price, 2))
        market_value = "{0:.2f}".format(round(float(quantity)*float(price), 2))
        if net_cost < 0:
            net_cost = 0
        net_cost = "{0:.2f}".format(round(net_cost, 2))

        if denominator_buy == 0:
            avg_buy_price = -999999
        else:
            avg_buy_price = "{0:.2f}".format(round(numerator_buy/denominator_buy, 2))

        if denominator_sell == 0:
            avg_sell_price = -999999
        else:
            avg_sell_price = "{0:.2f}".format(round(numerator_sell/denominator_sell, 2))

        if avg_sell_price == -999999 or avg_buy_price == -999999:
            delta = -999999
        else:
            delta = 100*(float(avg_sell_price) - float(avg_buy_price)) / float(avg_buy_price)
            delta = "{0:.2f}".format(round(delta, 2))

        profit = float(market_value) - profit_calc
        profit = "{0:.2f}".format(round(profit, 2))

        entry = [asset.name, asset.symbol, quantity, price, market_value, net_cost, avg_buy_price, avg_sell_price, delta, profit]
        portfolio.append(entry)

    df = DataFrame(sorted(portfolio, reverse=True, key = lambda x: float(x[4])))
    df.columns = ['Asset Name', 'Asset Symbol', 'Quantity', 'Price ({})'.format(fiat), 'Market Value ({})'.format(fiat), 'Net Cost ({})'.format(fiat), 'Avg. Buy Price ({})'.format(fiat), 'Avg. Sell Price ({})'.format(fiat), 'Avg. Delta (%)', 'All Time Profit ({})'.format(fiat)]
    table = tabulate(df, headers='keys', tablefmt='psql', showindex=False, floatfmt=("", "", ".8f", ".2f", ".2f", ".2f", ".2f", ".2f", ".2f", ".2f"))
    table = table.replace(" -999999.00 ", "            ")
    print(table.replace(" N/A ", "     "))

if response is '2':
    all_transactions = []
    user = get_user()
    for t in user.transactions:
        transaction = [t.trans_id, t.user_id, t.asset_symbol, t.action, t.source_location, t.destination_location, t.volume, t.price, t.currency_symbol, t.fee, t.fee_currency_symbol, t.memo]
        all_transactions.append(transaction)

    df = DataFrame(all_transactions)
    df.columns = ['TX ID', 'User', 'Asset', 'Action', 'Source', 'Destination', 'Volume', 'Price', 'Currency', 'Fee', 'Fee Currency', 'Memo']
    table = tabulate(df, headers='keys', tablefmt='psql', showindex=False, floatfmt=("", "", "", "", "", "", "0.8f", "0.8f", "", "0.8f", "", ""))
    print(table.replace(" nan ", "     "))

