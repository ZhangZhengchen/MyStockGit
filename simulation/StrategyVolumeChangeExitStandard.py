'''
Created on 2017 7 8 

@author: Yali
'''
from MyDBSimulation import SimulationBaseClass
import datetime
from Predict import MyPredictDB
import collections
from datetime import timedelta
from data import PrepareData
import math
import numpy

class VolumeChangeExistLow(SimulationBaseClass):
    def __init__(self,InitMoney,StartDate,EndDate,AllTimeHighPeriod=200,AllTimeLowPeriod = 10,StockList = [],StockNumber = 3):
        '''
        @param AllTimeHighPeriod: one year all time high or one month all time high? the unit is days
        @param DownPercent: must >0 and <1 
        '''
        SimulationBaseClass.__init__(self, InitMoney, StartDate, EndDate,StockNumber)
        self.AllTimeLowPeriod = AllTimeLowPeriod
        self.AllList = StockList
        # Get all data
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d').date()
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d').date()
        totalPeriod = (theEndDate-theStartDate).days
        print("Getting all data")
        self.AllData = MyPredictDB.GetAllDataFromAList(self.AllList,EndDate,AllTimeHighPeriod+totalPeriod)
        print("Calculating all time highs")
        self.AllTimeHigh = {}
        self.AllTimeLow = {}
        RemoveData = []
        for anitem in self.AllData:
            # get all time high
            alltimehigh = {}
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
                    lastLowIndex = min(i+1+self.AllTimeLowPeriod,len(allClosePrices))
                    #print lastIndex
                    #print i
                    #print allClosePrices
                    if allClosePrices[i]>max(allClosePrices[i+1:lastIndex]):
                        alltimehigh[allDates[i].strftime('%Y-%m-%d')]=True
                    else:
                        alltimehigh[allDates[i].strftime('%Y-%m-%d')]=False
                        
                    if allClosePrices[i]<min(allClosePrices[i+1:lastLowIndex]):
                        alltimelow[allDates[i].strftime('%Y-%m-%d')] = True
                    else:
                        alltimelow[allDates[i].strftime('%Y-%m-%d')] = False
                        
                od = collections.OrderedDict(sorted(alltimehigh.items(),reverse=True))
                self.AllTimeHigh[anitem] = od
                
                odlow = collections.OrderedDict(sorted(alltimelow.items(),reverse=True))
                self.AllTimeLow[anitem] = odlow
                
            except:
                if anitem in self.AllTimeHigh:
                    del self.AllTimeHigh[anitem]
                if anitem in self.AllTimeLow:
                    del self.AllTimeLow[anitem]
                RemoveData.append(anitem)
                
        for anitem in RemoveData:
            del self.AllData[anitem]
    
    
    
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
            if len(self.CurrentList)<self.StockNumber:
                BuyRes = self.GetBuyList(currentDate.strftime('%Y-%m-%d'))
                for anitem in BuyRes:
                    self.BuyAStock(currentDate.strftime('%Y-%m-%d'), anitem[0], anitem[1])
                    if len(self.CurrentList)==self.StockNumber:
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
        Percentage = (self.RemainMoney+totalmoney)/self.InitMoney
        print('Percent is '+str(Percentage))
        print('Detail:')
        print('Win times')
        print(self.Win)
        print('Lose times')
        print(self.Lose)
        if self.Win['Time']+self.Lose['Time']>0:
            Profit = (self.RemainMoney+totalmoney-self.InitMoney)/(self.Win['Time']+self.Lose['Time'])
        else:
            Profit = 0.0
        if self.Lose['Average']>0:
            Expect = Profit/self.Lose['Average']
        else:
            Expect = 100.00
        
        return [Percentage,self.Win,self.Lose,Profit,Expect]
        
    
    def SellNow(self,Symbol,aDate): 
        '''
        If the price is lower than 3% of the buying price, sell it
        @param aDate: string format 2017-01-01 
        @param LastBuyDay: string format 2017-01-01 
        @param BuyPrice: float number 
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
        
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        
        ThisSymbolData = self.AllTimeLow[Symbol]
        if not aDate in ThisSymbolData:
            return [False,0.0] 
        dayinterval = 0
        while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            APreDate -= datetime.timedelta(days=1)
            dayinterval+=1
        if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            return [False,0.0]
        
        # if the lose money has achieve the maximum, sell
        BuyMoney = 0.0
        TheBuyData = self.CurrentList[Symbol]
        TotalNumber = 0
        for anitem in TheBuyData:
            BuyMoney += anitem[0]*anitem[1]
            TotalNumber += anitem[0]
        i=0
        while TheDatas[0][i]!=APreDate.date():
            i+=1
        ClosePrice = TheDatas[2][i]*TotalNumber
        if (BuyMoney-ClosePrice)>=self.InitMoney*0.025*len(TheBuyData):
        #if (BuyMoney-ClosePrice)>=150.00:
            return [True,TheDatas[1][i]]
        # if all time low, sell        
        elif ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
            i = 0
            while TheDatas[0][i]!=aDateDate:
                i+=1
            
            return [True,TheDatas[1][i]]
        else:
            return [False,0.0]
        
    def GetBuyList(self,aDate):
        '''
        @param aDate: string format
        @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
        Get the stocks achieved all time high yesterday.
        Then buy at the open price today.
        The stock is ordered by the volume*close price yesterday.
        '''
        StockList = []
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        for anitem in self.AllTimeHigh:
            ThisSymbolData = self.AllTimeHigh[anitem]
            if not aDate in ThisSymbolData:
                continue
            dayinterval = 0
            while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                APreDate -= datetime.timedelta(days=1)
                dayinterval+=1
            if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                continue
            
            
                
            if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
                PrePreDate = APreDate-datetime.timedelta(days=1)
                i=0
                while i<4 and not PrePreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                    PrePreDate -= datetime.timedelta(days=1)
                    i+=1
                if not PrePreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                    StockList.append(anitem)
                else:
                    if ThisSymbolData[PrePreDate.strftime('%Y-%m-%d')]==False:
                        StockList.append(anitem)
                #StockList.append(anitem)
        #sort the stocks according to the volume increase
        TheCompany = []
        for asymbol in StockList:
            TheSymbolData = self.AllData[asymbol]
            i = 0
            while TheSymbolData[0][i]!=APreDate.date():
                i+=1
            PreVolume = TheSymbolData[-1][i]
            PrePreVolume = 0
            for k in range(1,6):
                if i+k<len(TheSymbolData[-1]):
                    PrePreVolume+=TheSymbolData[-1][i+k]
                else:
                    break
            if k>0:
                PrePreVolume = PrePreVolume/k
            else:
                PrePreVolume = PreVolume
            if PrePreVolume>0:
                TheCompany.append(float(PreVolume)/float(PrePreVolume))
            else:
                TheCompany.append(1)
        #print(TheCompany)
        #print(StockList)   
        
        Index = numpy.argsort(TheCompany)
        #print('argsort result')
        #print(Index)
        Index = list(reversed(Index))
        #print('reverse index')
        #print(Index)
        SortedList = [None]*len(StockList)
        for i in range(len(StockList)):
            SortedList[i] = StockList[Index[i]]
        OpenPrices = []
        theDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        #print theDate
        for asymbol in SortedList:
            TheDatas = self.AllData[asymbol]
            #print TheDatas[0]
            i = 0
            for adate in TheDatas[0]:
                #print adate
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
    
    def GetBuyListNow(self,aDate):
        '''
        @param aDate: string format
        @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
        Get the stocks achieved all time high yesterday.
        Then buy at the open price today.
        The stock is ordered by the volume*close price yesterday.
        '''
        StockList = []
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        for anitem in self.AllTimeHigh:
            ThisSymbolData = self.AllTimeHigh[anitem]
            dayinterval = 0
            while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                APreDate -= datetime.timedelta(days=1)
                dayinterval+=1
            if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                continue
                
            if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
                PrePreDate = APreDate-datetime.timedelta(days=1)
                i=0
                while i<4 and not PrePreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                    PrePreDate -= datetime.timedelta(days=1)
                    i+=1
                if not PrePreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                    StockList.append(anitem)
                else:
                    if ThisSymbolData[PrePreDate.strftime('%Y-%m-%d')]==False:
                        StockList.append(anitem)
                #StockList.append(anitem)
        #sort the stocks according to the volume increase
        TheCompany = []
        for asymbol in StockList:
            TheSymbolData = self.AllData[asymbol]
            i = 0
            while TheSymbolData[0][i]!=APreDate.date():
                i+=1
            PreVolume = TheSymbolData[-1][i]
            PrePreVolume = 0
            for k in range(1,6):
                if i+k<len(TheSymbolData[-1]):
                    PrePreVolume+=TheSymbolData[-1][i+k]
                else:
                    break
            if k>0:
                PrePreVolume = PrePreVolume/k
            else:
                PrePreVolume = PreVolume
            if PrePreVolume>0:
                TheCompany.append(float(PreVolume)/float(PrePreVolume))
            else:
                TheCompany.append(1)
        #print(TheCompany)
        #print(StockList)   
        
        Index = numpy.argsort(TheCompany)
        #print('argsort result')
        #print(Index)
        Index = list(reversed(Index))
        #print('reverse index')
        #print(Index)
        SortedList = [None]*len(StockList)
        for i in range(len(StockList)):
            SortedList[i] = StockList[Index[i]]
        ReturnList =[]
        
        #print SortedList
        #print OpenPrices
        for i in range(len(SortedList)):
            ReturnList.append([SortedList[i],0.0])
        return ReturnList


class SellAllTimeLow(VolumeChangeExistLow):
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
            if len(self.CurrentList)<self.StockNumber:
                BuyRes = self.GetBuyList(currentDate.strftime('%Y-%m-%d'))
                for anitem in BuyRes:
                    self.BuyAStock(currentDate.strftime('%Y-%m-%d'), anitem[0], anitem[1])
                    if len(self.CurrentList)==self.StockNumber:
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
        Percentage = (self.RemainMoney+totalmoney)/self.InitMoney
        print('Percent is '+str(Percentage))
        print('Detail:')
        print('Win times')
        print(self.Win)
        print('Lose times')
        print(self.Lose)
        if self.Win['Time']+self.Lose['Time']>0:
            Profit = (self.RemainMoney+totalmoney-self.InitMoney)/(self.Win['Time']+self.Lose['Time'])
        else:
            Profit = 0.0
        if self.Lose['Average']>0:
            Expect = Profit/self.Lose['Average']
        else:
            Expect = 100.00
        
        return [Percentage,self.Win,self.Lose,Profit,Expect]
        
        
    def BuyAStock(self,theDate,Symbol,BuyPrice):
        '''
        Buy a stock on some day
        Calculate the money left
        Update status
        @param theDate:string format 2017-01-01 
        '''
        NumberHold = 0
        if len(self.CurrentList)>=self.StockNumber:
            return
        RemainMoney = float(self.RemainMoney)/(self.StockNumber-len(self.CurrentList))-10 
        
        if RemainMoney<BuyPrice:
            #print ("there is not enough money. "+str(self.RemainMoney)+". The stock price is "+str(BuyPrice))
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
            #print("we remain cash "+str(self.RemainMoney))
            #print self.CurrentList
    
    def GetBuyList(self,aDate):
        '''
        @param aDate: string format
        @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
        Get the stocks achieved all time high yesterday.
        Then buy at the open price today.
        The stock is ordered by the volume*close price yesterday.
        '''
        StockList = []
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        for anitem in self.AllTimeLow:
            #ThisSymbolData = self.AllTimeLow[anitem]
            ThisSymbolData = self.AllTimeHigh[anitem]
            if not aDate in ThisSymbolData:
                continue
            dayinterval = 0
            while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                APreDate -= datetime.timedelta(days=1)
                dayinterval+=1
            if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                continue
                
            if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
                StockList.append(anitem)
        #sort the stocks according to the volume increase
        TheCompany = []
        for asymbol in StockList:
            TheSymbolData = self.AllData[asymbol]
            i = 0
            while TheSymbolData[0][i]!=APreDate.date():
                i+=1
            PreVolume = TheSymbolData[-1][i]
            PrePreVolume = 0
            for k in range(1,6):
                if i+k<len(TheSymbolData[-1]):
                    PrePreVolume+=TheSymbolData[-1][i+k]
                else:
                    break
            if k>0:
                PrePreVolume = PrePreVolume/k
            else:
                PrePreVolume = PreVolume
            if PrePreVolume>0:
                TheCompany.append(float(PreVolume)/float(PrePreVolume))
            else:
                TheCompany.append(1)
        #print(TheCompany)
        #print(StockList)   
        
        Index = numpy.argsort(TheCompany)
        #print('argsort result')
        #print(Index)
        Index = list(reversed(Index))
        #print('reverse index')
        #print(Index)
        SortedList = [None]*len(StockList)
        for i in range(len(StockList)):
            SortedList[i] = StockList[Index[i]]
        OpenPrices = []
        theDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        #print theDate
        for asymbol in SortedList:
            TheDatas = self.AllData[asymbol]
            #print TheDatas[0]
            i = 0
            for adate in TheDatas[0]:
                #print adate
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
            
            # win or lose
            if BuyMoney<=SellMoney:
                self.Lose['Time']+=1
                self.Lose['Money'].append(SellMoney-BuyMoney)
                self.Lose['Min'] = numpy.min(self.Lose['Money'])
                self.Lose['Max'] = numpy.max(self.Lose['Money'])
                self.Lose['Average'] = numpy.mean(self.Lose['Money'])
            else:
                self.Win['Time']+=1
                self.Win['Money'].append(BuyMoney-SellMoney)
                self.Win['Min'] = numpy.min(self.Win['Money'])
                self.Win['Max'] = numpy.max(self.Win['Money'])
                self.Win['Average'] = numpy.mean(self.Win['Money'])
        else:
            print("We are not holding "+Symbol)
        #print("we remain cash "+str(self.RemainMoney))
    
    
    def SellNow(self,Symbol,aDate): 
        '''
        If the price is lower than 3% of the buying price, sell it
        @param aDate: string format 2017-01-01 
        @param LastBuyDay: string format 2017-01-01 
        @param BuyPrice: float number 
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
        
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        
        #ThisSymbolData = self.AllTimeHigh[Symbol]
        ThisSymbolData = self.AllTimeLow[Symbol]
        if not aDate in ThisSymbolData:
            return [False,0.0] 
        dayinterval = 0
        while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            APreDate -= datetime.timedelta(days=1)
            dayinterval+=1
        if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            return [False,0.0]
        
        # if the lose money has achieve the maximum, sell
        BuyMoney = 0.0
        TheBuyData = self.CurrentList[Symbol]
        TotalNumber = 0
        for anitem in TheBuyData:
            BuyMoney += anitem[0]*anitem[1]
            TotalNumber += anitem[0]
        i=0
        while TheDatas[0][i]!=APreDate.date():
            i+=1
        ClosePrice = TheDatas[2][i]*TotalNumber
        if (ClosePrice-BuyMoney)>=self.InitMoney*0.025*len(TheBuyData):
            return [True,TheDatas[1][i]]
        # if all time low, sell        
        elif ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
            i = 0
            while TheDatas[0][i]!=aDateDate:
                i+=1
            
            return [True,TheDatas[1][i]]
        else:
            return [False,0.0]

                     
if __name__=='__main__':
    
    Step=''
    XLB=PrepareData.GetBigCompany("../data/XLB.txt")
    XLE=PrepareData.GetBigCompany("../data/XLE.txt")
    XLF=PrepareData.GetBigCompany("../data/XLF.txt")
    XLI=PrepareData.GetBigCompany("../data/XLI.txt")
    XLK=PrepareData.GetBigCompany("../data/XLK.txt")
    XLP=PrepareData.GetBigCompany("../data/XLP.txt")
    XLU=PrepareData.GetBigCompany("../data/XLU.txt")
    XLV=PrepareData.GetBigCompany("../data/XLV.txt")
    XLY=PrepareData.GetBigCompany("../data/XLY.txt")
    
    UpTrend = [XLB,XLF,XLI,XLK,XLV,XLY]
    
    BigLists = []
    for anitem in UpTrend:
        for aname in anitem:
            if not aname in BigLists:
                BigLists.append(aname)
    
    Step='Test'
    if Step=='Test':
        StartDate = '2016-01-04'
        #StartDate = '2015-01-06'
        #EndDate = '2016-01-25'
        EndDate = '2016-06-29'
        AllRes = {}
        AllVar = {}
        for i in [10,20,30,60,90,100,120,150,200]:
            temp = []
            for j in [10,20,30,60]:
                astrategy = VolumeChangeExistLow(5000,StartDate,EndDate,i,j,BigLists,1)
                #astrategy = SellAllTimeLow(5000,StartDate,EndDate,i,j,BigLists,3)
                [Percent,Win,Lose,AverageProfit,Expection] = astrategy.RunAStrategy()
                print ('i==='+str(i)+'\tj===='+str(j))
                AllRes[str(i)+','+str(j)] = [Percent,AverageProfit,Expection]
                temp.append(Percent)
                print ('=====================================\n\n\n')
            AllVar[i] = [numpy.mean(temp),numpy.std(temp)]
        AllRes = collections.OrderedDict(sorted(AllRes.items()))
        for anitem in AllRes:
            print (anitem+'\t'+str(AllRes[anitem]))
        
        print (AllVar)