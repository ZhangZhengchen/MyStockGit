'''
Created on 2017 7 12

@author: Yali
'''
import sys
sys.path.append('../')
sys.path.append('../DataRelated')
import datetime
from StrategyVolumeChangeExitStandard import VolumeChangeExistLow,SellAllTimeLow
import numpy
from data import PrepareData
import collections
from StrategyExitVariation import BuyATHExitBigVibration

def GetBuyListToday(EndDate,BigLists):
    PreDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d')
    PreDate -= datetime.timedelta(days=1)
    for i in [30,60,100,120]:
        j = 10
        print('i==='+str(i))
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),i,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(7000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),AllTimeHighPeriod=i,\
                                           AllTimeLowPeriod = j,VibrationPeriod=j,StockList=BigLists,StockNumber=40,Leverage=8)
        #astrategy.RunAStrategy()
        res = astrategy.GetBuyListNow(EndDate)
        #res = astrategy.ShouldBeSellNow('AAPL', '2017-06-15', '2017-05-03', 146)
        print(res)
        print('\n')

def GetSellListToday(EndDate,BigLists):
    PreDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d')
    PreDate -= datetime.timedelta(days=1)
    for i in [30]:
        for j in [30,60,90,120]:
            print('j==='+str(j))
            #astrategy = VolumeChangeExistLow(5000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),i,j,BigLists,3)
            astrategy = BuyATHExitBigVibration(7000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),i,\
                                               AllTimeLowPeriod = j,VibrationPeriod=j,StockList=BigLists,StockNumber=40,Leverage=8)
            #astrategy.RunAStrategy()
            res = astrategy.GetSellListNow(EndDate)
            #res = astrategy.ShouldBeSellNow('AAPL', '2017-06-15', '2017-05-03', 146)
            print(res)
            print('\n')
        
def ShallSellToday(EndDate,BigLists,SymbolList):
    '''
    EndDate is the last closing day.
    Because normally when I check shall I sell them, today is not closed yet.
    '''
    for j in [30]:
        startindex = -1
        PreDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d')
        PreDate -= datetime.timedelta(days=1)
    
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',EndDate,100,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(5000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),100,j,StockList=BigLists,StockNumber=1)
        for asymbol in SymbolList:
            asymbol = asymbol.lower()
            if not asymbol in astrategy.AllData:
                print('No symbol '+asymbol)
                continue
            TheData = astrategy.AllData[asymbol]
            if startindex==-1:
                if not PreDate.date() in TheData[0]:
                    return
                
                for i in range(len(TheData[0])):
                    if TheData[0][i]==PreDate.date():
                        startindex = i
                        break
            LowestValue = numpy.min(TheData[2][startindex+1:startindex+j+1])
            if TheData[2][startindex]<LowestValue:
                print('SELL '+asymbol+'. Last close price is '+str(TheData[2][startindex]))
            else:
                print('Don\'t sell ' +asymbol+'. Last close price is '+str(TheData[2][startindex]))
            #print astrategy.SellNow(asymbol, EndDate)
            print('The Lowest value is '+str(LowestValue)+'. It should be your stop loss price\n\n\n')
            

def ShallSellTodayVibration(EndDate,BigLists,CurrentList):
    '''
    EndDate is the last closing day.
    Because normally when I check shall I sell them, today is not closed yet.
    '''
    for j in [10]:
        startindex = -1
        PreDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d')
        PreDate -= datetime.timedelta(days=1)
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',EndDate,100,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(7000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),100,j,StockList=BigLists,StockNumber=8)
        astrategy.CurrentList = CurrentList
        for asymbol in astrategy.CurrentList:
            asymbol = asymbol.lower()
            if not asymbol in astrategy.AllData:
                print('No symbol '+asymbol)
                continue
            TheData = astrategy.AllData[asymbol]
            if startindex==-1:
                if not PreDate.date() in TheData[0]:
                    return
                
                for i in range(len(TheData[0])):
                    if TheData[0][i]==PreDate.date():
                        startindex = i
                        break
            meanVibration = numpy.mean(numpy.abs(numpy.array(TheData[3][startindex+1:startindex+j+1])-numpy.array(TheData[4][startindex+1:startindex+j+1])))
            todayVibration = TheData[3][startindex] - TheData[4][startindex]
            if todayVibration>astrategy.VibrationRatio*meanVibration and TheData[1][startindex]>TheData[2][startindex]:
                print ('SELL '+asymbol+'. Mean vibration is '+str(meanVibration)+'. Today vibration is '+str(todayVibration))
            else:
                print ('Don\'t sell ' +asymbol+'. Mean vibration is '+str(meanVibration)+'. Today vibration is '+str(todayVibration))
            
            Today = PreDate+datetime.timedelta(days=1)
            res = astrategy.SellNow(asymbol, Today.strftime('%Y-%m-%d'),beTesting=False)
            if res[0]:
                print('Sell '+asymbol)
            print('===============================================================\n\n')
            
from StrategyExitVariation import Holding                                    
if __name__=='__main__':
    
    Step=''
    BigLists = PrepareData.GetBigCompany("../data/BigCompany.txt")
    EndDateStr = '2018-01-12'
    Step='Buy'
    if Step=='Buy':
        #EndDate = datetime.date.today()
        #EndDateStr = EndDate.strftime('%Y-%m-%d')
        
        print( EndDateStr)
        GetBuyListToday(EndDateStr,BigLists)
    
    Step='Sell'
    if Step=='Sell':
        print('=================Sell list=================')
        #EndDate = datetime.date.today()
        #EndDateStr = EndDate.strftime('%Y-%m-%d')
        print (EndDateStr)
        GetSellListToday(EndDateStr,BigLists)
        
    Step = 'SellOrNot'
    if Step=='SellOrNot':
        #SellDate = EndDate-datetime.timedelta(days=1)
        #EndDateStr = SellDate.strftime('%Y-%m-%d')
        
        print (EndDateStr)
        CurrentList = {}
        ratio = 1.36
        '''CurrentList['TSLA'] = [Holding(314.89,10,'2017-07-10',924.72/ratio,308.00)]
        CurrentList['FB'] = [Holding(156.91,14,'2017-07-12',314.53/ratio,148.43)]
        CurrentList['NVDA'] = [Holding(164.23,44,'2017-07-13',1003.84/ratio,152.00)]  
        
        CurrentList['CCL'] = [Holding(67.21,50,'2017-07-18',456.69/ratio,65.00)]
        CurrentList['GILD'] = [Holding(73.44,33,'2017-07-20',329.52/ratio,70.0)]
        CurrentList['DOV'] = [Holding(83.76,30,'2017-07-20',338.87/ratio,80.0)]
        CurrentList['UNH'] = [Holding(190.8,15,'2017-07-20',390.34/ratio,183.0)]
        CurrentList['MS'] = [Holding(47.14,56,'2017-07-20',357.58/ratio,44.5)]
        CurrentList['PVH'] = [Holding(117.36,20,'2017-07-21',316.86/ratio,110.0)]
        CurrentList['HON'] = [Holding(136.9,25,'2017-07-25',465.9/ratio,132.0)]
        CurrentList['KMX'] = [Holding(66.83,40,'2017-07-27',363.32/ratio,63.5)]
        CurrentList['V'] = [Holding(99.43,30,'2017-07-28',362.08/ratio,95.7)]
        CurrentList['PYPL'] = [Holding(60.35,45,'2017-07-28',362.08/ratio,57)]'''
        CurrentList['INTC'] = [Holding(45.58,35,'2017-12-19',217.98/ratio,42.5)]
        CurrentList['F'] = [Holding(12.74,150,'2017-12-19',257.43/ratio,12.35)]
        CurrentList['ABBV'] = [Holding(99.12,15,'2017-12-19',198.51/ratio,94)]
        ShallSellToday(EndDateStr, BigLists,CurrentList)
        #EndDateStr = '2017-07-31'
        ShallSellTodayVibration(EndDateStr,BigLists,CurrentList)
        