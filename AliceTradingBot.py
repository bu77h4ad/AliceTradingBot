import json
import datetime
import threading
from tkinter import *
import time
from indicators import *
from APIpoloniex import *
import os
from API_KEY import *
import queue

polo = APIpoloniex(api_key, api_secret, 3.0)
q = queue.Queue() # Экземпляр класса, очередь

###Глобальные переменные
_mainThreadStop = False
pair = 'USDT_LTC'
Balances = -1
RSIchartLine = [30,70] #горизонтальные линии на графике
TradeHistory = -1
chart = -1
current = -1

NSMA=3   #SMA период
NPriceChannel =50
zoomX = 5
timeframe=300 #300-5min 900-15min 1800-30min 7200-2hour

root = Tk(); f = Frame(bg="Black"); f.pack(fill="both")
m = Menu(root) #создается объект Меню на главном окне
root.title("Alice Trading Bot")
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

def stepNew():
  """ Автоматичекий подсчет шага в % 
      шаг = депозит / макимальное количество ставок
  """
  sum = orders['lot']
  i=0
  while sum < float (Balances['USDT']):
    sum += sum * orders['coefficient']
    i+=1
  orders['step'] = (float (current['high24hr']) - float(current['low24hr'])) / i
  print ('step =', orders['step']) 

def chartNew():     
  """ Получить график цены """
  global chart
  
  chart_New = polo.returnChartData(currencyPair=pair, period=timeframe, start=int(time.time()-3600*24*2) ) # История Чарта за ...    
  if chart_New != -1:  chart = chart_New  
  #elif chart_New == -1: time.sleep(0.15); chartNew()
  return 

def BalancesNew():  
  """ Получить мой Баланс """
  global Balances
  
  Balances_New = polo.returnBalances() 
  if Balances_New != -1 : Balances = Balances_New
  #elif Balances_New == -1 : time.sleep(0.15); BalancesNew()
  return


def currentTickerNew():     
  """ Получить текущие котировки в паре  """
  global current
  
  currentTicker_New = polo.returnTicker()         
  if currentTicker_New != -1: current = currentTicker_New[pair]  
  #elif currentTicker_New == -1: time.sleep(0.15); currentTickerNew() 
  return
  
def mainThread():
  """  Поток, для обработки очередей с запросами на poloniex.com """
  while not _mainThreadStop :
     try:
       element = q.get_nowait()
     except : # на случай ошибок или пустой очереди sys.exc_info()[0]
      pass
     else :   # если нет ошибок
      if element['event'] == 'BUY': orderBuy = polo.buy(element['pair'], element['rate'] , element['amount']); print (orderBuy)
      if element['event'] == 'SELL': orderSell = polo.sell(element['pair'], element['rate'] , element['amount']); print (orderSell)
      if element['event'] == 'chartNew': chartNew()
      if element['event'] == 'BalancesNew': BalancesNew()
      if element['event'] == 'currentTickerNew': currentTickerNew()
      if element['event'] == 'stepNew': stepNew()
     time.sleep(0.1)

def tick():
  """ Отрисовка окна окна и принятие решений по торговле """
  text1.insert(1.0, time.strftime("[%H:%M:%S] qsize "+str( q.qsize() ) +' ' ))    
  
  q.put({'event':'currentTickerNew'})
  q.put({'event':'BalancesNew'})
  q.put({'event':'chartNew'})

  #на первое включение
  while (Balances == -1 or current == -1 or chart == -1 )  : time.sleep(0.1)

  lowestAsk =  float(current['lowestAsk'])    # могу купить
  highestBid = float(current['highestBid'])   # могу продать
    
  canv.delete("all")
  canvRSI.delete("all")
  #### отрисовка координатной сетки
  for i in range(1,13):
    canv.create_line(0,i*30,650,i*30,width=1,fill="#404040",dash=1 ) # ось Y
    canv.create_line(i*50,0,i*50,300,width=1,fill="#404040",dash=1 ) # ось Х 
    # время по ось Х
    str1 = time.strftime('%H:%M', time.localtime(int(chart[-(i-1)*int(50/zoomX)]['date'] ) )) 
    canv.create_text(650 -i*50,10,text=str1 ,fill="grey")
    
    
  #### определение максимумов и минимумов
  high = Highest(len(chart)- 1 ,chart)
  low = Lowest(len(chart) -1 ,  chart)

  ### ОТРИСОВИ
  #### отрисовка цены на графике
  delta24 = high - low
  for i in range(1,len(chart) -NPriceChannel - 1 ):   
    canv.create_line(600 -i*zoomX, (high - float(chart[-i]['close']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high - float(chart[-i-1]['close']))/ (delta24/300),width=1,fill="#00B000" )
  ### end

  #### Отрисовка средней скользящей      
    canv.create_line(600 -i*zoomX, (high - float(SMA(NSMA,chart,-i)))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high - float(SMA(NSMA,chart,-i-1)))/ (delta24/300),width=1,fill="#FF6A00",dash=1 ) # SMA отрисовка 
  ### end  

  ### Отрисовка Price Channel
    #Нижняя линия
    canv.create_line(600 -i*zoomX, (high - float(PiceChannel(NPriceChannel,chart,-i)['lowPrice']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high - float(PiceChannel(NPriceChannel,chart,-i-1)['lowPrice']))/ (delta24/300),width=1,fill="#0094FF",dash=1 ) 
    #Средняя линия
    canv.create_line(600 -i*zoomX, (high - float(PiceChannel(NPriceChannel,chart,-i)['centerLine']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high - float(PiceChannel(NPriceChannel,chart,-i-1)['centerLine']))/ (delta24/300),width=1,fill="#0094FF",dash=1 ) 
    # Верхняя линия
    canv.create_line(600 -i*zoomX, (high - float(PiceChannel(NPriceChannel,chart,-i)['highPrice']))/ (delta24/300) 
                    ,600 -(i+1)*zoomX,(high - float(PiceChannel(NPriceChannel,chart,-i-1)['highPrice']))/ (delta24/300),width=1,fill="#0094FF",dash=1 )     
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
  RSIcurrent = RSI(14,chart)  
  # ПОКУПКА # RSI < 70 и хватает ли депозита
  if  RSIcurrent < 80 and float(Balances['USDT']) > orders['lot'] :    
    if orders['count'] == 0:     # первый вход
      #orders['bet'][0] = lowestAsk
      orders['count'] +=1          
      q.put({'event': 'stepNew'}) 
      q.put({'event': 'BUY', 'pair' : pair, 'rate' : lowestAsk, 'amount' : orders['lot'] / lowestAsk })             
      #orderBuy = polo.buy(pair, lowestAsk , orders['lot'] / lowestAsk)
      #print(currentDT,'buy','orderBuy', pair, lowestAsk , orders['lot'] / lowestAsk)      
      #for i in range(1,49):
      #  orders['bet'][i] = lowestAsk  - lowestAsk / 100 * i * orders['step'] 
      orders['bet'].clear
      orders['bet'] = [ lowestAsk  - lowestAsk / 100 * x * orders['step'] for x in range(0, round(100 / orders['step']))] 

    else : # Второй вход и последующее и хватает ли депозита
      if lowestAsk < orders['bet'][orders['count']] and float(Balances['USDT']) > (orders['coefficient']**(orders['count']-1)) * orders['lot'] :
        #os.system("Coin.mp3")        
        orders['count'] +=1                         #формула линейной прогрессии  1*orders['coefficient'] ** orders['count']-1 #   bn = b1 *q**n-1
        #orderBuy = polo.buy(pair, lowestAsk , (orders['coefficient']**(orders['count']-1)) * orders['lot'] / lowestAsk)
        q.put({'event': 'BUY', 'pair' : pair, 'rate' : lowestAsk, 'amount' : (orders['coefficient']**(orders['count']-1)) * orders['lot'] / lowestAsk })
        #print(currentDT,'buy', 'orderBuy', pair, lowestAsk , (orders['coefficient']**(orders['count']-1)) * orders['lot'] / lowestAsk )                          
        
  #ПРОДАЖА  
  if (highestBid > orders['bet'][orders['count'] -2 ] and  orders['count'] >= 2) or (orders['count'] == 1  and  highestBid > orders['bet'][0] + orders['bet'][0] / 100 * orders['step']):    
    q.put({'event': 'SELL', 'pair' : pair, 'rate' : highestBid, 'amount' : Balances['LTC']})
    #orderSell = polo.sell(pair, highestBid, polo.returnBalances()['LTC'])
    #print (currentDT, 'SELL','orderSell',pair, highestBid, Balances['LTC']  )    
    orders['count'] = 0    
 
  f = open('Configure.ini','w')
  json.dump(orders, f, sort_keys = True, indent = 3)
  f.close
    
  
  canvRSI.create_text(640,RSIchartLine[0]-7, text= 100-RSIchartLine[0]  ,fill="Slate Gray" )
  canvRSI.create_text(640,RSIchartLine[1]+7, text= 100-RSIchartLine[1]  ,fill="Slate Gray" )
  canvRSI.create_text(50,90,text= "RSI ("+str(14)+"): {:2.4f}".format(RSIcurrent) ,fill="Slate Gray" )
  canv.create_text(60,275,text= "SMA ("+str(NSMA)+"): {:.8f}".format(SMA(NSMA,chart)) ,fill="#FF6A00" )
  canv.create_text(85,290,text="PriceChannel (" + str(NPriceChannel) + "): {:.8f}".format(PiceChannel(NPriceChannel,chart)['centerLine']) ,fill="#0094FF" )
  
  RSIchartLine[0]  

  time_var.set("TF  :\t{:.0f}".format(timeframe/60)+ " min    "+                
               "\nBUY   :\t{:.8f} ".format(lowestAsk) +  
  	           "\nSELL  :\t{:.8f} ".format(highestBid) +
               "\nRefresh: " + time.strftime("%H:%M:%S")  )

  root.after(5000, tick)  # следующий tick через 5 с

mainThread = threading.Thread(target = mainThread, name = 'mainThiredAliceBot' ).start()

root.after(1, tick)
root.mainloop()

_mainThreadStop = True    
