import json
import datetime
import threading
from tkinter import *
from tkinter.messagebox import *
import time
from indicators import *
from APIpoloniex import *
import os
import queue

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Чтение Настроек из файла
try:
  f = open('Configure.ini','r')
  configure = json.load(f)
  f.close
except :
  showerror("Error", "Error in reading 'Configure.ini'\n" + str (sys.exc_info()[1]) )
  quit()

polo = APIpoloniex(configure['api_key'], configure['api_secret'], 1.0)
q = queue.Queue() # Экземпляр класса, очередь

###Глобальные переменные
_mainThreadStop = False
pair = configure['pair']
Balances = -1
RSIchartLine = [30,70] #горизонтальные линии на графике
TradeHistory = -1
chart = -1
current = -1

NSMA = configure['SMAperiod']   #SMA период
NPriceChannel = configure['PriceChannelPeriod']
NRSI= configure['RSIperiod']
zoomX = 5
timeFrame = configure['timeFrame'] #300-5min 900-15min 1800-30min 7200-2hour
#---Сборка Главного Окна
root = Tk(); f = Frame(bg="Black"); f.pack(fill="both")
m = Menu(root) #создается объект Меню на главном окне
root.title("Alice Trading Bot 20171026 beta")
root.geometry('650x550+100+100') # ширина, высота, x=300, y=200

image_path = resource_path("chart.ico")
root.iconbitmap(image_path)
root.resizable(False, False) # размер окна не может быть изменён 
root.config(menu=m) #окно конфигурируется с указанием меню для него

#---MENU-------------------------------- 
def showIndicator(indicator):
  if configure[indicator] == 1 : configure[indicator] = 0
  else: configure[indicator] = 1      

def timeFrameSet(n):
  global timeFrame 
  timeFrame=n                 # Для чарта
  timeFrameVar.set(n)         # для корректной работы галочек
  configure['timeFrame'] = n  # длязаписи в конфиг

fileMenu = Menu(m, tearoff=0) #создается пункт меню с размещением на основном меню (m)
m.add_cascade(label="File", menu=fileMenu) #пункту располагается на основном меню (m)
#fileMenu.add_command(label="Open...", command = '') #формируется список команд пункта меню
fileMenu.add_command(label="Exit", command = root.quit) #формируется список команд пункта меню

#---MENU---VIEW---------------------      
viewMenu = Menu(m, tearoff=0) #создается пункт меню с размещением на основном меню (m)
m.add_cascade(label="View", menu=viewMenu) #пункту располагается на основном меню (m)

SMAshow = IntVar()
PriceChannelShow = IntVar()
RSIshow = IntVar()
timeFrameVar = IntVar()

SMAshow.set(configure['SMAshow'])
PriceChannelShow.set(configure['PriceChannelShow'])
RSIshow.set(configure['RSIshow'])
timeFrameVar.set(configure['timeFrame'])

viewMenu.add_checkbutton(label="5 min", variable=timeFrameVar, onvalue=300, offvalue=0, command=lambda: timeFrameSet(300))
viewMenu.add_checkbutton(label="15 min", variable=timeFrameVar, onvalue=900, offvalue=0, command=lambda: timeFrameSet(900))
viewMenu.add_checkbutton(label="30 min", variable=timeFrameVar, onvalue=1800, offvalue=0, command=lambda: timeFrameSet(1800))
viewMenu.add_checkbutton(label="2 hour", variable=timeFrameVar, onvalue=7200, offvalue=0, command=lambda: timeFrameSet(7200))
viewMenu.add_separator()
viewMenu.add_checkbutton(label="SMA", variable=SMAshow, onvalue=1, offvalue=0, command=lambda:showIndicator('SMAshow'))
viewMenu.add_checkbutton(label="Price Channel", variable=PriceChannelShow, onvalue=1, offvalue=0, command=lambda:showIndicator('PriceChannelShow'))
viewMenu.add_checkbutton(label="RSI",variable = RSIshow, onvalue=1, offvalue=0, command=lambda:showIndicator('RSIshow'))
#---END---MENU----------------------
#time_var = StringVar()
#label = Label(f, textvariable=time_var, justify= LEFT, font="Courier 9", bg="Black", fg="#00B000",borderwidth = 0)
chartX = 650
chartY = 400
canv = Canvas(f, width=chartX, height=chartY, bg="Black", borderwidth=0)

text1=Text(f, font='Courier 9', wrap=WORD, borderwidth=1, bg="Black", fg="#00B000", exportselection=0)
text1.insert(1.0, time.strftime("[%H:%M:%S] Loading ... \n"))
text1.insert(1.0, time.strftime("[%H:%M:%S] Chosen pair : " + configure['pair'] + "\n"))
text1.insert(1.0, time.strftime("[%H:%M:%S] Chosen Time Frame : " + str(configure['timeFrame'] / 60) + " min\n"))

statusBarText = StringVar()
statusBar = Label(f, textvariable=statusBarText ,font="Courier 9", bg="Black", fg="#00B000", bd=1, relief=SUNKEN, anchor=W)
statusBar.pack(side = "bottom",fill=X)  

canv.pack()

#label.pack(side="left", anchor=NW, padx=0)
text1.pack(side="top", fill=X)

#---MENU---About
def about():
  """ Окно ABOUT """
  winAbout = Toplevel()
  winAbout.title("About")
  x = (winAbout.winfo_screenwidth() /2 - winAbout.winfo_reqwidth())
  y = (winAbout.winfo_screenheight()/2 - winAbout.winfo_reqheight()) 
  winAbout.wm_geometry('470x170+%d+%d'% (x, y)) # ширина=500, высота=400, x=300, y=200
  winAbout.iconbitmap(image_path)
  winAbout.resizable(False, False) # размер окна не может быть изменён 
  winAbout["bg"] = "Black"
    
  winAbout.txt=Text(winAbout, height=9, width=7, borderwidth =0, font='Arial 9',bg = "Black" , fg="#00B000",wrap=WORD)
  txt = "DONATIONS: \n\
  BTC fb0a34933ca0781f5e9917a52ea86d72cbb1c05b4ccfff56f9c78bdce5f8a573\n\
  LTC LRsm54XYJxG7NJCuAntK98odJoXhwp1GBK\n\
  ETH 0x8750793385349e2edd63e87d5c523b3b2c972b82\n\
  ZEC t1TW9tC321fZyDQRX4spzpxar1hRBcBHU6S\n\n\
CONTACT:\n\
  Telegram: bu77h4ad\n\
  VK: vk.com/alicetradingbot"
  winAbout.txt.insert('end', txt)
  winAbout.txt.configure(state=DISABLED)
  winAbout.txt.pack(fill="both")

  winAbout.but = Button(winAbout,text = 'Ok',activebackground = "#00B000" , activeforeground = "Black", relief="groove",borderwidth=2, height=1,width=5,font='Arial 9',bg = "Black" , fg="#00B000",command = winAbout.destroy )    
  winAbout.but.pack(fill="none")

  winAbout.mainloop()
m.add_command(label="About", command = about) #формируется список команд пункта меню

def stepNew():
  """ Автоматичекий подсчет шага в % 
      шаг = изменение цены за сутки / макимальное количество ставок
  """
  sum = configure['lot']
  i=0  
  while sum < float (Balances[str(configure['pair']).split('_')[0]]):
    sum += sum * configure['coefficient']
    i+=1
  stepAuto = ((float (current['high24hr']) - float(current['low24hr'])) / i) / (float (current['lowestAsk'] ) / 100 )
  if configure['stepMin'] < stepAuto : configure['stepNow'] = stepAuto 
  else : configure['stepNow'] = configure['stepMin']
  text1.insert(1.0, time.strftime("[%H:%M:%S] " + 'step = ' + str(configure['stepNow']) + ' max. count bet = ' +  str(i) +" \n"))  

def chartNew():     
  """ Получить график цены """
  global chart
  
  numberMustCandel = chartX//50*(50/zoomX) + max([NSMA,NPriceChannel,NRSI]) 
  numberCandelInDay = 86400 / timeFrame
  mustDay = numberMustCandel // numberCandelInDay + 1
  
  chart_New = polo.returnChartData(currencyPair=pair, period=timeFrame, start=int(time.time()-3600*24*mustDay) ) # История Чарта за ...    
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
      if element['event'] == 'BUY' : 
        orderBuy  = polo.buy (element['pair'], element['rate'], element['amount'], timeOutSec = 3)
        text1.insert(1.0, time.strftime("[%H:%M:%S] BUY price: " + str(element['rate']) +  " amount: "+ str(element['amount'])+ " | Return Poloniex: "+ str('orderBuy') + " \n"))
      if element['event'] == 'SELL': 
        orderSell = polo.sell(element['pair'], element['rate'], element['amount'], timeOutSec = 3)         
        text1.insert(1.0, time.strftime("[%H:%M:%S] SELL price: " + str(element['rate']) +  " amount: "+ str(element['amount'])+ " | Return Poloniex: "+ str('orderSell') + " \n"))
      if element['event'] == 'chartNew': chartNew()
      if element['event'] == 'BalancesNew': BalancesNew()
      if element['event'] == 'currentTickerNew': currentTickerNew()
      if element['event'] == 'stepNew': stepNew()
     time.sleep(0.1) 

def tick():
  """ Отрисовка окна окна и принятие решений по торговле """  
  
  q.put({'event':'currentTickerNew'})
  q.put({'event':'BalancesNew'})
  q.put({'event':'chartNew'})

  #на первое включение
  while (Balances == -1 or current == -1 or chart == -1 ):
    time.sleep(1.5); 
    chartNew(); 
    BalancesNew(); 
    currentTickerNew(); 
    if (Balances != -1 or current != -1 or chart != -1 ):  text1.insert(1.0, time.strftime("[%H:%M:%S] loading is complete\n"));
  
  lowestAsk =  float(current['lowestAsk'])    # могу купить
  highestBid = float(current['highestBid'])   # могу продать
    
  canv.delete("all")  
  #### отрисовка координатной сетки
  if configure['RSIshow'] == True: RSIY=100; winX = -2;
  else: RSIY=0; winX=1;
  for i in range(1,chartY // 30 + winX):
    canv.create_line(0,i*30,chartX,i*30,width=1,fill="#404040",dash=1 ) # ось X  
  for i in range(1,chartX // 50):      
    canv.create_line(i*50,0,i*50,chartY-RSIY,width=1,fill="#404040",dash=1 ) # ось Y 
    # время по ось Х
    str1 = time.strftime('%H:%M', time.localtime(int(chart[-(i-1)*int(50/zoomX)]['date'] ) )) 
    canv.create_text(650 -i*50,10,text=str1 ,fill="grey")
    
    
  #### определение максимумов и минимумов
  high = Highest(len(chart)- 1 ,chart)
  low = Lowest(len(chart) -1 ,  chart)

  ### ОТРИСОВИ
  #### отрисовка цены на графике
  delta24 = high - low

  for i in range(1,len(chart) ):   #-NPriceChannel - 1
    canv.create_line(600 -i*zoomX, (high - float(chart[-i]['close']))/ (delta24/(chartY-RSIY)) 
                    ,600 -(i+1)*zoomX,(high - float(chart[-i-1]['close']))/ (delta24/(chartY-RSIY)),width=1,fill="#00B000" )
  ### end

  #### Отрисовка SMA средней скользящей      
    if configure['SMAshow'] == True and i < len(chart) - NSMA:
      canv.create_line(600 -i*zoomX, (high - float(SMA(NSMA,chart,-i)))/ (delta24/(chartY-RSIY)) 
                    ,600 -(i+1)*zoomX,(high - float(SMA(NSMA,chart,-i-1)))/ (delta24/(chartY-RSIY)),width=1,fill="#FF6A00",dash=1 ) # SMA отрисовка 
  ### end  

  ### Отрисовка Price Channel
    if configure['PriceChannelShow'] == True and i < len(chart) - NPriceChannel :
    #Нижняя линия
      canv.create_line(600 -i*zoomX, (high - float(PiceChannel(NPriceChannel,chart,-i)['lowPrice']))/ (delta24/(chartY-RSIY)) 
                    ,600 -(i+1)*zoomX,(high - float(PiceChannel(NPriceChannel,chart,-i-1)['lowPrice']))/ (delta24/(chartY-RSIY)),width=1,fill="#0094FF",dash=1 ) 
    #Средняя линия
      canv.create_line(600 -i*zoomX, (high - float(PiceChannel(NPriceChannel,chart,-i)['centerLine']))/ (delta24/(chartY-RSIY)) 
                    ,600 -(i+1)*zoomX,(high - float(PiceChannel(NPriceChannel,chart,-i-1)['centerLine']))/ (delta24/(chartY-RSIY)),width=1,fill="#0094FF",dash=1 ) 
    # Верхняя линия
      canv.create_line(600 -i*zoomX, (high - float(PiceChannel(NPriceChannel,chart,-i)['highPrice']))/ (delta24/(chartY-RSIY)) 
                    ,600 -(i+1)*zoomX,(high - float(PiceChannel(NPriceChannel,chart,-i-1)['highPrice']))/ (delta24/(chartY-RSIY)),width=1,fill="#0094FF",dash=1 )     
  ### Отрисовка RSI 
    if configure['RSIshow'] == True  and i < len(chart) - NRSI :       
      canv.create_line(600 -i*zoomX, chartY-RSI(NRSI,chart,-i) ,
                        600 -(i+1)*zoomX, chartY-RSI(NRSI,chart,-i-1),width=1,fill="Slate Gray" )
      canv.create_line(0,chartY-RSIchartLine[0], 650,chartY-RSIchartLine[0], width=1, fill="Slate Gray", dash=1 )
      canv.create_line(0,chartY-RSIchartLine[1], 650,chartY-RSIchartLine[1], width=1, fill="Slate Gray", dash=1 )       
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
  RSIcurrent = RSI(NRSI,chart)  
  # ПОКУПКА # RSI < 70 и хватает ли депозита
  if  RSIcurrent < 30 and float(Balances['USDT']) > configure['lot'] :    
    if configure['count'] == 0:     # первый вход
      #configure['bet'][0] = lowestAsk
      configure['count'] +=1          
      q.put({'event': 'stepNew'}) 
      q.put({'event': 'BUY', 'pair' : pair, 'rate' : lowestAsk, 'amount' : configure['lot'] / lowestAsk })             
      #orderBuy = polo.buy(pair, lowestAsk , configure['lot'] / lowestAsk)
      #print(currentDT,'buy','orderBuy', pair, lowestAsk , configure['lot'] / lowestAsk)      
      #for i in range(1,49):
      #  configure['bet'][i] = lowestAsk  - lowestAsk / 100 * i * configure['step'] 
      configure['bet'].clear
      configure['bet'] = [ lowestAsk  - lowestAsk / 100 * x * configure['stepNow'] for x in range(0, round(100 / configure['stepNow']))] 

    else : # Второй вход и последующее и хватает ли депозита
      if lowestAsk < configure['bet'][configure['count']] and float(Balances['USDT']) > (configure['coefficient']**(configure['count']-1)) * configure['lot'] :
        #os.system("Coin.mp3")        
        configure['count'] +=1                         #формула линейной прогрессии  1*configure['coefficient'] ** configure['count']-1 #   bn = b1 *q**n-1
        #orderBuy = polo.buy(pair, lowestAsk , (configure['coefficient']**(configure['count']-1)) * configure['lot'] / lowestAsk)
        q.put({'event': 'BUY', 'pair' : pair, 'rate' : lowestAsk, 'amount' : (configure['coefficient']**(configure['count']-1)) * configure['lot'] / lowestAsk })
        #print(currentDT,'buy', 'orderBuy', pair, lowestAsk , (configure['coefficient']**(configure['count']-1)) * configure['lot'] / lowestAsk )                          
        
  #ПРОДАЖА  
  if (highestBid > configure['bet'][configure['count'] -2 ] +  (configure['bet'][0] / 1000 * configure['count']) and  configure['count'] >= 2) or (configure['count'] == 1  and  highestBid > configure['bet'][0] + configure['bet'][0] / 100 * configure['stepNow']):    
    q.put({'event': 'SELL', 'pair' : pair, 'rate' : highestBid, 'amount' : Balances['LTC']})
    #orderSell = polo.sell(pair, highestBid, polo.returnBalances()['LTC'])
    #print (currentDT, 'SELL','orderSell',pair, highestBid, Balances['LTC']  )    
    configure['count'] = 0    
 
  f = open('Configure.ini','w')
  json.dump(configure, f, sort_keys = True, indent = 3)
  f.close
  
  if configure['RSIshow'] == True:       
    canv.create_text(640, chartY-100+RSIchartLine[0]-7, text=100-RSIchartLine[0]  ,fill="Slate Gray" )
    canv.create_text(640, chartY-100+RSIchartLine[1]+7, text=100-RSIchartLine[1]  ,fill="Slate Gray" )
    canv.create_text(50, chartY-10, text="RSI ("+str(NRSI)+"): {:2.4f}".format(RSIcurrent) ,fill="Slate Gray" )  
    canv.create_line(0,chartY-RSIY, 650, chartY-RSIY, width=2, fill="White" )       
  if configure['SMAshow'] == True: canv.create_text(60,chartY-RSIY-25,text= "SMA ("+str(NSMA)+"): {:.8f}".format(SMA(NSMA,chart)) ,fill="#FF6A00" )
  if configure['PriceChannelShow'] == True: canv.create_text(85,chartY-RSIY-10,text="PriceChannel (" + str(NPriceChannel) + "): {:.8f}".format(PiceChannel(NPriceChannel,chart)['centerLine']) ,fill="#0094FF" )
  
  RSIchartLine[0]  
  
  statusBarText.set("TF : {:.0f}".format(timeFrame/60)+ " min" + " | Qeueu : {:.0f}".format(q.qsize()) + " | "+ "BUY  : {:.8f}".format(lowestAsk) + " | " + "SELL : {:.8f}".format(highestBid) + " | " +  "Refresh: " + time.strftime("%H:%M:%S")) 
  root.after(5000, tick)  # следующий tick через 5 с

mainThread = threading.Thread(target=mainThread, name='mainThiredAliceBot').start()

root.after(1, tick)
root.mainloop()

_mainThreadStop = True    
