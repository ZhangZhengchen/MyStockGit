'''
Created on 2017 8 12

@author: Yali
'''

from StrategyExitVariation import GetSPXInfo,ReadStockHistoryFromCSV
import datetime
from datetime import timedelta
import numpy as np
import collections
import sys
from StrategyFunctions import GetAllTimeHighList,CalculatePositionSize
from StrategyFunctions import MarketSituation,Holding
from data import PrepareData
import matplotlib.pyplot as plt
import os,cPickle

class MyTrendFollowingStrategy():
    '''
    If the market is > 100day SMA, buy only.
    Else if the market is < 100day SMA and > 200day SMA, buy and sell.
    Else if the market is <200 day SMA and < 100 day SMA, sell only.
    '''
    def __init__(self,InitMoney,StartDate,EndDate,BULL_ATHP=200,BULL_ATLP = 30,BULL_VibrationPeriod = 10,BULL_VibrationRatio=3.5,\
                 BEAR_ATHP=30,BEAR_ATLP = 100,BEAR_VibrationPeriod = 10,BEAR_VibrationRatio=3.5,\
                 StockList = [],StockNumber = 3, Leverage=5,\
                 ShortTermMAPeriod=100,LongTermMAPeriod=200):
        self.LongPosition = {}
        self.ShortPosition = {}

        # money
        self.InitMoney = InitMoney
        self.Leverage = Leverage
        self.RemainMoney = self.InitMoney*self.Leverage
        self.TrueMoney = InitMoney
        self.Margin = 0.0
        self.Commission = 15
        self.TrueMoneyHistory = {}
        
        
        self.Win = {'Time':0,'Max':0.0,'Min':0.0,'Average':0.0,'Money':[],'HoldingDays':[]}
        self.Lose = {'Time':0,'Max':0.0,'Min':0.0,'Average':0.0,'Money':[],'HoldingDays':[]}
        self.MaxStockNumber = StockNumber
        if StockNumber<=0:
            self.MaxStockNumber = 1
        # Bull    
        self.BULL_VibrationPeriod = BULL_VibrationPeriod
        self.BULL_VibrationRatio = BULL_VibrationRatio
        self.BULL_ATHIGHP = BULL_ATHP
        self.BULL_ATLOWP = BULL_ATLP
        
        #BEAR
        self.BEAR_VibrationPeriod = BEAR_VibrationPeriod
        self.BEAR_VibrationRatio = BEAR_VibrationRatio
        self.BEAR_ATHIGHP = BEAR_ATHP
        self.BEAR_ATLOWP = BEAR_ATLP
        
        self.AllList = StockList
        
        
        # Get all data
        self.StartDate = StartDate
        self.EndDate = EndDate
        tempAllTimeHigh = np.max([self.BULL_ATHIGHP,self.BULL_ATLOWP,self.BEAR_ATHIGHP,self.BEAR_ATLOWP])
        self.AllData = self.GetHistoryData(tempAllTimeHigh)
        self.GetUtilityData()
        self.MarketSituation = self._getMarketSituation(ShortTermMAPeriod, LongTermMAPeriod)
        
        self.MarginMargin = 1.3
    
    
    def GetHistoryData(self,AllTimeHighPeriod):
        '''
        @param BeTesting: If testing, read data from CSV files. Else, read data from database.
        @return: The returned data is a dictionary. The key is symbols, the values are history data.
                History data is an array. Pricedate,Open,Close,High,Low,Volume. The Pricedate[0] is the most recent date/end date.
        '''
        print("Getting all data")
        AllData = {}
        ReadStockHistoryFromCSV(self.StartDate,self.EndDate,AllTimeHighPeriod,AllData)
        return AllData
    
    
    def GetUtilityData(self):
        '''
        If we are testing, we calculate the useful data before running the strategies to save running time.
        We will use something like: Does a stock reach All Time High/Low every day. Mean vibration of each day. etc.
        '''
        print("Calculating all time highs")
        [self.BULL_AllTimeHighHistory, self.BULL_AllTimeLowHistory, self.BULL_Vibration] = \
        self._getMiddleData(self.BULL_ATHIGHP, self.BULL_ATLOWP, self.BULL_VibrationPeriod, self.BULL_VibrationRatio,"Long")
        
        [self.BEAR_AllTimeHighHistory, self.BEAR_AllTimeLowHistory, self.BEAR_Vibration] = \
        self._getMiddleData(self.BEAR_ATHIGHP, self.BEAR_ATLOWP, self.BEAR_VibrationPeriod, self.BEAR_VibrationRatio,'Short')
    
    def _getMiddleData(self,AllTimeHighPeriod,AllTimeLowPeriod,VibrationPeriod,VibrationRatio,LongOrShort='Long'): 
        DumpFile = '../data/'+LongOrShort+'_High_'+str(AllTimeHighPeriod)+'_Low_'+str(AllTimeLowPeriod)+'_VibrationPeriod_'+str(VibrationPeriod)+'_VibrationRation_'+str(VibrationRatio)
        if os.path.isfile(DumpFile):
            [AllTimeHighHis,AllTimeLowHis,VibrationHis] = cPickle.load(open(DumpFile,'rb'))
            return [AllTimeHighHis,AllTimeLowHis,VibrationHis]
         
        AllTimeHighHis = {}
        AllTimeLowHis = {}
        VibrationHis = {}
        RemoveData = []  
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d').date()
        for anitem in self.AllData:
            # get all time high
            alltimehigh = {}
            alltimelow = {}
            AVibration = {}
            AMeanVibration = {}
            ADayVibration = {}
            TheStockData = self.AllData[anitem]
            allClosePrices = []
            allDates = []
            # the index of start date in the array
            # the front, the near date. the end, the previous date
            startIndex = -1
            i = 0
            allOpenPrices = TheStockData[1]
            allClosePrices = TheStockData[2]
            allHighPrices = TheStockData[3]
            allLowPrices = TheStockData[4]
            ###
            #sometimes there is 0 in the data, this is an error. We fix it using a simple method.
            self._fixZeroValues(allOpenPrices)
            self._fixZeroValues(allClosePrices)
            self._fixZeroValues(allHighPrices)
            self._fixZeroValues(allLowPrices)
                        
            ###
            PreClosePrices = allClosePrices[1:]
            PreClosePrices.append(0.0)
            HMinPreClose = np.array(allHighPrices)-np.array(PreClosePrices)
            PreCloseMinL = np.array(PreClosePrices) - np.array(allLowPrices)
            HighMinLow = np.array(allHighPrices)-np.array(allLowPrices)
            allVibration = []
            for viIndex in range(len(HMinPreClose)):
                allVibration.append(np.max([HMinPreClose[viIndex],PreCloseMinL[viIndex],HighMinLow[viIndex]]))
            
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
                    lastVibrationIndex = min(i+1+VibrationPeriod,len(allClosePrices))
                    lastLowIndex = min(i+1+AllTimeLowPeriod,len(allClosePrices))
                    #print lastIndex
                    #print i
                    #print allClosePrices
                    currentStringFormatDate = allDates[i].strftime('%Y-%m-%d')
                    if allClosePrices[i]>max(allClosePrices[i+1:lastIndex]):
                        alltimehigh[currentStringFormatDate]=True
                    else:
                        alltimehigh[currentStringFormatDate]=False
                        
                    if allClosePrices[i]<min(allClosePrices[i+1:lastLowIndex]):
                        alltimelow[currentStringFormatDate] = True
                    else:
                        alltimelow[currentStringFormatDate] = False
                        
                    #calculate vibration
                    AMeanVibration[currentStringFormatDate] = np.mean(allVibration[i+1:lastVibrationIndex])
                    #ADayVibration[currentStringFormatDate] = allHighPrices[i]-allLowPrices[i]
                    #ADayVibration[currentStringFormatDate] = np.max([allHighPrices[i]-allLowPrices[i],allHighPrices[i]-allClosePrices[i+1],allClosePrices[i+1]-allLowPrices[i]])
                    ADayVibration[currentStringFormatDate] = allVibration[i]
                    if LongOrShort=='Long':
                        if ADayVibration[currentStringFormatDate]>VibrationRatio*AMeanVibration[currentStringFormatDate] \
                        and allClosePrices[i]<allOpenPrices[i]:
                            AVibration[currentStringFormatDate] = True
                        else:
                            AVibration[currentStringFormatDate] = False
                    else:
                        if ADayVibration[currentStringFormatDate]>VibrationRatio*AMeanVibration[currentStringFormatDate] \
                        and allClosePrices[i]>allOpenPrices[i]:
                            AVibration[currentStringFormatDate] = True
                        else:
                            AVibration[currentStringFormatDate] = False
     
                od = collections.OrderedDict(sorted(alltimehigh.items(),reverse=True))
                AllTimeHighHis[anitem] = od
                
                odVibration = collections.OrderedDict(sorted(AVibration.items(),reverse=True))
                odlowMean = collections.OrderedDict(sorted(AMeanVibration.items(),reverse=True))
                odlowADay = collections.OrderedDict(sorted(ADayVibration.items(),reverse=True))
                VibrationHis[anitem] = [odVibration,odlowMean,odlowADay]
                
                odlow = collections.OrderedDict(sorted(alltimelow.items(),reverse=True))
                AllTimeLowHis[anitem] = odlow
            except:
                if anitem in AllTimeHighHis:
                    del AllTimeHighHis[anitem]
                if anitem in VibrationHis:
                    del VibrationHis[anitem]
                if anitem in AllTimeLowHis:
                    del AllTimeLowHis[anitem]
                RemoveData.append(anitem)
                
        for anitem in RemoveData:
            del self.AllData[anitem]
        
        cPickle.dump([AllTimeHighHis,AllTimeLowHis,VibrationHis], open(DumpFile,'wb'))
        return [AllTimeHighHis,AllTimeLowHis,VibrationHis]
        
    def _fixZeroValues(self,AnArray):
        for checkindex in range(len(AnArray)):
                if AnArray[checkindex]==0:
                    if checkindex==0:
                        tempindex = checkindex+1
                        while AnArray[tempindex]==0:
                            tempindex+=1
                        AnArray[checkindex] = AnArray[tempindex]
                    else:
                        AnArray[checkindex] = AnArray[checkindex-1]    
                        
                        
    def _getMarketSituation(self,ShortTermMAPeriod,LongTermMAPeriod):
        '''
        If close price of ShortTermMA>= close price of LongTermMA, up trend
        Else down trend
        
        If Up Trend: 
            if SPY close above ShortTermMA, bull
            if SPY close under ShortTermMA and above LongTermMA, flat
            if SPY close under LongTermMA, bear
        If Down Trend:
            if SPY close under ShortTermMA, bear
            if SPY close above ShortTermMA and under LongTermMA, flat
            if SPY close above LongTermMA, bull
        '''
        # if we can load, we just load
        FileName = '../data/MarketSituation_'+str(ShortTermMAPeriod)+'_'+str(LongTermMAPeriod)
        if os.path.isfile(FileName):
            Situation = cPickle.load(open(FileName,'rb'))
            return Situation
        # if not, then calculate it and save
        SPYData = GetSPXInfo()
        # get short term ma
        TotalData = len(SPYData)
        if TotalData<ShortTermMAPeriod or TotalData<LongTermMAPeriod:
            print('Total data number is less than MA length')
            sys.exit("The program is stopped.")
        if ShortTermMAPeriod>=LongTermMAPeriod:
            print('Please make sure SHORT TERM is short than LONG TERM')
            sys.exit("The program is stopped.")
        Dates = []
        ClosePrices = []
        for i in range(TotalData):
            Dates.append(SPYData.keys()[i])
            ClosePrices.append(SPYData[Dates[i]][0])
            
        Situation = {}
        for i in range(TotalData-1):
            endindex = np.min([i+ShortTermMAPeriod+1,TotalData])
            ShortSMA = np.mean(ClosePrices[i+1:endindex])
            
            endindex = np.min([i+LongTermMAPeriod+1,TotalData])
            LongSMA = np.mean(ClosePrices[i+1:endindex])
            
            Trend = MarketSituation.FLAT
            if ShortSMA>=LongSMA:# up trend
                #Trend = MarketSituation.BULL
                # here we use i+1 because we need to calculate yesterday's value
                if ClosePrices[i+1]>ShortSMA:
                    Trend = MarketSituation.BULL
                elif ClosePrices[i+1]<ShortSMA and ClosePrices[i+1]>LongSMA:
                    Trend = MarketSituation.BULL
                elif ClosePrices[i+1]<LongSMA:
                    Trend = MarketSituation.FLAT
            else:
                #Trend = MarketSituation.BEAR
                if ClosePrices[i+1]>LongSMA:
                    Trend = MarketSituation.FLAT
                elif ClosePrices[i+1]<LongSMA and ClosePrices[i+1]>ShortSMA:
                    Trend = MarketSituation.BEAR
                elif ClosePrices[i+1]<ShortSMA:
                    Trend = MarketSituation.BEAR
            # save ShortSMA and Long SMA as a backup
            Situation[Dates[i]] = [Trend,ShortSMA,LongSMA]
        Situation = collections.OrderedDict(sorted(Situation.items(),reverse=True))
        cPickle.dump(Situation, open(FileName,'wb'))
        return Situation
    
    def RunAStrategy(self):
        '''
        If Bull: Buy Only
        If Bear: Sell Only
        If Flat: No Operation at the moment. Later should be Swing 
        '''
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d')
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d')
        currentDate = theStartDate
        MinimumMoney = [1e10,datetime.date.today()]
        while currentDate<=theEndDate:
            if len(self.LongPosition)+len(self.ShortPosition)<self.MaxStockNumber:
                # long
                BuyRes = GetAllTimeHighList(currentDate.strftime('%Y-%m-%d'), self.AllData, self.BULL_AllTimeHighHistory, self.MarketSituation,'Long')
                for anitem in BuyRes:
                    self.Long_BuyAStock(currentDate.strftime('%Y-%m-%d'), anitem[0], anitem[1])
                    if len(self.LongPosition)+len(self.ShortPosition)>=self.MaxStockNumber:
                        break
                # short
                SellRes = GetAllTimeHighList(currentDate.strftime('%Y-%m-%d'), self.AllData, self.BEAR_AllTimeHighHistory, self.MarketSituation, 'Short')
                for anitem in SellRes:
                    self.Short_SellAStock(currentDate.strftime('%Y-%m-%d'), anitem[0], anitem[1])
                    if len(self.LongPosition)+len(self.ShortPosition)>=self.MaxStockNumber:
                        break
                    
            Long_removed = []
            Short_removed = []
            for i in range(len(self.LongPosition)):
                asymbol = self.LongPosition.keys()[i]
                [SellOrNot,SellPrice] = self.Long_SellNow(asymbol,currentDate.strftime('%Y-%m-%d'))
                if SellOrNot:
                    self.Long_SellAStock(asymbol, SellPrice, currentDate.strftime('%Y-%m-%d'))
                    Long_removed.append(asymbol)
            
            for i in range(len(self.ShortPosition)):
                asymbol = self.ShortPosition.keys()[i]
                [SellOrNot,SellPrice] = self.Short_CoverNow(asymbol,currentDate.strftime('%Y-%m-%d'))
                if SellOrNot:
                    self.Short_CoverAStock(asymbol, SellPrice, currentDate.strftime('%Y-%m-%d'))
                    Short_removed.append(asymbol)
                    
            CurrentMoney = self.CalculateTotalMoney(currentDate.strftime('%Y-%m-%d'))
            if CurrentMoney<MinimumMoney[0] and CurrentMoney>0.0:
                MinimumMoney = [CurrentMoney,currentDate]
            for anitem in Long_removed:
                del self.LongPosition[anitem]
            for anitem in Short_removed:
                del self.ShortPosition[anitem]
            #save the true money
            #self.TrueMoneyList[currentDate]=self.TrueMoney
            if CurrentMoney>0.0:
                self.TrueMoneyHistory[currentDate]=CurrentMoney
            currentDate+=timedelta(days=1)
            
        '''thecurrentdata = self.AllData
        totalmoney = 0
        totalBuyMoney = 0
        for anitem in self.LongPosition:
            thedata = self.LongPosition[anitem]
            totalnum = 0
            for adata in thedata:
                totalnum += adata.HoldingNumber
                totalBuyMoney += adata.HoldingNumber*adata.OpenPrice
            print('We are holding '+str(totalnum) +' '+anitem)
            print('The current price is '+str(thecurrentdata[anitem][2][0]))
            themoney = totalnum*thecurrentdata[anitem][2][0]
            totalmoney += themoney
        #totalmoney/=self.Leverage
        #print('we have remain cash:'+str(self.RemainMoney/self.Leverage))
        #print('we have total money:'+str(self.RemainMoney+totalmoney))
        FinalMoney = self.TrueMoney-totalBuyMoney+totalmoney'''
        
        FinalMoney = self.CalculateTotalMoney(currentDate.strftime('%Y-%m-%d'))
        print('we have total money:'+str(FinalMoney))
        Percentage = (FinalMoney)/self.InitMoney
        print('Percent is '+str(Percentage))
        print('Detail:')
        print('Win times')
        print(self.Win)
        print('Lose times')
        print(self.Lose)
        if self.Win['Time']+self.Lose['Time']>0:
            Profit = (FinalMoney-self.InitMoney)/(self.Win['Time']+self.Lose['Time'])
        else:
            Profit = 0.0
        if self.Lose['Average']>0:
            Expect = Profit/self.Lose['Average']
        else:
            Expect = 100.00
        print('Total lose is '+str(np.sum(self.Lose['Money'])))
        print('Total win is '+str(np.sum(self.Win['Money'])))
        print('Current true money '+str(self.TrueMoney))
        #print('Current buy money '+str(totalBuyMoney))
        #print('Current sell money '+str(totalmoney))
        print('Minimum Market Value is '+str(MinimumMoney[0])+' '+MinimumMoney[1].strftime('%Y-%m-%d'))
        TrueMoneyListSorted = collections.OrderedDict(sorted(self.TrueMoneyHistory.items(),reverse=True))
        beDraw = True
        if beDraw:
            fig, ax = plt.subplots(1)
            ax.plot(TrueMoneyListSorted.keys(),TrueMoneyListSorted.values())
            fig.autofmt_xdate()
            plt.show()
        return [Percentage,self.Win,self.Lose,Profit,Expect]
    
    def Long_BuyAStock(self,theDate,Symbol,BuyPrice):
        '''
        Buy a stock on some day
        Calculate the money left
        Update status
        @param theDate:string format 2017-01-01 
        '''
        NumberHold = 0
        if len(self.LongPosition)+len(self.ShortPosition)>=self.MaxStockNumber:
            return
        if self.TrueMoney<self.Commission:
            return
        
        if self.RemainMoney<BuyPrice:
            #print ("there is not enough money. "+str(self.RemainMoney)+". The stock price is "+str(BuyPrice))
            return
        
        if self.Commission*2/self.RemainMoney>0.02:
            return
        
        if BuyPrice>0.0:
            MaxNumberHold = np.floor(self.RemainMoney/BuyPrice)
            MeanVibrations = self.BULL_Vibration[Symbol][1]
            if not theDate in MeanVibrations:
                print 'Error! The date is not in list.'
                print theDate+' '+Symbol
                sys.exit('The program will stop now')
                
            TheVibration = MeanVibrations[theDate]
            [NumberHold,StopPrice] = CalculatePositionSize(self.TrueMoney,TheVibration, BuyPrice, \
                                                                ratio=0.025,VibrationRatio=self.BULL_VibrationRatio,Commission=self.Commission)
            if NumberHold==0:
                return

            if NumberHold>MaxNumberHold:
                NumberHold = MaxNumberHold
            #self.RemainMoney -= NumberHold*BuyPrice
            Margin = NumberHold*BuyPrice/self.Leverage
            if self.TrueMoney<self.Margin+Margin+self.Commission:
                return
            
            if self.TrueMoney/(self.Margin+Margin)<self.MarginMargin:
                return
            
            
            self.Margin += Margin
            self.TrueMoney -= self.Commission
            self.RemainMoney = (self.TrueMoney-self.Margin)*self.Leverage
            print('After Buying [TrueMoney,Margin,RemainBuyPower]')
            print [self.TrueMoney,self.Margin,self.RemainMoney]
            thehold = Holding(BuyPrice,NumberHold,theDate,Margin)
            thehold.StopLoss =  StopPrice
            if Symbol in self.LongPosition:
                current = self.LongPosition[Symbol]
                current.append(thehold)
                self.LongPosition[Symbol] = current
            else:
                self.LongPosition[Symbol] = [thehold]
                
            print('buy '+str(NumberHold)+' '+Symbol +' with price '+str(BuyPrice)+' at '+theDate)
            print('Stop loss price is '+str(StopPrice))
            print("we remain cash "+str(self.RemainMoney))  
            
    def Long_SellNow(self,Symbol,aDate): 
        '''
        If the price is lower than 3% of the buying price, sell it
        @param aDate: string format 2017-01-01 
        @param LastBuyDay: string format 2017-01-01 
        @param BuyPrice: float number 
        @return: If sell, return [True,SellPrice]. Else return [False,0.0]
        '''           
        if not Symbol in self.LongPosition:
            return [False,0.0]
        
        BuyInfo = self.LongPosition[Symbol]
        # if it is the same day of buying, return false
        LastBuyDay = BuyInfo[-1].OpenDate
        LastBuyDate = datetime.datetime.strptime(LastBuyDay,'%Y-%m-%d').date()
        if aDate==LastBuyDay:
            return [False,0.0]
        
        aDateDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        TheDatas = self.AllData[Symbol]
        
        if not aDateDate in TheDatas[0]:
            return [False,0.0]
        # weekend, public holiday etc.

        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        
        ThisSymbolData = self.BULL_Vibration[Symbol][0]

        dayinterval = 0
        while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            APreDate -= datetime.timedelta(days=1)
            dayinterval+=1
        if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            return [False,0.0]
        
        # if the lose money has achieve the maximum, sell
        BuyMoney = 0.0
        TheBuyData = self.LongPosition[Symbol]
        TotalNumber = 0
        for anitem in TheBuyData:
            BuyMoney += anitem.HoldingNumber*anitem.OpenPrice
            TotalNumber += anitem.HoldingNumber
        i=0
        while TheDatas[0][i]!=APreDate.date():
            i+=1
        ClosePrice = TheDatas[2][i]*TotalNumber
        ProfitLose = self._calculateMaxProfitAndLose(Symbol, TheDatas[2][i])
        #MaxLoseMoney = numpy.min([200,self.TrueMoney*0.025])
        MaxLoseMoney = self.TrueMoney*0.025
        if (BuyMoney-ClosePrice)>=MaxLoseMoney:
            #if (BuyMoney-ClosePrice)>=150.00:
            print 'Buy money is '+str(BuyMoney)+' Close money is '+str(ClosePrice)+'. The possible money is '+str(BuyMoney-ClosePrice)
            print 'Threshold is '+str(MaxLoseMoney)
            return [True,TheDatas[1][i-1]]
        elif TheDatas[2][i]<TheBuyData[-1].StopLoss:
            print('Price is lower than the stop loss. Close Price is '+str(TheDatas[2][i])+' Stop loss is '+str(TheBuyData[-1].StopLoss))
            return [True,TheDatas[1][i-1]]

        # if all time low, sell        
        elif ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
            MeanVibration = self.BULL_Vibration[Symbol][1]
            ADayVibration = self.BULL_Vibration[Symbol][2]
            print 'The day vibration is '+str(ADayVibration[APreDate.strftime('%Y-%m-%d')])+'. Average vibration is '+str(MeanVibration[APreDate.strftime('%Y-%m-%d')])
            return [True,TheDatas[1][i-1]]

        # all time low
        elif self.BULL_AllTimeLowHistory[Symbol][APreDate.strftime('%Y-%m-%d')]==True:
            print 'Close at 30 days low yesterday.'
            return [True,TheDatas[1][i-1]]

        #profit lose
        elif ProfitLose[0]:
            print 'Profit lose more than 30%. '
            print ProfitLose
            return [True,TheDatas[1][i-1]]

        elif APreDate in self.MarketSituation and self.MarketSituation[APreDate][0]==MarketSituation.BEAR:
            print 'It is a bear market now.'
            print self.MarketSituation[APreDate]
            return [True,TheDatas[1][i-1]]
        elif (aDateDate-LastBuyDate).days>20 and ProfitLose[3]<1.03:
            print 'Exit with time limitation.'
            print LastBuyDay+' '+aDate+' '+str((aDateDate-LastBuyDate).days)+' '+str(ProfitLose[3])
            return [True,TheDatas[1][i-1]]
        else:
            return [False,0.0]
    
    def Long_SellAStock(self,Symbol,SellPrice,SellDate):
        '''
        @param SellDate: string format 2017-01-01 
        '''
        Commission = 0.0
        if Symbol in self.LongPosition:
            holdings = self.LongPosition[Symbol]
            SellMoney = 0
            BuyMoney = 0.0
            
            for anitem in holdings:
                SellMoney += anitem.HoldingNumber*SellPrice
                print('Sell '+str(anitem.HoldingNumber)+' '+Symbol +' with price '+str(SellPrice)+' at '+SellDate)
                # calculate total buy number and money
                BuyMoney += anitem.HoldingNumber*anitem.OpenPrice
                Commission +=self.Commission
            self.TrueMoney +=SellMoney-BuyMoney-self.Commission
            self.Margin -=BuyMoney/self.Leverage
            if self.TrueMoney<self.Margin+self.Commission:
                self.RemainMoney = 0.0
            else:
                self.RemainMoney = (self.TrueMoney-self.Margin)*self.Leverage
            print('After selling [TrueMoney,Margin,RemainBuyPower]')
            print [self.TrueMoney,self.Margin,self.RemainMoney]
            #self.RemainMoney +=SellMoney-10
            BuyDate = holdings[-1].OpenDate
            BuyDate = datetime.datetime.strptime(BuyDate,'%Y-%m-%d').date()
            SellDate = datetime.datetime.strptime(SellDate,'%Y-%m-%d').date()
            HoldingDays = (SellDate-BuyDate).days
            # win or lose
            if SellMoney-BuyMoney<self.Commission+Commission:
                self.Lose['Time']+=1
                self.Lose['Money'].append(BuyMoney-SellMoney+self.Commission+Commission)
                self.Lose['Min'] = np.min(self.Lose['Money'])
                self.Lose['Max'] = np.max(self.Lose['Money'])
                self.Lose['Average'] = np.mean(self.Lose['Money'])
                self.Lose['HoldingDays'].append(HoldingDays)
                print('Lose. '+'We hold it for '+str(HoldingDays)+' days. We lose '+str(BuyMoney-SellMoney+self.Commission+Commission))
            else:
                self.Win['Time']+=1
                self.Win['Money'].append(SellMoney-BuyMoney-self.Commission-Commission)
                self.Win['Min'] = np.min(self.Win['Money'])
                self.Win['Max'] = np.max(self.Win['Money'])
                self.Win['Average'] = np.mean(self.Win['Money'])
                self.Win['HoldingDays'].append(HoldingDays)
                print('Win. '+'We hold it for '+str(HoldingDays)+' days. We win '+str(SellMoney - BuyMoney-self.Commission-Commission))
        else:
            print("We are not holding "+Symbol)
        print("we remain cash "+str(self.RemainMoney))  
        
    def _calculateMaxProfitAndLose(self,asymbol,ClosePrice,LongOrShort="Long"):
        '''
        @param asymbol:
        @param aDate: String format %Y-%m-%d  
        '''
        if LongOrShort=="Long":
            CurrentHolds = self.LongPosition[asymbol]
        else:
            CurrentHolds = self.ShortPosition[asymbol]
        TotalProfit = 0.0
        TotalMaxprofit = 0.0
        TotalBuyMoney = 0.0
        
        for anitem in CurrentHolds:
            if LongOrShort=='Long':
                profit = (ClosePrice - anitem.OpenPrice)*anitem.HoldingNumber
            else:
                profit = (anitem.OpenPrice - ClosePrice)*anitem.HoldingNumber
            if profit>0 and profit>anitem.MaximumProfit:
                anitem.MaximumProfit = profit
            elif profit<0 and profit<anitem.MaximumLose:
                anitem.MaximumLose = profit
            TotalProfit += profit
            TotalMaxprofit += anitem.MaximumProfit
            TotalBuyMoney += anitem.OpenPrice*anitem.HoldingNumber
            
            
        if TotalProfit>0 and TotalProfit<TotalMaxprofit*0.7 and (TotalBuyMoney+TotalMaxprofit)/TotalBuyMoney>1.50:
            return [True,profit,anitem.MaximumProfit,(TotalBuyMoney+TotalMaxprofit)/TotalBuyMoney]
        else:
            return [False,profit,anitem.MaximumProfit,(TotalBuyMoney+TotalMaxprofit)/TotalBuyMoney]
            
    def CalculateTotalMoney(self,OneDay):
        '''
        @param OneDay: 
        '''
        todayIndex = 0
        ADate = datetime.datetime.strptime(OneDay,'%Y-%m-%d').date()
        TheDatas = self.AllData['AAPL']
        if not ADate in TheDatas[0]:
            return -10.0
        while TheDatas[0][todayIndex]!=ADate:
            todayIndex+=1
        totalBuyMoney = 0.0
        totalmoney = 0.0
        thecurrentdata = self.AllData
        for anitem in self.LongPosition:
            thedata = self.LongPosition[anitem]
            totalnum = 0
            for adata in thedata:
                totalnum += adata.HoldingNumber
                totalBuyMoney += adata.HoldingNumber*adata.OpenPrice
            #print('We are holding '+str(totalnum) +' '+anitem)
            #print('The current price is '+str(thecurrentdata[anitem][2][todayIndex]))
            themoney = totalnum*thecurrentdata[anitem][2][todayIndex]
            totalmoney += themoney
        FinalMoney = self.TrueMoney-totalBuyMoney+totalmoney
        
        totalBuyMoney = 0.0
        totalmoney = 0.0
        for anitem in self.ShortPosition:
            thedata = self.ShortPosition[anitem]
            totalnum = 0
            for adata in thedata:
                totalnum += adata.HoldingNumber
                totalBuyMoney += adata.HoldingNumber*adata.OpenPrice
            #print('We are holding '+str(totalnum) +' '+anitem)
            #print('The current price is '+str(thecurrentdata[anitem][2][todayIndex]))
            themoney = totalnum*thecurrentdata[anitem][2][todayIndex]
            totalmoney += themoney
        FinalMoney +=totalBuyMoney-totalmoney
        
        return FinalMoney   
 
    def Short_SellAStock(self,theDate,Symbol,SellPrice):
        NumberHold = 0
        if len(self.LongPosition)+len(self.ShortPosition)>=self.MaxStockNumber:
            return
        if self.TrueMoney<self.Commission:
            return
        
        if self.RemainMoney<SellPrice:
            #print ("there is not enough money. "+str(self.RemainMoney)+". The stock price is "+str(BuyPrice))
            return
        
        if self.Commission*2/self.RemainMoney>0.02:
            return
        
        if SellPrice>0.0:
            MaxNumberHold = np.floor(self.RemainMoney/SellPrice)
            MeanVibrations = self.BEAR_Vibration[Symbol][1]
            if not theDate in MeanVibrations:
                print 'Error! The date is not in list.'
                print theDate+' '+Symbol
                sys.exit('The program will stop now')
                
            TheVibration = MeanVibrations[theDate]
            [NumberHold,StopPrice] = CalculatePositionSize(self.TrueMoney,TheVibration, SellPrice, \
                                        ratio=0.025,VibrationRatio=self.BULL_VibrationRatio,Commission=self.Commission,LongOrShort='Short')
            if NumberHold==0:
                return

            if NumberHold>MaxNumberHold:
                NumberHold = MaxNumberHold
            #self.RemainMoney -= NumberHold*BuyPrice
            Margin = NumberHold*SellPrice/self.Leverage
            if self.TrueMoney<self.Margin+Margin+self.Commission:
                return
            
            if self.TrueMoney/(self.Margin+Margin)<self.MarginMargin:
                return
            
            
            self.Margin += Margin
            self.TrueMoney -= self.Commission
            self.RemainMoney = (self.TrueMoney-self.Margin)*self.Leverage
            print('After Shorting [TrueMoney,Margin,RemainBuyPower]')
            print [self.TrueMoney,self.Margin,self.RemainMoney]
            thehold = Holding(SellPrice,NumberHold,theDate,Margin)
            thehold.StopLoss =  StopPrice
            if Symbol in self.ShortPosition:
                current = self.ShortPosition[Symbol]
                current.append(thehold)
                self.ShortPosition[Symbol] = current
            else:
                self.ShortPosition[Symbol] = [thehold]
                
            print('SHORT---sell '+str(NumberHold)+' '+Symbol +' with price '+str(SellPrice)+' at '+theDate)
            print('Stop loss price is '+str(StopPrice))
            print("we remain cash "+str(self.RemainMoney)) 
            
    def Short_CoverNow(self,Symbol,aDate): 
        '''
        @param aDate: string format 2017-01-01 
        @return: If cover, return [True,BuyPrice]. Else return [False,0.0]
        '''           
        if not Symbol in self.ShortPosition:
            return [False,0.0]
        
        BuyInfo = self.ShortPosition[Symbol]
        # if it is the same day of buying, return false
        LastBuyDay = BuyInfo[-1].OpenDate
        if aDate==LastBuyDay:
            return [False,0.0]
        
        aDateDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        TheDatas = self.AllData[Symbol]
        
        if not aDateDate in TheDatas[0]:
            return [False,0.0]
        # weekend, public holiday etc.

        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        
        ThisSymbolData = self.BEAR_Vibration[Symbol][0]

        dayinterval = 0
        while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            APreDate -= datetime.timedelta(days=1)
            dayinterval+=1
        if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            return [False,0.0]
        
        # if the lose money has achieve the maximum, sell
        BuyMoney = 0.0
        TheBuyData = self.ShortPosition[Symbol]
        TotalNumber = 0
        for anitem in TheBuyData:
            BuyMoney += anitem.HoldingNumber*anitem.OpenPrice
            TotalNumber += anitem.HoldingNumber
        i=0
        while TheDatas[0][i]!=APreDate.date():
            i+=1
        ClosePrice = TheDatas[2][i]*TotalNumber
        ProfitLose = self._calculateMaxProfitAndLose(Symbol, TheDatas[2][i],"Short")
        #MaxLoseMoney = numpy.min([200,self.TrueMoney*0.025])
        MaxLoseMoney = self.TrueMoney*0.025
        if (ClosePrice-BuyMoney)>=MaxLoseMoney:
            #if (BuyMoney-ClosePrice)>=150.00:
            print 'Buy money is '+str(BuyMoney)+' Close money is '+str(ClosePrice)+'. The possible money is '+str(ClosePrice-BuyMoney)
            print 'Threshold is '+str(MaxLoseMoney)
            return [True,TheDatas[1][i-1]]
        elif TheDatas[2][i]>TheBuyData[-1].StopLoss:
            print('Price is lower than the stop loss. Close Price is '+str(TheDatas[2][i])+' Stop loss is '+str(TheBuyData[-1].StopLoss))
            return [True,TheDatas[1][i-1]]

        # if all time low, sell        
        elif ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
            MeanVibration = self.BEAR_Vibration[Symbol][1]
            ADayVibration = self.BEAR_Vibration[Symbol][2]
            print 'The day vibration is '+str(ADayVibration[APreDate.strftime('%Y-%m-%d')])+'. Average vibration is '+str(MeanVibration[APreDate.strftime('%Y-%m-%d')])
            return [True,TheDatas[1][i-1]]

        # all time low
        elif self.BEAR_AllTimeLowHistory[Symbol][APreDate.strftime('%Y-%m-%d')]==True:
            print 'Close at 30 days low yesterday.'
            return [True,TheDatas[1][i-1]]

        #profit lose
        elif ProfitLose[0]:
            print 'Profit lose more than 30%. '
            print ProfitLose
            return [True,TheDatas[1][i-1]]

        elif APreDate in self.MarketSituation and self.MarketSituation[APreDate][0]==MarketSituation.BULL:
            print 'It is a bull market now. We shall cover the shorts.'
            print self.MarketSituation[APreDate]
            return [True,TheDatas[1][i-1]]
        else:
            return [False,0.0]
        
    def Short_CoverAStock(self,Symbol,SellPrice,SellDate):
        '''
        @param SellDate: string format 2017-01-01 
        '''
        Commission = 0.0
        if Symbol in self.ShortPosition:
            holdings = self.ShortPosition[Symbol]
            SellMoney = 0
            BuyMoney = 0.0
            
            for anitem in holdings:
                SellMoney += anitem.HoldingNumber*SellPrice
                print('Cover '+str(anitem.HoldingNumber)+' '+Symbol +' with price '+str(SellPrice)+' at '+SellDate)
                # calculate total buy number and money
                BuyMoney += anitem.HoldingNumber*anitem.OpenPrice
                Commission +=self.Commission
            self.TrueMoney +=BuyMoney-SellMoney-self.Commission
            self.Margin -=BuyMoney/self.Leverage
            if self.TrueMoney<self.Margin+self.Commission:
                self.RemainMoney = 0.0
            else:
                self.RemainMoney = (self.TrueMoney-self.Margin)*self.Leverage
            print('After covering [TrueMoney,Margin,RemainBuyPower]')
            print [self.TrueMoney,self.Margin,self.RemainMoney]
            #self.RemainMoney +=SellMoney-10
            BuyDate = holdings[-1].OpenDate
            BuyDate = datetime.datetime.strptime(BuyDate,'%Y-%m-%d').date()
            SellDate = datetime.datetime.strptime(SellDate,'%Y-%m-%d').date()
            HoldingDays = (SellDate-BuyDate).days
            # win or lose
            if BuyMoney-SellMoney<self.Commission+Commission:
                self.Lose['Time']+=1
                self.Lose['Money'].append(SellMoney-BuyMoney+self.Commission+Commission)
                self.Lose['Min'] = np.min(self.Lose['Money'])
                self.Lose['Max'] = np.max(self.Lose['Money'])
                self.Lose['Average'] = np.mean(self.Lose['Money'])
                self.Lose['HoldingDays'].append(HoldingDays)
                print('Lose. '+'We hold it for '+str(HoldingDays)+' days. We lose '+str(SellMoney-BuyMoney+self.Commission+Commission))
            else:
                self.Win['Time']+=1
                self.Win['Money'].append(BuyMoney-SellMoney-self.Commission-Commission)
                self.Win['Min'] = np.min(self.Win['Money'])
                self.Win['Max'] = np.max(self.Win['Money'])
                self.Win['Average'] = np.mean(self.Win['Money'])
                self.Win['HoldingDays'].append(HoldingDays)
                print('Win. '+'We hold it for '+str(HoldingDays)+' days. We win '+str(BuyMoney-SellMoney-self.Commission-Commission))
        else:
            print("We are not holding "+Symbol)
        print("we remain cash "+str(self.RemainMoney)) 
if __name__=="__main__":
    BigLists = PrepareData.GetBigCompany('../data/BigCompany.txt')
    BigLists.remove('FTV')
    #BigLists.remove('CMCSA')
    
    StartDate = '2016-01-23'
    #StartDate = '2015-01-06'
    #EndDate = '2016-01-25'
    EndDate = '2017-07-31'
    AllRes = {}
    AllVar = {}
    #for i in [60,90,100,120,150]:
    for i in [100]:
        temp = []
        #for j in [10,20,30,60]:
        for j in [30]:
            #for vr in [2.4,2.7,3.0,3.3]:
            for vr in [3.5]:
                astrategy = MyTrendFollowingStrategy(7000,StartDate,EndDate,BULL_ATHP=i,BULL_ATLP=30,BULL_VibrationPeriod=j,BULL_VibrationRatio=vr,\
                                                     StockList=BigLists,StockNumber=10,Leverage=8,\
                                                     ShortTermMAPeriod=75, LongTermMAPeriod=350)
                                                   
                #astrategy = SellAllTimeLow(5000,StartDate,EndDate,i,j,BigLists,3)
                [Percent,Win,Lose,AverageProfit,Expection] = astrategy.RunAStrategy()
                print 'i==='+str(i)+'\tj===='+str(j)+'\tvr==='+str(vr)
                AllRes[str(i)+','+str(j)+','+str(vr)] = [Percent,AverageProfit,Expection]
                temp.append(Percent)
                print '=====================================\n\n\n'
        AllVar[i] = [np.mean(temp),np.std(temp)]
    AllRes = collections.OrderedDict(sorted(AllRes.items()))
    for anitem in AllRes:
        print anitem+'\t'+str(AllRes[anitem])
    
    print AllVar  
