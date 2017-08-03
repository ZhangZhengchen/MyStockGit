'''
Created on 2017 7 12

@author: Yali
'''
import datetime
from StrategyVolumeChangeExitStandard import VolumeChangeExistLow,SellAllTimeLow
import numpy
from data import PrepareData
import collections
from StrategyExitVariation import BuyATHExitBigVibration

def GetBuyListToday(EndDate,BigLists):
    PreDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d')
    PreDate -= datetime.timedelta(days=1)
    for i in [90,100,120,150]:
        j = 10
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),i,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(7000,'2017-01-04',PreDate.strftime('%Y-%m-%d'),i,j,BigLists,40,8)
        #astrategy.RunAStrategy()
        res = astrategy.GetBuyListNow(EndDate)
        #res = astrategy.ShouldBeSellNow('AAPL', '2017-06-15', '2017-05-03', 146)
        print res
        
def ShallSellToday(EndDate,BigLists,SymbolList):
    '''
    EndDate is the last closing day.
    Because normally when I check shall I sell them, today is not closed yet.
    '''
    for j in [30]:
        startindex = -1
        TheDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d').date()
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',EndDate,100,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(5000,'2017-01-04',EndDate,100,j,BigLists,1)
        for asymbol in SymbolList:
            if not asymbol in astrategy.AllData:
                print('No symbol '+asymbol)
                continue
            TheData = astrategy.AllData[asymbol]
            if startindex==-1:
                if not TheDate in TheData[0]:
                    return
                
                for i in range(len(TheData[0])):
                    if TheData[0][i]==TheDate:
                        startindex = i
                        break
            LowestValue = numpy.min(TheData[2][startindex+1:startindex+j+1])
            if TheData[2][startindex]<LowestValue:
                print 'SELL '+asymbol+'. Last close price is '+str(TheData[2][startindex])
            else:
                print 'Don\'t sell ' +asymbol+'. Last close price is '+str(TheData[2][startindex])
            #print astrategy.SellNow(asymbol, EndDate)
            print 'The Lowest value is '+str(LowestValue)+'. It should be your stop loss price\n\n\n'
            

def ShallSellTodayVibration(EndDate,BigLists,CurrentList):
    '''
    EndDate is the last closing day.
    Because normally when I check shall I sell them, today is not closed yet.
    '''
    for j in [10,30]:
        startindex = -1
        TheDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d').date()
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',EndDate,100,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(7000,'2017-01-04',EndDate,100,j,BigLists,8)
        astrategy.CurrentList = CurrentList
        for asymbol in astrategy.CurrentList:
            if not asymbol in astrategy.AllData:
                print('No symbol '+asymbol)
                continue
            TheData = astrategy.AllData[asymbol]
            if startindex==-1:
                if not TheDate in TheData[0]:
                    return
                
                for i in range(len(TheData[0])):
                    if TheData[0][i]==TheDate:
                        startindex = i
                        break
            meanVibration = numpy.mean(numpy.abs(numpy.array(TheData[3][startindex+1:startindex+j+1])-numpy.array(TheData[4][startindex+1:startindex+j+1])))
            todayVibration = TheData[3][startindex] - TheData[4][startindex]
            if todayVibration>astrategy.VibrationRatio*meanVibration and TheData[1][startindex]>TheData[2][startindex]:
                print 'SELL '+asymbol+'. Mean vibration is '+str(meanVibration)+'. Today vibration is '+str(todayVibration)
            else:
                print 'Don\'t sell ' +asymbol+'. Mean vibration is '+str(meanVibration)+'. Today vibration is '+str(todayVibration)
            
            Today = TheDate+datetime.timedelta(days=1)
            res = astrategy.SellNow(asymbol, Today.strftime('%Y-%m-%d'),beTesting=False)
            if res[0]:
                print('Sell '+asymbol)
            print('===============================================================\n\n')
            
from StrategyExitVariation import Holding                                    
if __name__=='__main__':
    
    Step=''
    BigLists = PrepareData.GetBigCompany("../data/BigCompany.txt")
    Step='Buy'
    if Step=='Buy':
        #EndDate = datetime.date.today()
        #EndDateStr = EndDate.strftime('%Y-%m-%d')
        EndDateStr = '2017-08-03'
        print EndDateStr
        GetBuyListToday(EndDateStr,BigLists)
        
    Step = 'SellOrNot'
    if Step=='SellOrNot':
        #SellDate = EndDate-datetime.timedelta(days=1)
        #EndDateStr = SellDate.strftime('%Y-%m-%d')
        
        print EndDateStr
        CurrentList = {}
        ratio = 1.36
        CurrentList['TSLA'] = [Holding(314.89,10,'2017-07-10',924.72/ratio,308.00)]
        CurrentList['FB'] = [Holding(156.91,14,'2017-07-12',314.53/ratio,148.43)]
        CurrentList['NVDA'] = [Holding(164.23,44,'2017-07-13',1003.84/ratio,152.00)]  
        CurrentList['BA'] = [Holding(209.32,25,'2017-07-17',720.51/ratio,205.0)]
        CurrentList['CCL'] = [Holding(67.21,50,'2017-07-18',456.69/ratio,65.00)]
        CurrentList['GILD'] = [Holding(73.44,33,'2017-07-20',329.52/ratio,70.0)]
        CurrentList['DOV'] = [Holding(83.76,30,'2017-07-20',338.87/ratio,80.0)]
        CurrentList['UNH'] = [Holding(190.8,15,'2017-07-20',390.34/ratio,183.0)]
        CurrentList['MS'] = [Holding(47.14,56,'2017-07-20',357.58/ratio,44.5)]
        CurrentList['PVH'] = [Holding(117.36,20,'2017-07-21',316.86/ratio,110.0)]
        CurrentList['HON'] = [Holding(136.9,25,'2017-07-25',465.9/ratio,132.0)]
        CurrentList['KMX'] = [Holding(66.83,40,'2017-07-27',363.32/ratio,63.5)]
        CurrentList['V'] = [Holding(99.43,30,'2017-07-28',362.08/ratio,95.7)]
        CurrentList['PYPL'] = [Holding(60.35,45,'2017-07-28',362.08/ratio,57)]
        CurrentList['NEE'] = [Holding(146.95,22,'2017-08-02',438.86/ratio,141.2)]
        CurrentList['HBI'] = [Holding(23.84,90,'2017-08-04',582.73/ratio,22.3)]
        EndDateStr = '2017-08-02'
        ShallSellToday(EndDateStr, BigLists,CurrentList)
        #EndDateStr = '2017-07-31'
        ShallSellTodayVibration(EndDateStr,BigLists,CurrentList)
        