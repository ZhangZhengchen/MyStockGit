'''
Created on 2017 7 10

@author: Yali
'''
import math
from Predict.FundamentalStudy import TotalNumber

def CalculatePositionSize(TotalMoney,BuyPrice,StopLoss,RiskRatio,Charge=30):
    '''
    '''
    LoseEach = BuyPrice-StopLoss
    TotalLose = TotalMoney*RiskRatio-Charge
    if LoseEach>0:
        return math.floor(TotalLose/LoseEach)
    else:
        return 0
    

if __name__=='__main__':
    TotalMoney = 5000
    BuyPrice = 91.0
    StopLoss = 88.0
    RiskRatio = 0.025
    res = CalculatePositionSize(TotalMoney, BuyPrice, StopLoss, RiskRatio)
    print res
    