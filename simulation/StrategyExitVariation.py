'''
Created on 2017 7 13 

@author: Yali
'''
from StrategyVolumeChangeExitStandard import VolumeChangeExistLow
from MyDBSimulation import SimulationBaseClass
import datetime,collections
from Predict import MyPredictDB
import numpy 
from data import PrepareData
from datetime import timedelta
import matplotlib.pyplot as plt
from data.StockHistory import ReadStockHistoryFromCSV,GetSPXInfo
from StrategyFunctions import Holding


class BuyATHExitBigVibration(SimulationBaseClass):
    def __init__(self,InitMoney,StartDate,EndDate,AllTimeHighPeriod=200,AllTimeLowPeriod =30,VibrationPeriod = 10,\
                 StockList = [],StockNumber = 3, Leverage=5,VibrationRatio=3.5, BeTesting=False):
        '''
        @param AllTimeHighPeriod: one year all time high or one month all time high? the unit is days
        @param DownPercent: must >0 and <1 
        '''
        SimulationBaseClass.__init__(self, InitMoney, StartDate, EndDate,StockNumber)
        self.VibrationPeriod = VibrationPeriod
        self.VibrationRatio = VibrationRatio
        self.Leverage = Leverage
        self.RemainMoney = self.InitMoney*self.Leverage
        self.TrueMoney = InitMoney
        self.Margin = 0.0
        self.Commission = 15
        self.AllList = StockList
        
        self.TrueMoneyList = {}
        # Get all data
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d').date()
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d').date()
        totalPeriod = (theEndDate-theStartDate).days
        self.SPYData = []
        print("Getting all data")
        if not BeTesting:
            self.AllData = MyPredictDB.GetAllDataFromAList(self.AllList,EndDate,AllTimeHighPeriod+totalPeriod)
        else:
            self.SPYData = GetSPXInfo()
            self.AllData = {}
            ReadStockHistoryFromCSV(self.StartDate,self.EndDate,AllTimeHighPeriod,self.AllData)
        print("Calculating all time highs")
        self.AllTimeHigh = {}
        self.AllTimeLow = {}
        self.AllTimeLowPeriod = AllTimeLowPeriod
        self.Vibration = {}
        RemoveData = []
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
            #allVibration = numpy.abs(numpy.array(allClosePrices)-numpy.array(allOpenPrices))
            PreClosePrices = allClosePrices[1:]
            PreClosePrices.append(0.0)
            HMinPreClose = numpy.array(allHighPrices)-numpy.array(PreClosePrices)
            PreCloseMinL = numpy.array(PreClosePrices) - numpy.array(allLowPrices)
            HighMinLow = numpy.array(allHighPrices)-numpy.array(allLowPrices)
            allVibration = []
            for viIndex in range(len(HMinPreClose)):
                allVibration.append(numpy.max([HMinPreClose[viIndex],PreCloseMinL[viIndex],HighMinLow[viIndex]]))
            
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
                    lastVibrationIndex = min(i+1+self.VibrationPeriod,len(allClosePrices))
                    lastLowIndex = min(i+1+self.AllTimeLowPeriod,len(allClosePrices))
                    #print lastIndex
                    #print i
                    #print allClosePrices
                    currentStringFormatDate = allDates[i].strftime('%Y-%m-%d')
                    if allClosePrices[i]>max(allClosePrices[i+1:lastIndex]):
                        alltimehigh[currentStringFormatDate]=True
                    else:
                        alltimehigh[currentStringFormatDate]=False
                    
                    #calculate vibration
                    AMeanVibration[currentStringFormatDate] = numpy.mean(allVibration[i+1:lastVibrationIndex])
                    #ADayVibration[currentStringFormatDate] = allHighPrices[i]-allLowPrices[i]
                    ADayVibration[currentStringFormatDate] = numpy.max([allHighPrices[i]-allLowPrices[i],allHighPrices[i]-allClosePrices[i+1],allClosePrices[i+1]-allLowPrices[i]])
                    if ADayVibration[currentStringFormatDate]>self.VibrationRatio*AMeanVibration[currentStringFormatDate] and allClosePrices[i]<allOpenPrices[i]:
                        AVibration[currentStringFormatDate] = True
                    else:
                        AVibration[currentStringFormatDate] = False
                    
                    if allClosePrices[i]<min(allClosePrices[i+1:lastLowIndex]):
                        alltimelow[allDates[i].strftime('%Y-%m-%d')] = True
                    else:
                        alltimelow[allDates[i].strftime('%Y-%m-%d')] = False
                        
                od = collections.OrderedDict(sorted(alltimehigh.items(),reverse=True))
                self.AllTimeHigh[anitem] = od
                
                odVibration = collections.OrderedDict(sorted(AVibration.items(),reverse=True))
                odlowMean = collections.OrderedDict(sorted(AMeanVibration.items(),reverse=True))
                odlowADay = collections.OrderedDict(sorted(ADayVibration.items(),reverse=True))
                self.Vibration[anitem] = [odVibration,odlowMean,odlowADay]
                
                odlow = collections.OrderedDict(sorted(alltimelow.items(),reverse=True))
                self.AllTimeLow[anitem] = odlow
            except:
                if anitem in self.AllTimeHigh:
                    del self.AllTimeHigh[anitem]
                if anitem in self.Vibration:
                    del self.Vibration[anitem]
                if anitem in self.AllTimeLow:
                    del self.AllTimeLow[anitem]
                RemoveData.append(anitem)
                
        for anitem in RemoveData:
            del self.AllData[anitem]
            
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
                            
    def SellNow(self,Symbol,aDate,beTesting = True): 
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
        LastBuyDay = BuyInfo[-1].OpenDate
        if aDate==LastBuyDay:
            return [False,0.0]
        
        aDateDate = datetime.datetime.strptime(aDate,'%Y-%m-%d').date()
        TheDatas = self.AllData[Symbol]
        # weekend, public holiday etc.
        if not aDateDate in TheDatas[0] and beTesting:
            return [False,0.0]
        
        
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        
        ThisSymbolData = self.Vibration[Symbol][0]
        if not aDate in ThisSymbolData and beTesting:
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
            BuyMoney += anitem.HoldingNumber*anitem.OpenPrice
            TotalNumber += anitem.HoldingNumber
        i=0
        while TheDatas[0][i]!=APreDate.date():
            i+=1
        ClosePrice = TheDatas[2][i]*TotalNumber
        ProfitLose = self.CalculateMaxProfitAndLose(Symbol, TheDatas[2][i])
        #MaxLoseMoney = numpy.min([200,self.TrueMoney*0.025])
        MaxLoseMoney = self.TrueMoney*0.025
        if (BuyMoney-ClosePrice)>=MaxLoseMoney:
            #if (BuyMoney-ClosePrice)>=150.00:
            print( 'Buy money is '+str(BuyMoney)+' Close money is '+str(ClosePrice)+'. The possible money is '+str(BuyMoney-ClosePrice))
            print( 'Threshold is '+str(MaxLoseMoney))
            if beTesting:
                return [True,TheDatas[1][i-1]]
            else:
                return [True,0.0]
        elif TheDatas[2][i]<TheBuyData[-1].StopLoss:
            print('Price is lower than the stop loss. Close Price is '+str(TheDatas[2][i])+' Stop loss is '+str(TheBuyData[-1].StopLoss))
            if beTesting:
                return [True,TheDatas[1][i-1]]
            else:
                return [True,0.0]
        # if all time low, sell        
        elif ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
            MeanVibration = self.Vibration[Symbol][1]
            ADayVibration = self.Vibration[Symbol][2]
            print( 'The day vibration is '+str(ADayVibration[APreDate.strftime('%Y-%m-%d')])+'. Average vibration is '+str(MeanVibration[APreDate.strftime('%Y-%m-%d')]))
            if beTesting:
                return [True,TheDatas[1][i-1]]
            else:
                return [True,0.0]
        # all time low
        elif self.AllTimeLow[Symbol][APreDate.strftime('%Y-%m-%d')]==True:
            print( 'CLose at 30 days low yesterday.')
            if beTesting:
                return [True,TheDatas[1][i-1]]
            else:
                return [True,0.0]
        #profit lose
        elif ProfitLose[0]:
            print( 'Profit lose more than 30%. ')
            print( ProfitLose)
            if beTesting:
                return [True,TheDatas[1][i-1]]
            else:
                return [True,0.0]
        elif APreDate in self.SPYData and \
        ((self.SPYData[APreDate][0]<self.SPYData[APreDate][2] and self.SPYData[APreDate][1]>self.SPYData[APreDate][2])\
        or (self.SPYData[APreDate][0]<self.SPYData[APreDate][1] and self.SPYData[APreDate][1]<self.SPYData[APreDate][2]) ):
            print( 'SPY close below 200 day')
            print( self.SPYData[APreDate])
            return [True,TheDatas[1][i-1]]
        else:
            return [False,0.0]
        
    def CalculatePositionSize(self,TrueMoney,Symbol,OpenDate,OpenPrice, ratio=0.025, VibrationRatio=3.5):
        '''
        @param TrueMoney: true money we have now 
        @param Symbol: 
        @param OpenDate: string format date %Y-%m-%d
        @param OpenPrice: 
        @param ratio: One trade shall not lose more than InitMoney*ratio
        @param VibrationRatio: default 3.5 
        self.InitMoney is the true money we have.
        The initial stop price is OpenPrice - VibrationRatio*MeanVibration 
        '''
        # Get Mean Vibration
        MeanVibrations = self.Vibration[Symbol][1]
        if not OpenDate in MeanVibrations:
            print( 'Error! The date is not in list.')
            print( OpenDate+' '+Symbol)
            return 0
        TheVibration = MeanVibrations[OpenDate]
        StopLose = VibrationRatio*TheVibration
        TotalLose = TrueMoney*ratio
        #TotalLose = numpy.min([200,TotalLose])
        if StopLose<=0:
            return [0,0]
        if TrueMoney<OpenPrice:
            return [0,0]
        if TotalLose<StopLose:
            return [0,0]
        PositionSize = numpy.floor(TotalLose/StopLose)
        if self.Commission*2/(PositionSize*OpenPrice)>0.02:
            return [0,0]
        return [PositionSize,OpenPrice-StopLose]    
    
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
        if self.TrueMoney<self.Commission:
            return
        
        if self.RemainMoney<BuyPrice:
            #print( ("there is not enough money. "+str(self.RemainMoney)+". The stock price is "+str(BuyPrice))
            return
        
        if self.Commission*2/self.RemainMoney>0.02:
            return
        
        
        
        if BuyPrice>0.0:
            MaxNumberHold = numpy.floor(self.RemainMoney/BuyPrice)
            [NumberHold,StopPrice] = self.CalculatePositionSize(self.TrueMoney, Symbol, theDate, BuyPrice, ratio=0.025,VibrationRatio=self.VibrationRatio)
            if NumberHold==0:
                return

            if NumberHold>MaxNumberHold:
                NumberHold = MaxNumberHold
            #self.RemainMoney -= NumberHold*BuyPrice
            Margin = NumberHold*BuyPrice/self.Leverage
            if self.TrueMoney<self.Margin+Margin+self.Commission:
                return
            
            if self.TrueMoney/(self.Margin+Margin)<1.3:
                return
            
            
            self.Margin += Margin
            self.TrueMoney -= self.Commission
            self.RemainMoney = (self.TrueMoney-self.Margin)*self.Leverage
            print('After Buying [TrueMoney,Margin,RemainBuyPower]')
            print( [self.TrueMoney,self.Margin,self.RemainMoney])
            thehold = Holding(BuyPrice,NumberHold,theDate,Margin)
            thehold.StopLoss =  StopPrice
            if Symbol in self.CurrentList:
                current = self.CurrentList[Symbol]
                current.append(thehold)
                self.CurrentList[Symbol] = current
            else:
                self.CurrentList[Symbol] = [thehold]
                
            print('buy '+str(NumberHold)+' '+Symbol +' with price '+str(BuyPrice)+' at '+theDate)
            print('Stop loss price is '+str(StopPrice))
            print("we remain cash "+str(self.RemainMoney))    
            
    def SellAStock(self,Symbol,SellPrice,SellDate):
        '''
        @param SellDate: string format 2017-01-01 
        '''
        Commission = 0.0
        if Symbol in self.CurrentList:
            holdings = self.CurrentList[Symbol]
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
            print( [self.TrueMoney,self.Margin,self.RemainMoney])
            #self.RemainMoney +=SellMoney-10
            BuyDate = holdings[-1].OpenDate
            BuyDate = datetime.datetime.strptime(BuyDate,'%Y-%m-%d').date()
            SellDate = datetime.datetime.strptime(SellDate,'%Y-%m-%d').date()
            HoldingDays = (SellDate-BuyDate).days
            # win or lose
            if SellMoney-BuyMoney<self.Commission+Commission:
                self.Lose['Time']+=1
                self.Lose['Money'].append(BuyMoney-SellMoney+self.Commission+Commission)
                self.Lose['Min'] = numpy.min(self.Lose['Money'])
                self.Lose['Max'] = numpy.max(self.Lose['Money'])
                self.Lose['Average'] = numpy.mean(self.Lose['Money'])
                self.Lose['HoldingDays'].append(HoldingDays)
                print('Lose. '+'We hold it for '+str(HoldingDays)+' days. We lose '+str(BuyMoney-SellMoney+self.Commission+Commission))
            else:
                self.Win['Time']+=1
                self.Win['Money'].append(SellMoney-BuyMoney-self.Commission-Commission)
                self.Win['Min'] = numpy.min(self.Win['Money'])
                self.Win['Max'] = numpy.max(self.Win['Money'])
                self.Win['Average'] = numpy.mean(self.Win['Money'])
                self.Win['HoldingDays'].append(HoldingDays)
                print('Win. '+'We hold it for '+str(HoldingDays)+' days. We win '+str(SellMoney - BuyMoney-self.Commission-Commission))
        else:
            print("We are not holding "+Symbol)
        print("we remain cash "+str(self.RemainMoney))   
     
    
    def RunAStrategy(self):
        '''
        The difference to the base class is in the last step.
        When calculate the last date's price, the basic class needs to read the database again.
        Here we just get the data from self.AllData
        '''
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d')
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d')
        currentDate = theStartDate
        MinimumMoney = [1e10,datetime.date.today()]
        while currentDate<=theEndDate:
            if len(self.CurrentList)<self.StockNumber:
                BuyRes = self.GetBuyList(currentDate.strftime('%Y-%m-%d'))
                TodayNumber=0
                for anitem in BuyRes:
                    self.BuyAStock(currentDate.strftime('%Y-%m-%d'), anitem[0], anitem[1])
                    if len(self.CurrentList)==self.StockNumber:
                        break
                    TodayNumber+=1
                #if TodayNumber>=5:
                #    break
            removed = []
            for i in range(len(self.CurrentList)):
                asymbol = self.CurrentList.keys()[i]
                [SellOrNot,SellPrice] = self.SellNow(asymbol,currentDate.strftime('%Y-%m-%d'))
                if SellOrNot:
                    self.SellAStock(asymbol, SellPrice, currentDate.strftime('%Y-%m-%d'))
                    removed.append(asymbol)
            CurrentMoney = self.CalculateTotalMoney(currentDate.strftime('%Y-%m-%d'))
            if CurrentMoney<MinimumMoney[0] and CurrentMoney>0.0:
                MinimumMoney = [CurrentMoney,currentDate]
            for anitem in removed:
                del self.CurrentList[anitem]
            #save the true money
            #self.TrueMoneyList[currentDate]=self.TrueMoney
            if CurrentMoney>0.0:
                self.TrueMoneyList[currentDate]=CurrentMoney
            currentDate+=timedelta(days=1)
            
        thecurrentdata = self.AllData
        totalmoney = 0
        totalBuyMoney = 0
        for anitem in self.CurrentList:
            thedata = self.CurrentList[anitem]
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
        FinalMoney = self.TrueMoney-totalBuyMoney+totalmoney
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
        print('Total lose is '+str(numpy.sum(self.Lose['Money'])))
        print('Total win is '+str(numpy.sum(self.Win['Money'])))
        print('Current true money '+str(self.TrueMoney))
        print('Current buy money '+str(totalBuyMoney))
        print('Current sell money '+str(totalmoney))
        print('Minimum Market Value is '+str(MinimumMoney[0])+' '+MinimumMoney[1].strftime('%Y-%m-%d'))
        TrueMoneyListSorted = collections.OrderedDict(sorted(self.TrueMoneyList.items(),reverse=True))
        beDraw = True
        if beDraw:
            fig, ax = plt.subplots(1)
            ax.plot(TrueMoneyListSorted.keys(),TrueMoneyListSorted.values())
            fig.autofmt_xdate()
            plt.show()
        return [Percentage,self.Win,self.Lose,Profit,Expect]
    
    
    def CalculateMaxProfitAndLose(self,asymbol,ClosePrice):
        '''
        @param asymbol:
        @param aDate: String format %Y-%m-%d  
        '''
        CurrentHolds = self.CurrentList[asymbol]
        TotalProfit = 0.0
        TotalMaxprofit = 0.0
        TotalBuyMoney = 0.0
        
        for anitem in CurrentHolds:
            profit = (ClosePrice - anitem.OpenPrice)*anitem.HoldingNumber
            if profit>0 and profit>anitem.MaximumProfit:
                anitem.MaximumProfit = profit
            elif profit<0 and profit<anitem.MaximumLose:
                anitem.MaximumLose = profit
            TotalProfit += profit
            TotalMaxprofit += anitem.MaximumProfit
            TotalBuyMoney += anitem.OpenPrice*anitem.HoldingNumber
            
            
        if TotalProfit>0 and TotalProfit<TotalMaxprofit*0.7 and (TotalBuyMoney+TotalMaxprofit)/TotalBuyMoney>1.50:
            return [True,profit,anitem.MaximumProfit]
        else:
            return [False,profit,anitem.MaximumProfit]
            
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
        for anitem in self.CurrentList:
            thedata = self.CurrentList[anitem]
            totalnum = 0
            for adata in thedata:
                totalnum += adata.HoldingNumber
                totalBuyMoney += adata.HoldingNumber*adata.OpenPrice
            #print('We are holding '+str(totalnum) +' '+anitem)
            #print('The current price is '+str(thecurrentdata[anitem][2][todayIndex]))
            themoney = totalnum*thecurrentdata[anitem][2][todayIndex]
            totalmoney += themoney
        FinalMoney = self.TrueMoney-totalBuyMoney+totalmoney
        return FinalMoney
    
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
            
            if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==False:
                continue
            
            if APreDate in self.SPYData:
                TodaySPYData = self.SPYData[APreDate]
                #if TodaySPYData[0]<TodaySPYData[1] or TodaySPYData[1]<TodaySPYData[2]:
                if (TodaySPYData[0]<TodaySPYData[1] and TodaySPYData[1]>TodaySPYData[2])\
                or (TodaySPYData[1]<TodaySPYData[2] and TodaySPYData[0]<TodaySPYData[2]):
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
        #Get the stocks achieved all time high yesterday.
        #Then buy at the open price today.
        #The stock is ordered by the volume*close price yesterday.
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
            
            if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==False:
                continue
            
            if APreDate in self.SPYData:
                TodaySPYData = self.SPYData[APreDate]
                if TodaySPYData[0]<TodaySPYData[1] or TodaySPYData[1]<TodaySPYData[2]:
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
        
        StopLosses = []
        for asymbol in SortedList:
            MeanVibrations = self.Vibration[asymbol][1]
            if not APreDate.strftime('%Y-%m-%d') in MeanVibrations:
                print( 'Error! The date is not in list.')
                print( APreDate.strftime('%Y-%m-%d')+' '+asymbol)
                return 0
            TheVibration = MeanVibrations[APreDate.strftime('%Y-%m-%d')]
            StopLose = self.VibrationRatio*TheVibration
            StopLosses.append(StopLose)
        
        #print( SortedList
        #print( OpenPrices
        for i in range(len(SortedList)):
            ReturnList.append([SortedList[i],StopLosses[i]])
        return ReturnList
    
    def GetSellListNow(self,aDate):
        '''
        @param aDate: string format
        @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
        #Get the stocks achieved all time high yesterday.
        #Then buy at the open price today.
        #The stock is ordered by the volume*close price yesterday.
        '''
        StockList = []
        ThePreviousDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
        ThePreviousDay -= datetime.timedelta(days=1)
        APreDate = ThePreviousDay
        
        for anitem in self.AllTimeLow:
            ThisSymbolData = self.AllTimeLow[anitem]
            dayinterval = 0
            while dayinterval<4 and not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                APreDate -= datetime.timedelta(days=1)
                dayinterval+=1
            if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                continue
            
            if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==False:
                continue
            
            #if APreDate in self.SPYData:
            #    TodaySPYData = self.SPYData[APreDate]
            #    if TodaySPYData[0]<TodaySPYData[1] or TodaySPYData[1]<TodaySPYData[2]:
            #        continue
                
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
        
        StopLosses = []
        for asymbol in SortedList:
            MeanVibrations = self.Vibration[asymbol][1]
            if not APreDate.strftime('%Y-%m-%d') in MeanVibrations:
                print( 'Error! The date is not in list.')
                print( APreDate.strftime('%Y-%m-%d')+' '+asymbol)
                return 0
            TheVibration = MeanVibrations[APreDate.strftime('%Y-%m-%d')]
            StopLose = self.VibrationRatio*TheVibration
            StopLosses.append(StopLose)
        
        #print SortedList
        #print OpenPrices
        for i in range(len(SortedList)):
            ReturnList.append([SortedList[i],StopLosses[i]])
        return ReturnList
        
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
    BigLists = PrepareData.GetBigCompany('../data/BigCompany.txt')
    BigLists.remove('BLL')
    BigLists.remove('CMCSA')
    Step='Test'
    if Step=='Test':
        StartDate = '2014-01-08'
        #StartDate = '2015-01-06'
        #EndDate = '2016-01-25'
        EndDate = '2014-07-31'
        AllRes = {}
        AllVar = {}
        #for i in [60,90,100,120,150]:
        for i in [100]:
            temp = []
            #for j in [10,20,30,60]:
            for j in [10]:
                #for vr in [2.4,2.7,3.0,3.3]:
                for vr in [3.5]:
                    astrategy = BuyATHExitBigVibration(7000,StartDate,EndDate,i,j,BigLists,StockNumber=40,\
                                                       Leverage=8,VibrationRatio=vr,BeTesting=True)
                    #astrategy = SellAllTimeLow(5000,StartDate,EndDate,i,j,BigLists,3)
                    [Percent,Win,Lose,AverageProfit,Expection] = astrategy.RunAStrategy()
                    print( 'i==='+str(i)+'\tj===='+str(j)+'\tvr==='+str(vr))
                    AllRes[str(i)+','+str(j)+','+str(vr)] = [Percent,AverageProfit,Expection]
                    temp.append(Percent)
                    print( '=====================================\n\n\n')
            AllVar[i] = [numpy.mean(temp),numpy.std(temp)]
        AllRes = collections.OrderedDict(sorted(AllRes.items()))
        for anitem in AllRes:
            print( anitem+'\t'+str(AllRes[anitem]))
        print(AllVar) 