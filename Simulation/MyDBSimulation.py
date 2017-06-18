'''
Created on 2016 11 13

@author: Yali
'''
from Predict import MyPredictDB
import datetime
import random
import math
import numpy as np
from datetime import timedelta
from abc import abstractmethod
import collections
#Get a date, 
#Get all data, 
#Get Predict, 
#Set situation, 
#Get Result

class SimulationBaseClass:
    
    def __init__(self,InitMoney,StartDate,EndDate):
        '''
        self.CurrentList is a dictionary. 
        The key is the stock symbol
        The value is an array. Each item in the array is [NumberHold,BuyPrice,the buy Date]
        @param StartDate: string format 2017-01-01
        @param EndDate: string format 2017-01-02
        '''
        self.CurrentList = {}
        self.RemainMoney = InitMoney
        self.InitMoney = InitMoney
        self.StartDate = StartDate
        self.EndDate = EndDate
        

        # get all data
        
    def BuyAStock(self,theDate,Symbol,BuyPrice):
        '''
        Buy a stock on some day
        Calculate the money left
        Update status
        @param theDate:string format 2017-01-01 
        '''
        NumberHold = 0
        if len(self.CurrentList)==0:
            RemainMoney = self.RemainMoney/3-10
        elif len(self.CurrentList)==1 and self.RemainMoney>20:
            RemainMoney = self.RemainMoney/2-10
        elif len(self.CurrentList)==2 and self.RemainMoney>10:
            RemainMoney = self.RemainMoney-10
        elif len(self.CurrentList)==3:
            #print ("we already have 3 stocks in hand.")
            return
        else:
            print ("there is not enough money. "+str(self.RemainMoney))
            return 
        
        if BuyPrice>0.0:
            NumberHold = math.floor(RemainMoney/BuyPrice)
            self.RemainMoney -= NumberHold*BuyPrice
            if Symbol in self.CurrentList:
                current = self.CurrentList[Symbol]
                current.append([NumberHold,BuyPrice,theDate])
                self.CurrentList[Symbol] = current
            else:
                self.CurrentList[Symbol] = [[NumberHold,BuyPrice,theDate]]
                
            print('buy '+str(NumberHold)+' '+Symbol +' with price '+str(BuyPrice)+' at '+theDate)
            print("we remain cash "+str(self.RemainMoney))
        
        '''AllData = {}
        adate = datetime.datetime.strptime(theDate,'%Y-%m-%d')
        while True:
            AllData = MyPredictDB.GetAllData(theDate)
            if len(AllData.items())>0:
                break
            else:
                adate += timedelta(days=1)
                theDate = datetime.datetime.strftime(adate,'%Y-%m-%d')
        IsUpList = []
        for anitem in AllData:
            data = AllData[anitem]
            isup = MyPredictDB.IsUpTrend(data)
            if isup:
                IsUpList.append(anitem)
        if len(IsUpList)==0:
            return [0,0,0,initMoney]
        #buy 
        NumberHold = 0
        RemainMoney = initMoney-10
        
        theindex = random.randint(0,len(IsUpList)-1)
        print IsUpList
        print theindex
        TheStock = IsUpList[theindex]
        BuyPrice = AllData[TheStock][2][0]
        if BuyPrice>0.0:
            NumberHold = math.floor(RemainMoney/BuyPrice)
            RemainMoney -= NumberHold*BuyPrice
            return [TheStock,NumberHold,BuyPrice,RemainMoney,adate]
        else:
            print 'error.'
            print TheStock
            return [0,0,0,0,None]
            '''
    def SellAStock(self,Symbol,SellPrice,SellDate):
        '''
        @param SellDate: string format 2017-01-01 
        '''
        if Symbol in self.CurrentList:
            holdings = self.CurrentList[Symbol]
            SellMoney = 0
            for anitem in holdings:
                SellMoney += anitem[0]*SellPrice
                print('Sell '+str(anitem[0])+' '+Symbol +' with price '+str(SellPrice)+' at '+SellDate)
            self.RemainMoney +=SellMoney-10
        else:
            print("We are not holding "+Symbol)
        print("we remain cash "+str(self.RemainMoney))
    
    def RunAStrategy(self):
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d')
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d')
        currentDate = theStartDate
        while currentDate<=theEndDate:
            if len(self.CurrentList)<3:
                BuyRes = self.GetBuyList(currentDate.strftime('%Y-%m-%d'))
                for anitem in BuyRes:
                    self.BuyAStock(currentDate.strftime('%Y-%m-%d'), anitem[0], anitem[1])
                    if len(self.CurrentList)==3:
                        break
            removed = []
            for i in range(len(self.CurrentList)):
                asymbol = self.CurrentList.keys()[i]
                [SellOrNot,SellPrice] = self.SellNow(asymbol,currentDate.strftime('%Y-%m-%d'))
                if SellOrNot:
                    self.SellAStock(asymbol, SellPrice, currentDate.strftime('%Y-%m-%d'))
                    removed.append(asymbol)
            for anitem in removed:
                del self.CurrentList[anitem]
            currentDate+=timedelta(days=1)
            
        thecurrentdata = MyPredictDB.GetAllData(self.EndDate, 1)
        totalmoney = 0
        for anitem in self.CurrentList:
            thedata = self.CurrentList[anitem]
            totalnum = 0
            for adata in thedata:
                totalnum += adata[0]
            print('We are holding '+str(totalnum) +' '+anitem)
            print('The current price is '+str(thecurrentdata[anitem][2][0]))
            themoney = totalnum*thecurrentdata[anitem][2][0]
            totalmoney += themoney
        print('we have remain cash:'+str(self.RemainMoney))
        print('we have total money:'+str(self.RemainMoney+totalmoney))
        print('Percent is '+str((self.RemainMoney+totalmoney)/self.InitMoney))
    
    @abstractmethod
    def GetBuyList(self,aDate):
        '''
        Get the list of good stocks today.
        Return value: a list of stocks. Each item in the list [Symbol,BuyPrice]
        '''
        return []
    
    @abstractmethod
    def SellNow(self,Symbol,aDate):
        '''
        Whether we shold sell the given stock on this given day.
        If yes, return [True,SellPrice]
        If not, return [False,0.0]
        '''
        return[False,0.0]

class BuyAllTimeHigh(SimulationBaseClass):
    def __init__(self,InitMoney,StartDate,EndDate,AllTimeHighPeriod=200,DownPercent = 0.5):
        '''
        @param AllTimeHighPeriod: one year all time high or one month all time high? the unit is days
        @param DownPercent: must >0 and <1 
        '''
        SimulationBaseClass.__init__(self, InitMoney, StartDate, EndDate)
        self.DownPercent = DownPercent
        # Get all data
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d').date()
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d').date()
        totalPeriod = (theEndDate-theStartDate).days
        print("Getting all data")
        self.AllData = MyPredictDB.GetAllData(EndDate,AllTimeHighPeriod+totalPeriod)
        print("Calculating all time highs")
        self.AllTimeHigh = {}
        RemoveData = []
        for anitem in self.AllData:
            # get all time high
            alltimehigh = {}
            TheStockData = self.AllData[anitem]
            allClosePrices = []
            allDates = []
            # the index of start date in the array
            # the front, the near date. the end, the previous date
            startIndex = -1
            i = 0
            allClosePrices = TheStockData[2]
            allDates = TheStockData[0]
            for i in range(len(allDates)):
                if theStartDate==allDates[i]:
                    startIndex = i
                    break
            if startIndex==-1:
                #print("the start date is not in the database")
                RemoveData.append(anitem)
                continue
            
            try:
                for i in range(startIndex+1):
                    lastIndex = min(i+1+AllTimeHighPeriod,len(allClosePrices))
                    #print lastIndex
                    #print i
                    #print allClosePrices
                    if allClosePrices[i]>max(allClosePrices[i+1:lastIndex]):
                        alltimehigh[allDates[i].strftime('%Y-%m-%d')]=True
                    else:
                        alltimehigh[allDates[i].strftime('%Y-%m-%d')]=False
                od = collections.OrderedDict(sorted(alltimehigh.items(),reverse=True))
                self.AllTimeHigh[anitem] = od
            except:
                if anitem in self.AllTimeHigh:
                    del self.AllTimeHigh[anitem]
                RemoveData.append(anitem)
        for anitem in RemoveData:
            del self.AllData[anitem]
            
            
    def GetBuyList(self,aDate):
        '''
        @param aDate: string format
        @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
        Get the stocks achieved all time high yesterday.
        Then buy at the open price today.
        The stock is ordered by the volume*close price yesterday.
        '''
        StockList = []
        for anitem in self.AllTimeHigh:
            ThisSymbolData = self.AllTimeHigh[anitem]
            if aDate in ThisSymbolData and ThisSymbolData[aDate]==True:
                StockList.append(anitem)
        #sort the stocks
        TheCompany = []
        for asymbol in StockList:
            LastClosePrice = self.AllData[asymbol][2][-1]
            LastVolume = self.AllData[asymbol][-1][-1]
            # we use a simple method to calculate the company size
            #close price * volume
            TheNumber = LastClosePrice*LastVolume
            TheCompany.append(TheNumber)
        Index = sorted(range(len(TheCompany)), key=lambda k: TheCompany[k],reverse=True)
        SortedList = [None]*len(StockList)
        for i in range(len(StockList)):
            SortedList[Index[i]] = StockList[i]
        OpenPrices = []
        theDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        for asymbol in SortedList:
            TheDatas = self.AllData[asymbol]
            i = 0
            for adate in TheDatas[0]:
                if adate==theDate:
                    OpenPrices.append(TheDatas[1][i])
                    break
                i+=1
        ReturnList =[]
        #print SortedList
        #print OpenPrices
        for i in range(len(SortedList)):
            ReturnList.append([SortedList[i],OpenPrices[i]])
        return ReturnList
    
    def SellNow(self,Symbol,aDate): 
        '''
        If the price is higher than 3% of the buying price, sell it
        @param aDate: string format 2017-01-01 
        @return: If sell, return [True,SellPrice]. Else return [False,0.0]
        '''           
        if not Symbol in self.CurrentList:
            return [False,0.0]
        
        BuyInfo = self.CurrentList[Symbol]
        # if it is the same day of buying, return false
        LastBuyDay = BuyInfo[-1][2]
        if aDate==LastBuyDay:
            return [False,0.0]
        
        aDateDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        TheDatas = self.AllData[Symbol]
        # weekend, public holiday etc.
        if not aDateDate in TheDatas[0]:
            return [False,0.0]
        maxBuyPrice = 0.0
        for anitem in BuyInfo:
            #anitem=[number hold,buy price,buy date]
            if anitem[1]>maxBuyPrice:
                maxBuyPrice = anitem[1]
        # If the price is lower than 5% of the buy price or the highest price, sell it.
        maxPriceSinceBuy = maxBuyPrice
        LastBuyDayDate= datetime.datetime.strptime(LastBuyDay,'%Y-%m-%d').date()
        i = -1
        while TheDatas[0][i]<=LastBuyDayDate:
            i-=1
        
        while TheDatas[0][i]<aDateDate:
            if TheDatas[2][i]>maxPriceSinceBuy:
                maxPriceSinceBuy=TheDatas[2][i]
            i-=1
        if TheDatas[0][i]!=aDateDate:
            print "These two dates should be same"
            print TheDatas[0][i]
            print aDateDate
            return [False,0.0]
        
        # last close
        #print self.DownPercent
        #print maxPriceSinceBuy
        if TheDatas[2][i+1]<maxPriceSinceBuy*(1-self.DownPercent):
            return [True,TheDatas[1][i]]
        else:
            return [False,0.0]
'''def RunAStrategy(initMoney,startDate,endDate):
    #startDate: 2016-01-01, string
    #Get data of that date
    
        if not isBuy:
            CurrentHold = BuyStockAtADay(RemainMoney, datetime.datetime.strftime(currentDate,'%Y-%m-%d'))
            if CurrentHold[1]>0:
                isBuy = True
                currentDate = CurrentHold[4]
            print CurrentHold
            print currentDate
            if currentDate>=theEndDate:
                break
        else:
            while True:
                theSMA = MyPredictDB.GetSMAAtADate(CurrentHold[0],10,datetime.datetime.strftime(currentDate,'%Y-%m-%d'))
                print theSMA
                print currentDate
                if theSMA[0]==-1:
                    currentDate += timedelta(days=1)
                else:
                    break
            if currentDate>=theEndDate:
                break
            if theSMA[0]==float('inf'):
                print CurrentHold
                return
            if theSMA[0]>theSMA[1]:
                RemainMoney = SellAStock(CurrentHold,theSMA[1])
                isBuy = False
        currentDate = currentDate + timedelta(days=1)
    
    print CurrentHold
    theSMA = MyPredictDB.GetSMAAtADate(CurrentHold[0],10,datetime.datetime.strftime(theEndDate,'%Y-%m-%d'))
    print CurrentHold[1]*theSMA[1]+CurrentHold[3]
    '''
    
if __name__=='__main__':
    '''for i in [20,30,40,50,60,70,80,90,100,120,140]:
        astrategy = BuyAllTimeHigh(6000,'2016-01-04','2017-01-04',i,0.03)
        astrategy.RunAStrategy()
        print 'i==='+str(i)
        print '=====================================\n\n\n'
    '''
    astrategy = BuyAllTimeHigh(6000,'2016-01-04','2017-01-04',20,0.03)
    