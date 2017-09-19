import json
import datetime
import threading
from tkinter import *
import time
from indicators import *
from APIpoloniex import *
import os

api_key = 'BL2HO7TZ-L4UN5JLU-IKL7E7O5-51RZI53K'
api_secret = 'ef371b33fd0aa148439d97c310efc93bc717c7605009ba007a45650cf03617da97dfd06942fbfdd586a3f1c3ce9b54aeed9eb48cecaac8035821622fb8edaf7c'
#polo = Poloniex(api_key, api_secret,3000)
polo = APIpoloniex(api_key, api_secret,3.0)

###Глобальные переменные
pair = 'USDT_LTC'
USDT = -1
RSIchartLine = [30,70] #горизонтальные линии на графике
TradeHistory = -1
chart = -1
current = -1

NSMA=3   #SMA период
NPriceChannel =50
zoomX = 5
timeframe=300 #300-5min 900-15min 1800-30min 7200-2hour
GMT= 0 * 3600 # Часовой пояс относительно гринвича где 3 - изменить на свой

root = Tk(); f = Frame(bg="Black"); f.pack(fill="both")
m = Menu(root) #создается объект Меню на главном окне
root.title("Trading Robot v1")
root.geometry('650x470+100+100') # ширина=500, высота=400, x=300, y=200
root.iconbitmap(default='chart.ico')
root.resizable(False, False) # размер окна не может быть изменён 
root.config(menu=m) #окно конфигурируется с указанием меню для него
 
fm = Menu(m, tearoff=0) #создается пункт меню с размещением на основном меню (m)
m.add_cascade(label="File",menu=fm) #пункту располагается на основном меню (m)
fm.add_command(label="Open...", command = '') #формируется список команд пункта меню
fm.add_command(label="Exit", command = root.quit) #формируется список команд пункта меню

time_var = StringVar()
label = Label(f, textvariable=time_var, font="Courier 9", bg="Black", fg="#00B000",borderwidth = 0)
canv = Canvas(f, width = 650, height = 300, bg = "Black",borderwidth = 0)
canvRSI = Canvas(f, width = 650, height = 100, bg = "Black",borderwidth = 0)
text1=Text(f,font='Courier 9',wrap=WORD,borderwidth = 1,bg="Black", fg="#00B000",exportselection=0)
text1.insert(1.0, time.strftime(" [%H:%M:%S] Start\n"))

canv.pack()
canvRSI.pack()
label.pack(side="left")
text1.pack(side="top",fill="both")

f = open('Configure.ini','r')
orders = json.load(f)
f.close

def TradeHistoryNew():
  global TradeHistory
  time.sleep(0.2)
  while chart == -1 :
    TradeHistory_New = polo.returnTradeHistory(currencyPair=pair, start=int(time.time())  -3600 / 4 , end=time.time())  # История ордеров за последнии N мин
    if TradeHistory_New != -1:  TradeHistory = TradeHistory_New
  else:
    TradeHistory_New = polo.returnTradeHistory(currencyPair=pair, start=int(time.time())  -3600 / 4 , end=time.time())  # История ордеров за последнии N мин
    if TradeHistory_New != -1 :  TradeHistory = TradeHistory_New
  return 

# Поллучаем значения графика
def chartNew():  
  time.sleep(0.4)
  global chart
  while chart == -1 :
    chart_New = polo.returnChartData(currencyPair=pair, period=timeframe, start=int(time.time()-3600*24*2) ) # История Чарта за ...
    if chart_New != -1:  chart = chart_New  
  else :
    chart_New = polo.returnChartData(currencyPair=pair, period=timeframe, start=int(time.time()-3600*24*2) ) # История Чарта за ...
    if chart_New != -1   :  chart = chart_New  
  return 

# получить текущее значения в паре  
def currentTicker():
  global current
  while  current == -1:
    currentNew = polo.returnTicker()         
    if currentNew != -1: current = currentNew[pair]  
  else:
    currentNew = polo.returnTicker()     
    if currentNew != -1  : current = currentNew[pair]  
  return

#Получить Баланс USDT
def BalancesNew():
  time.sleep(0.6)
  global USDT
  while  USDT == -1:    
    USDTnew = polo.returnBalances() 
    if USDTnew != -1 : USDT = float(USDTnew['USDT'])
  else :
    USDTnew = polo.returnBalances()     
    if USDTnew != -1 : USDT = float(USDTnew['USDT'])
  return


def tick():
  """Обновление данных на бирже"""
  
  threading.Thread(target = currentTicker).start()   
  threading.Thread(target = TradeHistoryNew).start()     
  threading.Thread(target = chartNew).start()  
  threading.Thread(target = BalancesNew).start() 
  
  #на первое включение
  while (USDT == -1 or current == -1 or chart == -1 or TradeHistory == -1): time.sleep(0.1)

  lowestAsk =  float(current['lowestAsk'])    # могу купить
  highestBid = float(current['highestBid'])   # могу продать
    
  canv.delete("all")
  canvRSI.delete("all")
  #### отрисовка координатной сетки
  for i in range(1,13):
    canv.create_line(0,i*30,650,i*30,width=1,fill="#404040",dash=1 ) # ось Y
    canv.create_line(i*50,0,i*50,300,width=1,fill="#404040",dash=1 ) # ось Х 
    # время по ось Х
    str1 = time.strftime('%H:%M', time.localtime(int(chart[-(i-1)*int(50/zoomX)]['date'] ) +GMT)) 
    canv.create_text(650 -i*50,10,text=str1 ,fill="grey")
    
    
  #### определение максимумов и минимумов
  high24hr = Highest(len(chart)- 1 ,chart)
  low24hr = Lowest(len(chart) -1 ,  chart)

  ### ОТРИСОВИ
  #### отрисовка цены на графике
  delta24 = high24hr - low24hr
  for i in range(1,len(chart) -NPriceChannel - 1 ):   
    canv.create_line(600 -i*zoomX, (high24hr - float(chart[-i]['close']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high24hr - float(chart[-i-1]['close']))/ (delta24/300),width=1,fill="#00B000" )
  ### end

  #### Отрисовка средней скользящей      
    canv.create_line(600 -i*zoomX, (high24hr - float(SMA(NSMA,chart,-i)))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high24hr - float(SMA(NSMA,chart,-i-1)))/ (delta24/300),width=1,fill="#FF6A00",dash=1 ) # SMA отрисовка 
  ### end  

  ### Отрисовка Price Channel
    #Нижняя линия
    canv.create_line(600 -i*zoomX, (high24hr - float(PiceChannel(NPriceChannel,chart,-i)['lowPrice']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high24hr - float(PiceChannel(NPriceChannel,chart,-i-1)['lowPrice']))/ (delta24/300),width=1,fill="#0094FF",dash=1 ) 
    #Средняя линия
    canv.create_line(600 -i*zoomX, (high24hr - float(PiceChannel(NPriceChannel,chart,-i)['centerLine']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high24hr - float(PiceChannel(NPriceChannel,chart,-i-1)['centerLine']))/ (delta24/300),width=1,fill="#0094FF",dash=1 ) 
    # Верхняя линия
    canv.create_line(600 -i*zoomX, (high24hr - float(PiceChannel(NPriceChannel,chart,-i)['highPrice']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high24hr - float(PiceChannel(NPriceChannel,chart,-i-1)['highPrice']))/ (delta24/300),width=1,fill="#0094FF",dash=1 )     
    # RSI  
    canvRSI.create_line(600 -i*zoomX, 100 - RSI(14,chart,-i) ,
                        600 -(i+1)*zoomX,100 - RSI(14,chart,-i-1),width=1,fill="Slate Gray" )
    canvRSI.create_line(0,RSIchartLine[0],650,RSIchartLine[0],width=1,fill="Slate Gray",dash=1 )
    canvRSI.create_line(0,RSIchartLine[1],650,RSIchartLine[1],width=1,fill="Slate Gray",dash=1 )    
  ### end 
  currentDT = datetime.datetime.now()    
  ### ПОКУПКА И ПРОДАЖА  
  #print ('currentDT.minute -',currentDT.minute == 29 or currentDT.minute == 59,'  len(TradeHistory) -', len(TradeHistory) == 0,len(TradeHistory), ' currentNew ',currentNew != -1)
  """
  if (currentDT.minute == 29 or currentDT.minute == 59) and (len(TradeHistory) == 0) and (currentNew != -1) :
    print ('=========> len(TradeHistory) - ', len(TradeHistory), ' currentNew ',currentNew != -1)
    if PiceChannel(NPriceChannel,chart)['centerLine'] > SMA(NSMA, chart) and PiceChannel(NPriceChannel,chart,-2)['centerLine'] <= SMA(NSMA, chart,-2) :
      ordersell = polo.sell(pair, highestBid , 103)
      text1.insert(1.0, time.strftime(" [%H:%M:%S] "+str(ordersell)+"\n"))
    if PiceChannel(NPriceChannel,chart)['centerLine'] < SMA(NSMA, chart) and PiceChannel(NPriceChannel,chart,-2)['centerLine'] >= SMA(NSMA, chart, -2) :     
      orderbuy = polo.buy(pair, lowestAsk , 103)
      text1.insert(1.0, time.strftime(" [%H:%M:%S] "+str(orderbuy)+"\n"))
  """
  #res= {"bet":[]}
  #res["bet"] = [ lowestAsk  - lowestAsk / 100 * x * orders['step'] for x in range(1, 100 // orders['step'])]
  #print (res)
  #res = orders
  #res['bet'].clear()  
  RSIcurrent = RSI(14,chart)  
  # ПОКУПКА # RSI < 70 и хватает ли депозита
  if  RSIcurrent < 80 and float(USDT) > orders['lot'] :    
    if orders['count'] == 0:     # первый вход
      orders['bet'][0] = lowestAsk
      orders['count'] +=1           
      orderBuy = polo.buy(pair, lowestAsk , orders['lot'] / lowestAsk)
      print(currentDT,'buy', orderBuy)      
      for i in range(1,49):
        orders['bet'][i] = lowestAsk  - lowestAsk / 100 * i * orders['step'] 
      #del orders['bet']
      #orders['bet'] = [ lowestAsk  - lowestAsk / 100 * x * orders['step'] for x in range(1, 100 // orders['step'])] 

    else : # Второй вход и последующее и хватает ли депозита
      if lowestAsk < orders['bet'][orders['count']] and float(USDT) > (orders['coefficient']**(orders['count']-1)) * orders['lot'] :
        #os.system("Coin.mp3")        
        orders['count'] +=1                         #формула линейной прогрессии  1*orders['coefficient'] ** orders['count']-1 #   bn = b1 *q**n-1
        orderBuy = polo.buy(pair, lowestAsk , (orders['coefficient']**(orders['count']-1)) * orders['lot'] / lowestAsk)
        print(currentDT,'buy', orderBuy)                          
        
  #ПРОДАЖА  
  if (highestBid > orders['bet'][orders['count'] -2 ] and  orders['count'] >= 2) or (orders['count'] == 1  and  highestBid > orders['bet'][0] + orders['bet'][0] / 100 * orders['step']):    
    orderSell = polo.sell(pair, highestBid, polo.returnBalances()['LTC'])
    print (currentDT, 'SELL', orderSell )    
    orders['count'] =0
  
 
  f = open('Configure.ini','w')
  json.dump(orders, f, sort_keys = True, indent = 3)
  f.close
    
  #text1.insert(1.0, time.strftime(" [%H:%M:%S] open "+str(chart[-1]['open']) + " close " + str(chart[-1]['close']) +"\n" ))    
  canvRSI.create_text(640,RSIchartLine[0]-7, text= 100-RSIchartLine[0]  ,fill="Slate Gray" )
  canvRSI.create_text(640,RSIchartLine[1]+7, text= 100-RSIchartLine[1]  ,fill="Slate Gray" )
  canvRSI.create_text(50,90,text= "RSI ("+str(14)+"): {:2.4f}".format(RSIcurrent) ,fill="Slate Gray" )
  canv.create_text(60,275,text= "SMA ("+str(NSMA)+"): {:.8f}".format(SMA(NSMA,chart)) ,fill="#FF6A00" )
  canv.create_text(85,290,text="PriceChannel (" + str(NPriceChannel) + "): {:.8f}".format(PiceChannel(NPriceChannel,chart)['centerLine']) ,fill="#0094FF" )
  
  RSIchartLine[0]  
 # print('открытых ордеров :',len(OpenOrders) )
 # print (time.localtime(time.time() - 3600*5))


  time_var.set("TF  :\t{:.0f}".format(timeframe/60)+ " min    "+                
               "\nBUY   :\t{:.8f} ".format(lowestAsk) +  
  	           "\nSELL  :\t{:.8f} ".format(highestBid) +
               "\nRefresh: " + time.strftime("%H:%M:%S")  )
  label.after(2000, tick)  # следующий tick через 5 с

label.after(1000, tick)
root.mainloop()
    
