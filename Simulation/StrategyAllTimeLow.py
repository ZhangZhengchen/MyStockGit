'''
Created on 2017 6 25

@author: Yali
'''

from MyDBSimulation import SimulationBaseClass,BuyAllTimeHigh
import datetime
from Predict import MyPredictDB
import collections
from data import PrepareData
from datetime import timedelta
import math

class SellAllTimeLowWitList(SimulationBaseClass):
    def __init__(self,InitMoney,StartDate,EndDate,AllTimeHighPeriod=140,UpPercent = 0.05,StockList = []):
        '''
        @param AllTimeHighPeriod: one year all time high or one month all time high? the unit is days
        @param DownPercent: must >0 and <1 
        '''
        SimulationBaseClass.__init__(self, InitMoney, StartDate, EndDate)
        self.UpPercent = UpPercent
        self.AllList = StockList
        # Get all data
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d').date()
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d').date()
        totalPeriod = (theEndDate-theStartDate).days
        print("Getting all data")
        self.AllData = MyPredictDB.GetAllDataFromAList(self.AllList,EndDate,AllTimeHighPeriod+totalPeriod)
        print("Calculating all time lows")
        self.AllTimeLow = {}
        RemoveData = []
        for anitem in self.AllData:
            # get all time high
            alltimelow = {}
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
                    if allClosePrices[i]<min(allClosePrices[i+1:lastIndex]):
                        alltimelow[allDates[i].strftime('%Y-%m-%d')]=True
                    else:
                        alltimelow[allDates[i].strftime('%Y-%m-%d')]=False
                od = collections.OrderedDict(sorted(alltimelow.items(),reverse=True))
                self.AllTimeLow[anitem] = od
            except:
                if anitem in self.AllTimeLow:
                    del self.AllTimeLow[anitem]
                RemoveData.append(anitem)
        for anitem in RemoveData:
            del self.AllData[anitem]
    
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
        minBuyPrice = 1e5
        for anitem in BuyInfo:
            #anitem=[number hold,buy price,buy date]
            if anitem[1]<minBuyPrice:
                minBuyPrice = anitem[1]
        # If the price is lower than 5% of the buy price or the highest price, sell it.
        minPriceSinceBuy = minBuyPrice
        LastBuyDayDate= datetime.datetime.strptime(LastBuyDay,'%Y-%m-%d').date()
        i = -1
        while TheDatas[0][i]<=LastBuyDayDate:
            i-=1
        
        while TheDatas[0][i]<aDateDate:
            if TheDatas[2][i]<minPriceSinceBuy:
                minPriceSinceBuy=TheDatas[2][i]
            i-=1
        if TheDatas[0][i]!=aDateDate:
            print "These two dates should be same"
            print TheDatas[0][i]
            print aDateDate
            return [False,0.0]
        
        # last close
        #print self.DownPercent
        #print maxPriceSinceBuy
        if TheDatas[2][i+1]>minPriceSinceBuy*(1+self.UpPercent):
            return [True,TheDatas[1][i]]
        else:
            return [False,0.0]    
            
    
    def ShouldBeSellNow(self,Symbol,aDate,LastBuyDay,BuyPrice): 
        '''
        If the price is higher than 3% of the buying price, buy it
        @param aDate: string format 2017-01-01 
        @param LastBuyDay: string format 2017-01-01 
        @param BuyPrice: float number 
        @return: If sell, return [True,SellPrice]. Else return [False,0.0]
        '''           
        # if it is the same day of buying, return false
        if aDate==LastBuyDay:
            return [False,0.0]
        
        aDateDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        TheDatas = self.AllData[Symbol]
        # weekend, public holiday etc.
        if not aDateDate in TheDatas[0]:
            return [False,0.0]
        
        # If the price is lower than 5% of the buy price or the highest price, sell it.
        minPriceSinceBuy = BuyPrice
        LastBuyDayDate= datetime.datetime.strptime(LastBuyDay,'%Y-%m-%d').date()
        i = -1
        while TheDatas[0][i]<=LastBuyDayDate:
            i-=1
        
        # the highest close price
        while TheDatas[0][i]<aDateDate:
            if TheDatas[2][i]<minPriceSinceBuy:
                minPriceSinceBuy=TheDatas[2][i]
            i-=1
        
        '''# the highest price
        while TheDatas[0][i]<aDateDate:
            if TheDatas[3][i]>maxPriceSinceBuy:
                maxPriceSinceBuy=TheDatas[3][i]
            i-=1'''
            
        if TheDatas[0][i]!=aDateDate:
            print "These two dates should be same"
            print TheDatas[0][i]
            print aDateDate
            return [False,0.0]
        
        # last close
        #print self.DownPercent
        #print maxPriceSinceBuy
        if TheDatas[2][i+1]>minPriceSinceBuy*(1+self.UpPercent):
            return [True,TheDatas[1][i]]
        else:
            return [False,0.0]
        
        
    def SellAStock(self,Symbol,SellPrice,SellDate):
        '''
        @param SellDate: string format 2017-01-01 
        '''
        if Symbol in self.CurrentList:
            holdings = self.CurrentList[Symbol]
            SellMoney = 0
            # get buy money
            BuyMoney = 0
            for anitem in holdings:
                #anitem [NumberHold,buyprice,buydate]
                SellMoney += anitem[0]*SellPrice
                BuyMoney += anitem[0]*anitem[1]
                print('Buy '+str(anitem[0])+' '+Symbol +' with price '+str(SellPrice)+' at '+SellDate)
            # if sell high and buy low, then win money is positive
            self.RemainMoney += BuyMoney + BuyMoney - SellMoney-10
        else:
            print("We are not holding "+Symbol)
        print("we remain cash "+str(self.RemainMoney))
    
    def GetBuyList(self,aDate):
        '''
        @param aDate: string format
        @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
        Get the stocks achieved all time high yesterday.
        Then buy at the open price today.
        The stock is ordered by the volume*close price yesterday.
        '''
        StockList = []
        for anitem in self.AllTimeLow:
            ThisSymbolData = self.AllTimeLow[anitem]
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
        
    
    def RunAStrategy(self):
        '''
        The difference to the base class is in the last step.
        When calculate the last date's price, the basic class needs to read the database again.
        Here we just get the data from self.AllData
        '''
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
            
        thecurrentdata = self.AllData
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
        
        if RemainMoney<BuyPrice:
            print ("there is not enough money. "+str(self.RemainMoney)+". The stock price is "+str(BuyPrice))
            return
        
        if BuyPrice>0.0:
            NumberHold = math.floor(RemainMoney/BuyPrice)
            self.RemainMoney -= NumberHold*BuyPrice
            self.RemainMoney -= 10
            if Symbol in self.CurrentList:
                current = self.CurrentList[Symbol]
                current.append([NumberHold,BuyPrice,theDate])
                self.CurrentList[Symbol] = current
            else:
                self.CurrentList[Symbol] = [[NumberHold,BuyPrice,theDate]]
                
            print('sell '+str(NumberHold)+' '+Symbol +' with price '+str(BuyPrice)+' at '+theDate)
            print("we remain cash "+str(self.RemainMoney))
            print self.CurrentList
        
if __name__=='__main__':
    '''BigLists=PrepareData.GetBigCompany("../data/BigCompany.txt")
    for i in [10,20,40,60,80,100,120,140,160,180,200]:
        astrategy = SellAllTimeLowWitList(6000,'2015-11-04','2016-02-04',i,0.05,BigLists)
        astrategy.RunAStrategy()
        print 'i==='+str(i)
        print '=====================================\n\n\n'
        '''
        
    BigLists=PrepareData.GetBigCompany("../data/BigCompany.txt")
    EndDate = '2017-06-27'
    astrategy = SellAllTimeLowWitList(6000,'2017-01-04',EndDate,140,0.03,BigLists)
    #astrategy.RunAStrategy()
    res = astrategy.GetBuyList(EndDate)
    
    #res = astrategy.ShouldBeSellNow('AAPL', '2017-06-15', '2017-05-03', 146)
    print res