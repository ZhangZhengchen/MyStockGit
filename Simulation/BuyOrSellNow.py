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
        
def ShallSellToday(EndDate,SymbolList,BigLists):
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
            print astrategy.SellNow(asymbol, EndDate)
            print 'The Lowest value is '+str(LowestValue)+'. It should be your stop loss price\n\n\n'
            

def ShallSellTodayVibration(EndDate,SymbolList,BigLists):
    '''
    EndDate is the last closing day.
    Because normally when I check shall I sell them, today is not closed yet.
    '''
    for j in [10,30]:
        startindex = -1
        TheDate = datetime.datetime.strptime(EndDate,'%Y-%m-%d').date()
        #astrategy = VolumeChangeExistLow(5000,'2017-01-04',EndDate,100,j,BigLists,3)
        astrategy = BuyATHExitBigVibration(5000,'2017-01-04',EndDate,100,j,BigLists,1)
        for asymbol in SymbolList:
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
            if -1*todayVibration>astrategy.VibrationRatio*meanVibration:
                print 'SELL '+asymbol+'. Mean vibration is '+str(meanVibration)+'. Today vibration is '+str(todayVibration)
            else:
                print 'Don\'t sell ' +asymbol+'. Mean vibration is '+str(meanVibration)+'. Today vibration is '+str(todayVibration)
            print astrategy.SellNow(asymbol, EndDate)
            print('\n\n')
            
                                    
if __name__=='__main__':
    
    Step=''
    BigLists = PrepareData.GetBigCompany("../data/BigCompany.txt")
    Step='Buy'
    if Step=='Buy':
        #EndDate = datetime.date.today()
        #EndDateStr = EndDate.strftime('%Y-%m-%d')
        EndDateStr = '2017-07-22'
        print EndDateStr
        GetBuyListToday(EndDateStr,BigLists)
        
    Step = 'SellOrNot'
    if Step=='SellOrNot':
        #SellDate = EndDate-datetime.timedelta(days=1)
        #EndDateStr = SellDate.strftime('%Y-%m-%d')
        EndDateStr = '2017-07-21'
        print EndDateStr
        Symbols = ['NVDA','CCL','AVY','TSLA','FB','BA','GILD','DOV','UNH','MS','JNJ','PVH']
        ShallSellToday(EndDateStr, Symbols, BigLists)
        ShallSellTodayVibration(EndDateStr,Symbols,BigLists)
        