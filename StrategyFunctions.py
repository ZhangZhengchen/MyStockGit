'''
Created on 2017 8 13

@author: Yali
'''
import datetime
import numpy as np
from enum import Enum


class MarketSituation(Enum):
    BULL = 1
    FLAT = 2
    BEAR = 3

class Holding():
    def __init__(self,OpenPrice,HoldingNumber,OpenDate,MarginRequired,StopLoss=0.0):
        self.OpenPrice = OpenPrice
        self.HoldingNumber = HoldingNumber
        self.OpenDate = OpenDate
        self.MarginRequired = MarginRequired
        self.MaximumProfit = 0.0
        self.MaximumLose = 0.0
        self.StopLoss = StopLoss

def _getAllTimeHighOfADay(aDate,AllTimeHighHistory):
    StockList = []
    CurrentDay = datetime.datetime.strptime(aDate,'%Y-%m-%d')
    TheTempData = AllTimeHighHistory['BA']
    if not aDate in TheTempData:
        #print(aDate +' is not in the MarketSituation.')
        return None,[]
    for index,value in enumerate(TheTempData.keys()):
        if value==aDate and index+1<len(TheTempData.keys()):
            APreDate = datetime.datetime.strptime(TheTempData.keys()[index+1],'%Y-%m-%d')
            break
    if index+1>=len(TheTempData.keys()):
        return None,[]

    
    for anitem in AllTimeHighHistory:
        ThisSymbolData = AllTimeHighHistory[anitem]
        if not aDate in ThisSymbolData:
            continue
        if not APreDate.strftime('%Y-%m-%d') in ThisSymbolData:
            continue
        
        if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==False:
            continue
        
        if ThisSymbolData[APreDate.strftime('%Y-%m-%d')]==True:
            StockList.append(anitem)
            '''# the day before yesterday should not be the highest
            PrePreDate = APreDate-datetime.timedelta(days=1)
            i=0
            while i<4 and not PrePreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                PrePreDate -= datetime.timedelta(days=1)
                i+=1
            if not PrePreDate.strftime('%Y-%m-%d') in ThisSymbolData:
                StockList.append(anitem)
            else:
                if ThisSymbolData[PrePreDate.strftime('%Y-%m-%d')]==False:
                    StockList.append(anitem)'''
    return APreDate,StockList
def GetAllTimeHighList(aDate,AllData,AllTimeHighHistory, TheMarketSituation,LongOrShort='Long'):
    '''
    @param aDate: string format, current day
    @param AllData: All data of the stock lists. 
    @param AllTimeHighHistory: It is a dictionary, the key is the symbols SYMBOL, the values are another dictionary ValueDic.
                               The key of ValueDic is a date DATE, the value of ValueDic is True or False.
                               If it is True, it means at the date DATE, the stock SYMBOL, achieved all time high. Otherwise, not.
    @param TheMarketSituation: It must be an ordered dictionary. The key is a date in datetime format, the value is an array [BULL/FLAT/BEAR,ShortTermSMA,LongTermSMA]
    @return:   a list of stocks. Each item in the list [Symbol,BuyPrice]
    Get the stocks achieved all time high yesterday.
    Then buy at the open price today.
    The stock is ordered by the volume*close price yesterday.
    '''
    APreDate,StockList = _getAllTimeHighOfADay(aDate, AllTimeHighHistory)
    if APreDate==None:
        return []
    if LongOrShort=='Long':
        if APreDate in TheMarketSituation and TheMarketSituation[APreDate][0]!=MarketSituation.BULL:
            print(aDate+'\t'+'It\'s not a BULL market. We don\'t buy anything now.')
            return []
    else:
        if APreDate in TheMarketSituation and TheMarketSituation[APreDate][0]!=MarketSituation.BEAR:
            print(aDate+'\t'+'It\'s not a BEAR market. We don\'t short anything now.')
            return []
            #StockList.append(anitem)
    #sort the stocks according to the volume increase
    TheCompany = []
    for asymbol in StockList:
        TheSymbolData = AllData[asymbol]
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
    
    Index = np.argsort(TheCompany)
    #print('argsort result')
    #print(Index)
    if LongOrShort=='Long':
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
        TheDatas = AllData[asymbol]
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

def CalculatePositionSize(TrueMoney,MeanVibration, OpenPrice, ratio=0.025, VibrationRatio=3.5, Commission=15,LongOrShort='Long'):
        '''
        @param TrueMoney: true money we have now 
        @param MeanVibration: Mean Vibration of the stock
        @param OpenPrice: The price if you buy this one 
        @param ratio: One trade shall not lose more than InitMoney*ratio
        @param VibrationRatio: default 3.5 
        self.InitMoney is the true money we have.
        The initial stop price is OpenPrice - VibrationRatio*MeanVibration 
        @return: [PositionSize,StopLoss]
        '''
        # Get Mean Vibration
        
        StopLose = VibrationRatio*MeanVibration
        TotalLose = TrueMoney*ratio
        #TotalLose = numpy.min([200,TotalLose])
        if StopLose<=0:
            return [0,0]
        if TrueMoney<OpenPrice:
            return [0,0]
        if TotalLose<StopLose:
            return [0,0]
        PositionSize = np.floor(TotalLose/StopLose)
        if Commission*2/(PositionSize*OpenPrice)>0.02:
            return [0,0]
        if LongOrShort=='Long':
            return [PositionSize,OpenPrice-StopLose] 
        else:
            return [PositionSize,OpenPrice+StopLose] 

