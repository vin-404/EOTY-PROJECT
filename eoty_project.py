#################################################################################################################################
## IMPORTS
# MAIN
import pandas as pd
import csv 
from kivy.app import App
from kivymd.app import MDApp
from kivy.lang import Builder
#OTHER
import os
import random
import sys
import time
import requests
import re
# KIVY
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import Screen, ScreenManager, SwapTransition
from kivy.uix.widget import Widget
from kivy.graphics import Line
from kivy.clock import Clock
from kivy.uix.image import Image,CoreImage 
from kivy.properties import StringProperty, NumericProperty
# KIVYMD
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDIcon, MDLabel
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.button import MDTextButton, MDFillRoundFlatIconButton, MDRoundFlatIconButton, MDRaisedButton, MDFloatingActionButton, MDRectangleFlatIconButton, MDFillRoundFlatButton
from kivy.metrics import dp
from kivymd.uix.list import ThreeLineIconListItem, IconLeftWidget, OneLineIconListItem
from kivymd.color_definitions import colors, light_colors, text_colors,theme_colors
from kivymd.uix.datatables import MDDataTable
from kivymd.app import MDApp
from kivymd.icon_definitions import md_icons
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.checkbox import CheckBox
# IMPORT THE LIBRARY
import yfinance as yf
from datetime import datetime
#SQL
import mysql.connector
import sys
import time

#MatPlotLib 
from PIL import Image as PILImage
import matplotlib.pyplot as plt

#Misc
import random
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
#################################################################################################################################
# Initial database set-up + connection
my_db = mysql.connector.connect( 
    host = 'localhost', 
    user = 'root', 
    password = 'mysql', 
    database = 'simplystock'
)

user=''
passwrd=''
mycursor = my_db.cursor()
#################################################################################################################################
# Initialise money rounding to avoid crash
def money(x) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TICKER_FILE = os.path.join(BASE_DIR, "ticker.csv")
PLOT_PATH = os.path.join(BASE_DIR, "plot.png")
    
API_KEY = "d3cn6m9r01qmnfgefkggd3cn6m9r01qmnfgefkh0"

def get_price_safe(symbol):
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        r = requests.get(url, timeout=6)
        data = r.json() if r.ok else {}
        cur = float(data.get("c", 0.0))
        prev = float(data.get("pc", 0.0))
        return cur, prev
    except Exception:
        return 0.0, 0.0

STOCK_CACHE = {}

def get_price_cached(symbol, ttl=60):
    now = time.time()
    if symbol in STOCK_CACHE:
        price, prev, ts = STOCK_CACHE[symbol]
        if now - ts < ttl:
            return price, prev
    cur, prev = get_price_safe(symbol)
    STOCK_CACHE[symbol] = (cur, prev, now)
    return cur, prev

def set_balance_label(screen, text):
    for candidate in ("balancebutton6", "balance", "balance_label"):
        if candidate in screen.ids:
            screen.ids[candidate].text = text
            return

def strip_bbcode(s):
    return re.sub(r'\[/?[^\]]+\]', '', s or '')

reloadbuyingraph = False
reloadsellingraph = False
reloadtradewingraph = False

#################################################################################################################################
# WINDOW SIZE
height = 450
width = 800
Window.size = (width, height)
datatableupdate=True
username, passwrd='',''
#################################################################################################################################
## COLORS
'SSRED = 0.996078431372549, 0.3725490196078431, 0.3333333333333333, 1'
'SSGRAY = 0.4156862745098039, 0.5529411764705882, 0.5725490196078431, 1'
'SSBLACK = 0.1803921568627451, 0.192156862745098, 0.203921568627451, 1'
# THEME
theme = 'Light'
palette = 'Red'
hue = 'A200'
bgpalette = 'Gray'
bghue = '800'
# FONT SIZE
FONT_SIZE_SMALL = 16
FONT_SIZE_MEDIUM = 20
FONT_SIZE_LARGE = 32
FONT_SIZE_XL = 48
#################################################################################################################################
# SIGNUP SCREEN
class SignWindow(Screen):
    def DoSignUp(self,user,password,firstname,lastname,aadhar,phone):
        global username, passwrd
        app = App.get_running_app()
        app.username = user
        app.password = password
        app.firstname = firstname
        app.lastname = lastname
        app.phone = phone
        app.aadhar = aadhar
        username=user
        passwrd=password
        balance=0
        try:
            mycursor.execute(f"INSERT INTO login values ('{user}', '{password}' , '{firstname}' , '{lastname}' , '{phone}' , {aadhar} , {balance});")
            my_db.commit()
            self.ids.signuplabel.text= "Signed up!"
            app.root.current= 'homewin'
        except:
            self.ids.signuplabel.text= "Username already exists!"
#################################################################################################################################
# LOGIN SCREEN
class LoginWindow(Screen):
    def DoLogin(self,user,password):
        global username, passwrd
        app = App.get_running_app()
        app.username = user
        app.password = password
        username=user
        passwrd=password
        #VARIABLE FOR LOGIN AND PASSWORD
        app.username = user
        app.password = password

        login_username = user
        mycursor.execute(f"SELECT* from login WHERE Username = '{login_username}';")
        login_search_output=mycursor.fetchall()
        if login_search_output==[]:
            self.ids.loginlabel.text= "Username or Password is incorrect"
        else:
            login_password=password
            if login_password==login_search_output[0][1]:
                app.root.current = 'homewin'
            else:
                self.ids.loginlabel.text= "Username or Password is incorrect"
        app.config.read(app.get_application_config())
        app.config.write()
        
#################################################################################################################################

#################################################################################################################################
# HOME SCREEN
class HomeWindow(Screen):

    def DoBalance(self):
        mycursor.execute(f"SELECT balance FROM login WHERE username='{username}';")
        bal = float(mycursor.fetchall()[0][0])
        set_balance_label(self, f"Balance : {bal:.2f}")

    def StockTracking(self):
        plt.clf()
        a,b,c,d=random.choice([1,10,3,6]),random.choice([10,40,70,40]),random.choice([1,8,3,9]),random.choice([6,20,3,40])
        xpoints = np.array([a,b])
        ypoints = np.array([c,d])
        plt.plot(xpoints, ypoints)
        plt.savefig('EOTY/Plot image.png')
        self.ids.Image1.reload()

    def fillbuttons(self):
        stocks = ["BTM", "AMZN", "GME", "AAPL"]   
        labels = ["l1", "l2", "l3", "l4"]       
        icons  = ["b1", "b2", "b3", "b4"]       

        for i, sym in enumerate(stocks):
            cur, prev = get_price_cached(sym)

            if cur > prev:
                icon, color = "arrow-up-bold", "green"
            elif cur < prev:
                icon, color = "arrow-down-bold", "red"
            else:
                icon, color = "minus-thick", "#808080"

            getattr(self.ids, labels[i]).text = f"{cur:.2f}"
            getattr(self.ids, icons[i]).icon = icon
            getattr(self.ids, icons[i]).icon_color = color

    def SwitchTab(self):
        self.ids.btm_tab.switch_tab('trading')

    def buybtc(self):
        global cursticker, reloadbuyingraph, bcursvalue, bsname
        bsname, cursticker = "Bitcoin Depot Inc. Class A Common Stock", "BTM"
        bcursvalue, _ = get_price_cached(cursticker)
        reloadbuyingraph = True
        App.get_running_app().root.current = "buywin"

    def buyamzn(self):
        global cursticker, reloadbuyingraph, bcursvalue, bsname
        bsname, cursticker = "Amazon.com Inc. Common Stock", "AMZN"
        bcursvalue, _ = get_price_cached(cursticker)
        reloadbuyingraph = True
        App.get_running_app().root.current = "buywin"

    def buygme(self):
        global cursticker, reloadbuyingraph, bcursvalue, bsname
        bsname, cursticker = "GameStop Corp.", "GME"
        bcursvalue, _ = get_price_cached(cursticker)
        reloadbuyingraph = True
        App.get_running_app().root.current = "buywin"

    def buyapl(self):
        global cursticker, reloadbuyingraph, bcursvalue, bsname
        bsname, cursticker = "Apple Inc.", "AAPL"
        bcursvalue, _ = get_price_cached(cursticker)
        reloadbuyingraph = True
        App.get_running_app().root.current = "buywin"

    def add_datatable1(self, stock):
        app = App.get_running_app()
        app.stock = stock
        query = (stock or "").strip().lower()
        rows = []

        with open(TICKER_FILE) as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                symbol = (row[0] or "").strip()
                name   = (row[1] or "").strip()
                if not symbol or not name:
                    continue
                if query in symbol.lower() or query in name.lower():
                    cur, prev = get_price_cached(symbol)
                    pct = round(((cur - prev) / prev) * 100, 3) if prev else 0
                    if cur > prev:
                        icon, colour = "arrow-up-bold", [39/255, 174/255, 96/255, 1]
                    elif cur < prev:
                        icon, colour = "arrow-down-bold", [1, 0, 0, 1]
                    else:
                        icon, colour = "minus-thick", [108/255, 122/255, 137/255, 1]
                    rows.append((f"[color=#FFFFFF]{symbol}[/color]", (icon, colour, name), f"{pct:+.3f}"))

        if not rows:
            rows = [("", "No Stock Found", "No Data")]
        rows.append(("", "", ""))  # padding

        self.ids.ancl1.clear_widgets()
        self.data_tables = MDDataTable(
            size_hint=(1, 0.95),
            rows_num=20,
            pos_hint={"center_x": 0.3, "center_y": 0.15},
            background_color_header="#6a8d92",
            elevation=0,
            background_color="#d4d4d4",
            column_data=[("", dp(1)), ("Stock Name", dp(100)), ("Current Trend", dp(100))],
            row_data=rows,
        )
        self.data_tables.bind(on_row_press=self.check1)
        self.ids.ancl1.add_widget(self.data_tables)
    
    def check1(self, instance_table, instance_row):
        symbol = ""
        try:
            symbol = getattr(instance_row, "text", "") or ""
        except Exception:
            pass
        if not symbol and hasattr(instance_row, "cells"):
            try:
                symbol = instance_row.cells[0].text
            except Exception:
                pass
        symbol = strip_bbcode(symbol).strip()
        if symbol:
            self.showstock1(symbol)

    def showstock1(self, stock):
        global cursticker, bsname, bcursvalue, reloadbuyingraph
        app = App.get_running_app()
        cursticker = stock
        bsname = stock

        cur, prev = get_price_cached(cursticker)
        bcursvalue = cur

        # tiny 2-point plot
        plt.clf()
        xpoints = np.array([0, 1])
        ypoints = np.array([prev, cur])
        plt.plot(xpoints, ypoints, marker="o")
        plt.title(f"Trend for {cursticker}")
        plt.xlabel("Time"); plt.ylabel("Price")
        plt.savefig(PLOT_PATH)

        reloadbuyingraph = True
        app.root.current = "buywin"
#################################################################################################333
    def add_datatable(self):
        mycursor.execute(f"SELECT * FROM stocks WHERE username='{username}';")
        portfolio = mycursor.fetchall()
        rows = []

        for r in portfolio:
            sname = r[1]
            shares = int(r[2])
            invested = float(r[3])
            symbol = r[4]
            cur, prev = get_price_cached(symbol)
            current_value = shares * cur
            pnl = current_value - invested
            rows.append((sname, str(shares), f"{cur:.2f}", f"{pnl:.2f}"))

        if not rows:
            rows = [("No Stocks", "-", "-", "-")]

        self.ids.ancl.clear_widgets()
        self.data_tables = MDDataTable(
            size_hint=(1, 0.95),
            rows_num=20,
            pos_hint={"center_x": 0.3, "center_y": 0.15},
            background_color_header="#6a8d92",
            elevation=0,
            background_color="#d4d4d4",
            column_data=[("Stock", dp(100)), ("Shares", dp(50)), ("Current Price", dp(80)), ("Profit/Loss", dp(80))],
            row_data=rows,
        )
        self.data_tables.bind(on_row_press=self.check)
        self.ids.ancl.add_widget(self.data_tables)

    def check(self,instance_table,instance_row):
        global selectedstockid,cursid
        ind = instance_row.index // 6 # number of columns
        row_data = instance_table.row_data[ind] 
        selectedstockid=(row_data[1][2])
        try:
            cursid=selectedstockid
        except:
            cursid=''
        self.showstock()


    def showstock(self, stock):
        global cursid, tcursvalue, reloadsellingraph
        app = App.get_running_app()
        cursid = stock

        mycursor.execute(f"SELECT ticker FROM stocks WHERE sname='{cursid}' AND username='{username}';")
        symbol = mycursor.fetchall()[0][0]

        cur, prev = get_price_cached(symbol)
        tcursvalue = cur

        plt.clf()
        xpoints = np.array([0, 1])
        ypoints = np.array([prev, cur])
        plt.plot(xpoints, ypoints, marker="o")
        plt.title(f"Trend for {symbol}")
        plt.xlabel("Time"); plt.ylabel("Price")
        plt.savefig(PLOT_PATH)

        reloadsellingraph = True
        app.root.current = "tradewin"
#################################################################################################################################
class TradeWindow(Screen):
    def DoBalance(self):
        global balance
        mycursor.execute(f"SELECT balance from login WHERE username = '{username}';")
        balancefetch=mycursor.fetchall()
        balance=balancefetch[0][0]
        self.ids.balancebutton1.text = f'Balance : {str(balance)}'

    def graph(self):
        global reloadtradewingraph, tsname, tshares, tcursvalue, tprofitmoney, tprofitpercentage
        app = App.get_running_app()

        if reloadtradewingraph:
            self.ids.tradewingraph.reload()
        reloadtradewingraph = False

        mycursor.execute(f"SELECT money FROM stocks WHERE sname='{tsname}' AND username='{username}';")
        invested_money = float(mycursor.fetchall()[0][0])

        current_value = tshares * tcursvalue
        tprofitmoney = current_value - invested_money
        tprofitpercentage = (tprofitmoney / invested_money * 100) if invested_money > 0 else 0

        self.ids.sname.text = str(tsname)
        self.ids.shares.text = "Number of Shares: " + str(tshares)
        self.ids.curmoney.text = "Current Value $: " + f"{tcursvalue:.2f}"
        self.ids.profitmoney.text = "Profit: " + f"{tprofitmoney:.2f}"
        self.ids.profpercentage.text = "Profit Percentage: " + f"{tprofitpercentage:.2f}"

    def DoSell(self, sellamt):
        global balance, tshares, tcursvalue, tsname
        app = App.get_running_app()

        mycursor.execute(f"SELECT * FROM stocks WHERE sname='{cursid}' AND username='{username}';")
        data = mycursor.fetchall()
        if not data:
            self.ids.selllabel.text = "Error: No such stock in your portfolio."
            return

        tsname = data[0][1]
        tshares = int(data[0][2])
        symbol = data[0][4]

        try:
            sellamt = int(sellamt)
        except ValueError:
            self.ids.selllabel.text = "Error: Enter a valid number of shares."
            return
        if sellamt <= 0 or sellamt > tshares:
            self.ids.selllabel.text = "Not enough shares!"
            return

        cur, prev = get_price_cached(symbol)
        if cur <= 0:
            self.ids.selllabel.text = "Error: no valid price data."
            return
        tcursvalue = cur

        # update shares
        remaining = tshares - sellamt
        if remaining > 0:
            mycursor.execute(f"UPDATE stocks SET shares={remaining} WHERE username='{username}' AND sname='{tsname}';")
        else:
            mycursor.execute(f"DELETE FROM stocks WHERE username='{username}' AND sname='{tsname}';")
        my_db.commit()

        # update balance
        mycursor.execute(f"SELECT balance FROM login WHERE username='{username}';")
        balance = float(mycursor.fetchall()[0][0])
        newbalance = balance + (sellamt * tcursvalue)
        mycursor.execute(f"UPDATE login SET balance={newbalance} WHERE username='{username}';")
        my_db.commit()

        self.DoBalance()
        self.ids.shares.text = f"Number of Shares: {remaining}"
        self.ids.selllabel.text = f"Sold {sellamt} shares successfully!"

################################################################################################################################# 

class TransactionWindow(Screen):
    def GetBalance(self, bal):
        top_up = money(bal)
        mycursor.execute(f"SELECT balance FROM login WHERE username='{username}';")
        old = float(mycursor.fetchall()[0][0])
        newbalance = money(old + top_up)
        mycursor.execute(f"UPDATE login SET balance={newbalance} WHERE username='{username}';")
        my_db.commit()
        self.DoBalance()

    def DoBalance(self):
        global balance
        mycursor.execute(f"SELECT balance from login WHERE username = '{username}';")
        balancefetch=mycursor.fetchall()
        balance=balancefetch[0][0]
        self.ids.balancebutton2.text = f'Balance : {str(balance)}'

#################################################################################################################################

class BuyWindow(Screen):
    def DoBalance(self):
        global balance
        mycursor.execute(f"SELECT balance from login WHERE username = '{username}';")
        balancefetch=mycursor.fetchall()
        balance=balancefetch[0][0]
        self.ids.balancebutton6.text = f'Balance : {str(balance)}'

    def graph(self):
        global reloadtradewingraph, tsname, tshares, tcursvalue
        app = App.get_running_app()

        if reloadtradewingraph and "tradewingraph" in self.ids:
            self.ids.tradewingraph.reload()
        reloadtradewingraph = False

        mycursor.execute(f"SELECT money FROM stocks WHERE sname='{bsname}' AND username='{username}';")
        invested_money = float(mycursor.fetchall()[0][0]) if mycursor.rowcount != 0 else 0.0

        current_value = (tshares or 0) * (tcursvalue or 0.0)
        tprofitmoney = current_value - invested_money
        tprofitpercentage = (tprofitmoney / invested_money * 100) if invested_money > 0 else 0.0

        self.ids.sname.text = str(tsname)
        self.ids.shares.text = "Number of Shares: " + str(tshares)
        self.ids.curmoney.text = "Current Value $: " + f"{tcursvalue:.2f}"
        self.ids.profitmoney.text = "Profit: " + f"{tprofitmoney:.2f}"
        self.ids.profpercentage.text = "Profit Percentage: " + f"{tprofitpercentage:.2f}"

    def buystock(self, shares):
        global portfolioupdate
        app = App.get_running_app()

        try:
            shares = int(shares)
        except ValueError:
            self.ids.buylabel.text = "Error: Enter a valid number of shares."
            return
        if shares <= 0:
            self.ids.buylabel.text = "Error: Invalid number of shares."
            return

        tickername = cursticker
        cur, prev = get_price_cached(tickername)
        if cur <= 0:
            self.ids.buylabel.text = "Error: no price data, try again later."
            return

        spend = shares * cur

        mycursor.execute(f"SELECT balance FROM login WHERE username='{username}';")
        balance = float(mycursor.fetchall()[0][0])
        newbalance = balance - spend
        if newbalance < 0:
            self.ids.buylabel.text = "Not enough funds!"
            return

        mycursor.execute(f"UPDATE login SET balance={newbalance} WHERE username='{username}';")
        my_db.commit()

        mycursor.execute(f"SELECT shares, money FROM stocks WHERE sname='{bsname}' AND username='{username}';")
        row = mycursor.fetchall()
        if row:
            old_shares, old_money = int(row[0][0]), float(row[0][1])
            new_shares = old_shares + shares
            new_money = old_money + spend
            mycursor.execute(
                f"UPDATE stocks SET shares={new_shares}, money={new_money}, ticker='{tickername}' "
                f"WHERE sname='{bsname}' AND username='{username}';"
            )
        else:
            mycursor.execute(
                f"INSERT INTO stocks(username, sname, shares, money, ticker) "
                f"VALUES('{username}', '{bsname}', {shares}, {spend}, '{tickername}');"
            )
        my_db.commit()

        portfolioupdate = True
        set_balance_label(self, f"Balance : {newbalance:.2f}")
        self.ids.buylabel.text = "Shares bought successfully!"
#################################################################################################################################
# SCREEN MANAGER
class WindowManager(ScreenManager):
    pass
#################################################################################################################################
# MAIN CLASS
class MainApp(MDApp):
    def build(self):
        self.title = 'SimplyStocks'
        self.theme_cls.theme_style = theme
        self.theme_cls.primary_palette = palette
        self.theme_cls.primary_hue = hue
        self.theme_cls.background_palette = bgpalette
        self.theme_cls.background_hue = bghue     
        return Builder.load_file('eoty.kv')
MainApp().run()
#################################################################################################################################


