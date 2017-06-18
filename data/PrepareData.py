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
        
if __name__=='__main__':
    inputfile = './BigCompany.txt'
    output = inputfile
    SortBigComanyList(inputfile, output)