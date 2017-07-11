'''
Created on 2017 6 19 

@author: Yali
'''
def SortBigComanyList(input,output):
    f = open(input)
    alldata = f.readlines()
    f.close()
    
    removeRepeat = []
    for anitem in alldata:
        anitem = anitem.strip()
        if len(anitem)==0:
            continue
        if not anitem in removeRepeat:
            removeRepeat.append(anitem)
    
    sortedall = sorted(removeRepeat)
    
    f = open(output,'w')
    for anitem in sortedall:
        f.write(anitem+'\n')
    f.close()

def GetBigCompany(InputFile):
    Big = []
    f = open(InputFile)
    for aline in f:
        aline = aline.strip()
        Big.append(aline)
    f.close()
    return Big

def SectorsToALL():
    XLB=GetBigCompany("../data/XLB.txt")
    XLE=GetBigCompany("../data/XLE.txt")
    XLF=GetBigCompany("../data/XLF.txt")
    XLI=GetBigCompany("../data/XLI.txt")
    XLK=GetBigCompany("../data/XLK.txt")
    XLP=GetBigCompany("../data/XLP.txt")
    XLU=GetBigCompany("../data/XLU.txt")
    XLV=GetBigCompany("../data/XLV.txt")
    XLY=GetBigCompany("../data/XLY.txt")
    
    AllLists = [XLB,XLE,XLF,XLI,XLK,XLP,XLU,XLV,XLY]
    BigLists = []
    for anitem in AllLists:
        for aname in anitem:
            if not aname in BigLists:
                BigLists.append(aname)
    BigLists = sorted(BigLists)
    f = open('./BigCompany.txt','w')
    for anitem in BigLists:
        f.write(anitem+'\n')
    f.close()
            
if __name__=='__main__':
    '''inputfile = './BigCompany.txt'
    output = inputfile
    SortBigComanyList(inputfile, output)'''
    
    SectorsToALL()