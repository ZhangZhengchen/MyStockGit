'''
Created on 2017 6 19

@author: Yali
'''
from MyDBSimulation import SimulationBaseClass,BuyAllTimeHigh
import datetime
from Predict import MyPredictDB
import collections
from data import PrepareData
from datetime import timedelta

class BuyAllTimeHighWitList(BuyAllTimeHigh):
    def __init__(self,InitMoney,StartDate,EndDate,AllTimeHighPeriod=200,DownPercent = 0.5,StockList = []):
        '''
        @param AllTimeHighPeriod: one year all time high or one month all time high? the unit is days
        @param DownPercent: must >0 and <1 
        '''
        SimulationBaseClass.__init__(self, InitMoney, StartDate, EndDate)
        self.DownPercent = DownPercent
        self.AllList = StockList
        # Get all data
        theStartDate = datetime.datetime.strptime(self.StartDate,'%Y-%m-%d').date()
        theEndDate = datetime.datetime.strptime(self.EndDate,'%Y-%m-%d').date()
        totalPeriod = (theEndDate-theStartDate).days
        print("Getting all data")
        self.AllData = MyPredictDB.GetAllDataFromAList(self.AllList,EndDate,AllTimeHighPeriod+totalPeriod)
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
    
    def ShouldBeSellNow(self,Symbol,aDate,LastBuyDay,BuyPrice): 
        '''
        If the price is lower than 3% of the buying price, sell it
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
        maxPriceSinceBuy = BuyPrice
        LastBuyDayDate= datetime.datetime.strptime(LastBuyDay,'%Y-%m-%d').date()
        i = -1
        while TheDatas[0][i]<=LastBuyDayDate:
            i-=1
        
        # the highest close price
        while TheDatas[0][i]<aDateDate:
            if TheDatas[2][i]>maxPriceSinceBuy:
                maxPriceSinceBuy=TheDatas[2][i]
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
        if TheDatas[2][i+1]<maxPriceSinceBuy*(1-self.DownPercent):
            return [True,TheDatas[1][i]]
        else:
            return [False,0.0]
if __name__=='__main__':
    BigLists=PrepareData.GetBigCompany("../data/BigCompany.txt")
    '''for i in [100,120,140,160,180]:
        astrategy = BuyAllTimeHighWitList(6000,'2017-01-04','2017-06-22',i,0.05,BigLists)
        astrategy.RunAStrategy()
        print 'i==='+str(i)
        print '=====================================\n\n\n'
    '''
    
    BigLists=PrepareData.GetBigCompany("../data/BigCompany.txt")
    EndDate = '2017-06-22'
    astrategy = BuyAllTimeHighWitList(6000,'2017-01-04',EndDate,140,0.03,BigLists)
    #astrategy.RunAStrategy()
    res = astrategy.GetBuyList(EndDate)
    
    #res = astrategy.ShouldBeSellNow('AAPL', '2017-06-15', '2017-05-03', 146)
    print res
    