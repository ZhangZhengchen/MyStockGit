'''

@author: Yali
'''
import numpy as np
import datetime
from datetime import timedelta
import collections
import copy

class Condition(object):
    '''
    classdocs
    '''
    @staticmethod
    def strarr2floatarr(input):
        output=[]
        for ac in input:
            output.append(float(ac))
        return output
    '''
    The inputs are all in string format
    '''
    def __init__(self, thehis):
        '''
        Constructor
        thehis is a dictionary
        {'AAPL',[daily price,detail in a day]}
        daily price:dates, opens, closes, maxs, mins, volumns
        detail in a day:{datetime,[opens, maxs, mins, closes, volumns]}
        '''
        self.dates = []
        daily = thehis[0]
        for ad in daily[0]:
            #print ad
            self.dates.append(datetime.datetime.strptime(ad,'%Y-%m-%d'))
        self.prices = self.GetPrices(thehis)
        # cannot move this line before self.GetPrices()
        self.dates.sort()
        self.AllFluctuate = {}
        for adate,aprice in self.prices.iteritems():
            self.AllFluctuate[adate]=aprice[2]-aprice[3]
        self.AllFluctuate = collections.OrderedDict(sorted(self.AllFluctuate.items()))   
        self.isup = self.IsUp(1)
        self.isfluctuateup = self.IsFluctuateIncrease(2)
        self.isclosehigh = self.IsCloseHigh()
        self.iscontinueup = self.IsContinueUp() 
        self.isvup = self.IsVolumnUp()
        self.ma5 = self.GetSimpleMA(5)
        self.ma10 = self.GetSimpleMA(10)
        self.ma20 = self.GetSimpleMA(20)
        self.ismagood = self.IsMAGood()
        self.ismabad = self.IsMABad()
        self.lasthigh = self.GetLastHigh(60)
    
    def IsMAGood(self):
        isgood = {}
        if (len(self.ma20)==0):
            self.ma20 = self.GetSimpleMA(20)
        if (len(self.ma10)==0):
            self.ma10 = self.GetSimpleMA(10)
        if (len(self.ma5)==0):
            self.ma5 = self.GetSimpleMA(5)
        
        for adate in self.prices.keys():
            theclose = self.prices[adate][1]
            thema5 = self.ma5[adate]
            thema10 = self.ma10[adate]
            if theclose>thema10 and thema5>thema10 and thema10>self.ma20[adate]:
                isgood[adate] = 1-np.abs(self.prices[adate][0]-thema5)/(self.prices[adate][0]+thema5)
            else:
                isgood[adate] = 0
        return isgood
    
    def IsMABad(self):
        isbad = {}
        if (len(self.ma10)==0):
            self.ma10 = self.GetSimpleMA(10)
        if (len(self.ma5)==0):
            self.ma5 = self.GetSimpleMA(5)
        for adate in self.prices.keys():
            theclose = self.prices[adate][1]
            thema5 = self.ma5[adate]
            thema10 = self.ma10[adate]
            if theclose<thema5:
                isbad[adate] = 1
            else:
                isbad[adate] = 0
        return isbad
        
    def GetSimpleMA(self,window):
        ma = {}
        allcloseprice = []
        for thedate,theprice in self.prices.iteritems():
            allcloseprice.append(theprice[1])
        if len(allcloseprice)==0:
            return {}
        thevalue = Condition.movingaverage(allcloseprice, window)
        i=0
        for thedate, theprice in self.prices.iteritems():
            ma[thedate] = thevalue[i]
            i+=1  
        return ma
    
    def GetPrices(self,thehis):
        '''
        closep, highp, lowp, openp ===>
        open close high low
        '''
        theprices={}
        for i in range(len(self.dates)):
            theprices[self.dates[i]]=[float(thehis[0][4][i]),float(thehis[0][1][i]),
                                      float(thehis[0][2][i]),float(thehis[0][3][i]),float(thehis[0][5][i])]
        return collections.OrderedDict(sorted(theprices.items()))
    
    def IsUp(self,daterange):
        isup = {}
        for i in range(len(self.prices.keys())):
            thedate = self.prices.keys()[i]
            if i-daterange<0:
                isup[thedate]=0
            else:
                isup[thedate]=(self.prices[thedate][1]-self.prices.values()[i-daterange][1])/self.prices.values()[i-daterange][1]
        return isup
    
    def IsFluctuateIncrease(self, daterange, multip=1.8):
        AllAverage = {}
        for i in range(len(self.AllFluctuate.keys())):
            if i-daterange<0:
                AllAverage[self.AllFluctuate.keys()[i]] = 1e5
            else:
                theaverage = np.mean(self.AllFluctuate.values()[i-daterange:i-1])
                if theaverage<1e-5:
                    theaverage = 1e-3
                AllAverage[self.AllFluctuate.keys()[i]] = theaverage
        IsIncrease = {}
        for i in range(len(self.AllFluctuate.keys())):
            thedate = self.AllFluctuate.keys()[i]
            if i-daterange<0:
                IsIncrease[thedate]=0
            else:
                IsIncrease[thedate] = self.AllFluctuate[thedate]/AllAverage[thedate]
        return IsIncrease
    
    def IsCloseHigh(self,perce=0.65):
        IsHigh={}
        for adate, aprice in self.prices.iteritems():
            if aprice[2]-aprice[3]>0.01:
                IsHigh[adate] = (aprice[1]-aprice[3])/(aprice[2]-aprice[3])
            else:
                IsHigh[adate] = 0
        return IsHigh
    
    @staticmethod
    def movingaverage(values,window):
        weigths = np.repeat(1.0, window)/window
        smas = np.convolve(values, weigths, 'valid')
        smas = np.append([np.max(values) for i in range(window-1)],smas)
        return smas # as a numpy array
    
    @staticmethod
    def mymovingaverage(values,window):
        if window>len(values):
            return values
        
        if window<=0:
            return values
        
        smas = []
        for i in range(window-1):
            smas.append(float(values[i]))
        if smas[-1]==0 and len(smas)>1:
            smas[-1] = smas[-2]
        
        i = window-1
        smas.append(float(np.sum(values[0:i]))/float(window))
        if smas[-1]==0 and len(smas)>1:
            smas[-1] = smas[-2]
        for i in range(window,len(values)):
            smas.append((smas[i-1]*window-float(values[i-window])+float(values[i]))/float(window))
            if smas[-1]==0 and len(smas)>1:
                smas[-1] = smas[-2]
        
        
        return smas
    
    @staticmethod
    def myrsiFunc(prices, n=13):
        if n>len(prices):
            return np.zeros(len(prices))
        
        if n<=0:
            return np.zeros(len(prices))
        
        preprices = copy.copy(prices)
        preprices.insert(0,prices[0])
        preprices = preprices[0:len(preprices)-1]
        
        deltas = np.subtract(prices,preprices)
        seed = deltas[0:n+1]
        up = seed[seed>=0].sum()
        down = -1*seed[seed<0].sum()+0.00001
        rs = up/down
        rsi = np.zeros(len(prices))
        rsi[:n] = 100.-100./(1.+rs)
        for i in range(n, len(prices)):
            delta = deltas[i-1] # cause the diff is 1 shorter
            last = deltas[i-n]
            if last>0:
                up = up - last
            else:
                down = down + last
            
            if delta>0:
                up = up + delta
            else:
                down = down - delta
    
            rs = up/(down+0.00001)
            rsi[i] = 100. - 100./(1.+rs)
    
        return rsi
    @staticmethod
    def rsiFunc(prices, n=13):
        deltas = np.diff(prices)
        seed = deltas[:n+1]
        up = seed[seed>=0].sum()/n
        down = -seed[seed<0].sum()/n
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:n] = 100. - 100./(1.+rs)
    
        for i in range(n, len(prices)):
            delta = deltas[i-1] # cause the diff is 1 shorter
    
            if delta>0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta
    
            up = (up*(n-1) + upval)/n
            down = (down*(n-1) + downval)/n
    
            rs = up/(down+0.000001)
            rsi[i] = 100. - 100./(1.+rs)
    
        return rsi
    
    def GetLastHigh(self,dayrange=60):
        lasthigh = {}
        maxprice = 0
        dates = self.prices.keys()
        for i in range(np.min([dayrange,len(dates)])):
            lasthigh[dates[i]] = 0
        for i in range(dayrange,len(dates)):
            maxprice = 0
            for j in range(1,dayrange):
                if self.prices[dates[i-j]][1]>maxprice:
                    maxprice = self.prices[dates[i-j]][1]
            if self.prices[dates[i]][1]>maxprice:
                lasthigh[dates[i]] = 1
        return lasthigh
    
    def IsContinueUp(self):
        isup = {}
        thevalues = self.prices.values()
        for i in range(len(self.prices.keys())):
            thedate = self.prices.keys()[i]
            if i-3<0:
                isup[thedate]=0
            else:
                if (self.prices[thedate][1]>thevalues[i-1][1] #close high
                    and thevalues[i][1]>thevalues[i][0] #increase today
                    #and thevalues[i][2]>thevalues[i-1][2] # maximum high
                    and thevalues[i][3]>thevalues[i-1][3]): # minimum high
                    if (thevalues[i-1][1]>thevalues[i-2][1] #close high
                        and thevalues[i-1][1]>thevalues[i-1][0] #increase in i-1
                        #and thevalues[i-1][2]>thevalues[i-2][2] # maximum high
                        and thevalues[i-1][3]>thevalues[i-2][3]): # minimum high
                        isup[thedate]=7# 3 days up
                        if thevalues[i-2][1]<thevalues[i-2][0]:#decrease at i-2
                            isup[thedate] = 8
                    else:
                        if (thevalues[i][1]>thevalues[i-2][1] and thevalues[i][1]>thevalues[i][0]
                            and thevalues[i-2][1]>thevalues[i-3][1] and thevalues[i-2][1]>thevalues[i-2][0]):
                            isup[thedate] = 0
                        else:
                            isup[thedate] = 0
                elif (self.prices[thedate][1]>thevalues[i-2][1] and thevalues[i][1]>thevalues[i][0] 
                      and thevalues[i-2][1]>thevalues[i-3][1] and thevalues[i-2][1]>thevalues[i-2][0]):
                    isup[thedate]=0   
                else:
                    isup[thedate]=0
                '''
                we don't buy stocks with price < 0.1 SGD
                '''
                if self.prices[thedate][0]<0.1:
                    isup[thedate]=0
        return isup
    
    def IsVolumnUp(self,daterange=4):
        AllAverage = {}
        alldate = self.prices.keys()
        for i in range(len(alldate)):
            if i==0:
                AllAverage[alldate[i]] = self.prices[alldate[i]][4]
            elif i-daterange<0:
                temp = 0
                total = 0
                while i-temp-1>=0:
                    total += self.prices[alldate[i-temp-1]][4]
                    temp += 1
                AllAverage[alldate[i]] = total/temp
            else:
                temp = 0
                total = 0
                while temp<daterange:
                    total += self.prices[alldate[i-temp-1]][4]
                    temp += 1
                AllAverage[alldate[i]] = total/temp
        IsIncrease = {}
        for i in range(len(self.prices.keys())):
            thedate = self.prices.keys()[i]
            if i-daterange<0:
                IsIncrease[thedate]=0
            else:
                if AllAverage[thedate]<1:
                    IsIncrease[thedate]=-1000
                else:
                    IsIncrease[thedate] = self.prices[thedate][4]/AllAverage[thedate]
        return IsIncrease
  