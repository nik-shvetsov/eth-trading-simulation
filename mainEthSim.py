import warnings
warnings.filterwarnings("ignore")
import seaborn

import time
import house
import sp
from utils import generateAdresses, buildGraph, buildSmoothXY

import matplotlib.pyplot as plt
import numpy as np
import math
import random as rnd
from collections import defaultdict

from populus.project import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3

class Simulation(object):
    def __init__(self, sp, simdays, typeAuc, eTokenContract, eMarketContract):
        self.sp = sp
        #self.houseList = None
        #self.rulerList = None
        #self.addresses = addresses
        self.eTokenC = eTokenContract
        self.eMarketC = eMarketContract


        self.hour = 0
        self.current_day = 1

        self.avgWindow = 5
        self.decayFactor = 0.99
        self.hourDecay = 23
        
        #(cons, prod)
        self.weatherType = {'clowds': (1.0, 0.8), 'rain': (1.3, 0.2), 'sun': (0.95, 1.3)} #weatherType = {'sun': (1.5), 'rain': (0.2), 'clowds': (1.0)}
        self.wKeyProb = [0.45, 0.15, 0.40]
        self.keysW = self.weatherType.keys()
        self.keysW.sort()
        
        self.divNum = 100 #min energy value
        self.priceRange = [2,3,4,5,6]
        self.batteryTH = 0.1
        self.auctionType = typeAuc # 'simple' , 'loyal'

        #self.consumeMidRange = [4,12]
        #self.rulerCap = 15000.0 #500_000 Wh
        #self.num_of_households = 8 #9 +1 sc

        #self.initEnergy = 8000 # 8 kWh
        #self.maxEnergyDiv = 80 #init max energy / 100
        #self.initCoins = 20000

        self.days_to_sim = simdays #140

        self.graph_data_batteryBalance = defaultdict(list) #data for graphs #{address:consumption_time_print}
        self.graph_data_consumption = defaultdict(list)
        self.graph_data_production = defaultdict(list)
        self.graph_data_coins = defaultdict(list)
        self.graph_data_money = defaultdict(list)
        # cumulative
        self.graph_data_consumptionC = defaultdict(list)
        self.graph_data_productionC = defaultdict(list)
        self.graph_data_coinsC = defaultdict(list)
        self.graph_data_moneyC = defaultdict(list)


    def checkCoinBalance(self, address):
        print("Coin balance of {0} is {1}".format(address, self.eTokenC.call().balanceOf(address)))
        #return (address, eTokenC.call().balanceOf(address))

    def checkEnergyBalance(self, address):
        print("Energy balance of {0} is {1}".format(address, self.eMarketC.call({"from":address}).getEnergyBalance()))
        #return (address, eMarketC.call({"from":address}).getEnergyBalance())

    def roundToWh(self, amount):
        if (amount % self.divNum) == 0:
            newamount = amount
        else:
            newamount = amount - (amount % self.divNum)
        return int(newamount)


    def performDecay(self):
        if self.hour == self.hourDecay:
            for key in self.sp.Qtable:
                self.sp.Qtable[key] *= self.decayFactor


    def getCoinBalance(self, address):
        #return (address, eTokenC.call().balanceOf(address))
        return self.eTokenC.call().balanceOf(address)
        #for x in self.sp.households:
            #if x.address == address:
                #return x.ruler.tokenBalance


    def getEnergyBalance(self, address):
        #return (address, eMarketC.call({"from":address}).getEnergyBalance())
        return self.eMarketC.call({"from":address}).getEnergyBalance()
        #for x in self.sp.households:
            #if x.address == address:
                #return x.ruler.batteryBalance


    def getMoneyBalance(self, address):
        return int (self.eMarketC.call({"from":address}).getMoneyBalance())
        #for x in self.sp.households:
            #if x.address == address:
                #return x.ruler.moneyBalance

    def getEnergyConsumption(self, address):
        return self.eMarketC.call({"from":address}).getEnergyConsumption()
        #for x in self.sp.households:
            #if x.address == address:
                #return x.ruler.consumtion

    def getEnergyProduction(self, address):
        return self.eMarketC.call({"from":address}).getEnergyProduction()
        #for x in self.sp.households:
            #if x.address == address:
                #return x.ruler.production

    def getRates(self):
        in_rate = self.eMarketC.call().getRate()
        out_rate = self.eMarketC.call().getOuterRate()
        return (in_rate, out_rate)
        #return (self.sp.rate, self.sp.outer_rate)

    def setRates(self, whRate, out_whRate):
        txhash = self.eMarketC.transact().setRate(whRate)
        chain.wait.for_receipt(txhash)

        txhash = self.eMarketC.transact().setOuterRate(out_whRate)
        chain.wait.for_receipt(txhash)
        #self.sp.rate = whRate
        #self.sp.outer_rate = out_whRate

    def setPrices(self, newSellPrice, newBuyPrice):
        txhash = self.eTokenC.transact().setPrices(newSellPrice, newBuyPrice)
        chain.wait.for_receipt(txhash)
        #self.sp.buyPrice = newBuyPrice
        #self.sp.sellPrice = newSellPrice

    def buyCoins(self, receiver, amount):
        #txhash = eTokenC.transact({"from":address}).buy(amount)
        #chain.wait.for_receipt(txhash)

        #need buy rate
        buy_rate = self.eTokenC.call().buyPrice()

        txhash = self.eMarketC.transact().transactMoney(receiver, self.sp.address, amount*buy_rate)
        check = chain.wait.for_receipt(txhash)

        txhash = self.eMarketC.transact().sendCoin(self.eTokenC.address, self.sp.address, receiver, amount)
        check = chain.wait.for_receipt(txhash)
        #-------
        #buy_rate = self.sp.buyPrice
        #for x in self.sp.households:
            #if x.address == receiver:
                #money = amount*buy_rate
                #x.ruler.moneyBalance -= int(money)
                #self.sp.moneyBalance += int(money)
                #self.sp.tokenStorage -= amount
                #x.ruler.tokenBalance += amount

    def sellCoins(self, seller, amount):
        #txhash = eTokenC.transact({"from":address}).sell(amount)
        #chain.wait.for_receipt(txhash)

        #need sell rate
        sell_rate = self.eTokenC.call().sellPrice()

        txhash = self.eMarketC.transact().transactMoney(self.sp.address, seller, amount*sell_rate)
        check = chain.wait.for_receipt(txhash)

        txhash = self.eMarketC.transact().sendCoin(self.eTokenC.address, seller, self.sp.address, amount)
        check = chain.wait.for_receipt(txhash)

        #-----------
        #sell_rate = self.sp.sellPrice
        #for x in self.sp.households:
            #if x.address == seller:
                #money = amount*sell_rate
                #x.ruler.tokenBalance -= amount
                #self.sp.tokenStorage += amount
                
                #self.sp.moneyBalance -= int(money)
                #x.ruler.moneyBalance += int(money)

    def addCoinsAdm(self, receiver, numcoins):
        txhash = self.eTokenC.transact().mintToken(receiver, numcoins)
        chain.wait.for_receipt(txhash)
        #for x in self.sp.households:
            #if x.address == receiver:
                #x.ruler.tokenBalance += numcoins
    
    def transferCoins(self, sender, receiver, numcoins):
        txhash = self.eTokenC.transact().transfer(sender, receiver, numcoins)
        chain.wait.for_receipt(txhash)
        #for x in self.sp.households:
            #if x.address == receiver:
                #for y in self.sp.households:
                    #if y.address == sender:
                        #y.ruler.tokenBalance -= numcoins
                        #x.ruler.tokenBalance += numcoins

    def sendCoins(self, sender, receiver, numcoins):
        txhash = self.eMarketC.transact().sendCoin(self.eTokenC.address, sender, receiver, numcoins)
        check = chain.wait.for_receipt(txhash)
        #for x in self.sp.households:
            #if x.address == receiver:
                #for y in self.sp.households:
                    #if y.address == sender:
                        #y.ruler.tokenBalance -= numcoins
                        #x.ruler.tokenBalance += numcoins


    def buyEnergy(self, buyer, seller, energy, rate):
        txhash = self.eMarketC.transact({"from":buyer}).buyEnergy(self.eTokenC.address, seller, energy, rate)
        chain.wait.for_receipt(txhash)
        #-------------
        #for x in self.sp.households:
            #if x.address == buyer:
                #for y in self.sp.households:
                    #if y.address == seller:
                        #coins = (energy * (rate))
                        #x.ruler.tokenBalance -= coins
                        #y.ruler.tokenBalance += coins
                        #x.ruler.batteryBalance += energy
                        #y.ruler.batteryBalance -= energy

    def produceEnergy(self, address, energy):
        txhash = self.eMarketC.transact({"from":address}).produceEnergy(energy)
        chain.wait.for_receipt(txhash)
        self.sp.totalSolarEnergy += energy
        #-----------
        #for x in self.sp.households:
            #if x.address == address:
                #x.ruler.production += energy
                #x.ruler.batteryBalance += energy
                #self.sp.totalSolarEnergy += energy

    def consumeEnergy(self, address, energy):
        txhash = self.eMarketC.transact({"from":address}).consumeEnergy(energy)
        chain.wait.for_receipt(txhash)
        #----------
        #for x in self.sp.households:
            #if x.address == address:
                #x.ruler.batteryBalance -= energy
                #x.ruler.consumption += energy

    def buyFromOuterGrid(self, address, Wh):
        txhash = self.eMarketC.transact().buyFromOuterGrid(address, Wh)
        chain.wait.for_receipt(txhash)
        self.sp.totalOuterGrid += Wh
        #print ("Buying from outer grid {0}wh, to {1}".format(Wh, address))
        #---------
        #for x in self.sp.households:
            #if x.address == address:
                #x.ruler.batteryBalance += Wh
                #money = int(Wh * (self.sp.outer_rate)) # *10
                #x.ruler.moneyBalance -= money
                #self.sp.totalOuterGrid += Wh
                 
    def sellToOuterGrid(self, address, Wh):
        txhash = self.eMarketC.transact().sellToOuterGrid(address, Wh)
        chain.wait.for_receipt(txhash)
        #print ("Selling to outer grid {0}wh, from {1}".format(Wh, address))
        #---------
        #for x in self.sp.households:
            #if x.address == address:
                #x.ruler.batteryBalance -= Wh
                #money = int(Wh * (self.sp.rate)) # *1
                #x.ruler.moneyBalance += money

        #print ("Selling to outer grid {0}wh, from {1}".format(Wh, address))


    def executeTransactions(self, transactionList):
        for x in transactionList:
            #[buyer, seller, amount, rate]
            self.buyEnergy(x[0], x[1], x[2], x[3])
        #------
        #for x in transactionList:
            ##[buyer, seller, amount, rate]
            #self.buyEnergy(x[0], x[1], x[2], x[3])

    def checkValidCoinBalance(self, houseAddress, amountPriceMult):
        coinBal = self.getCoinBalance(houseAddress)
        if coinBal < amountPriceMult:
            self.buyCoins(houseAddress, amountPriceMult)

    def updateInfoSContract(self):
        for x in self.sp.households:
            pass

    def priceFormationSell(self, amountMidRange, amount, qlearn, sample):
        if qlearn == False:
            formedPrice = None
            rnd.seed()

            while (formedPrice == None):
                if amount > max(amountMidRange):
                    for x in self.priceRange:
                        rnd.seed()
                        prob = rnd.uniform(0, 1)
                        betaProb = np.random.beta(4, 2)
                        if prob < betaProb:
                            #print (prob, betaProb)
                            formedPrice = x
                            break

                elif amount < min(amountMidRange):
                    for x in reversed(self.priceRange):
                        rnd.seed()
                        prob = rnd.uniform(0, 1)
                        betaProb = np.random.beta(2, 4)
                        if prob < betaProb:
                            #print(prob, betaProb)
                            formedPrice = x
                            break

                else:
                    for x in (self.priceRange):
                        rnd.seed()
                        prob = rnd.uniform(0, 1)
                        betaProb = np.random.beta(8, 8)
                        if prob < betaProb:
                            #print(prob, betaProb)
                            formedPrice = x
                            break

            return formedPrice #4
        else:
            self.sp.QtableCluster = []
            for x in self.sp.Qtable.keys():
                    self.sp.QtableCluster.append([x[0][0], x[0][1], x[0][2], x[1][0]]) #without price x[1][1]
            #print (sp.QtableCluster)

            finPrice = 0
            
            while (finPrice == 0):
                distances = []
                
                for x in self.sp.QtableCluster:
                    euc = math.sqrt(0.5*pow(x[0]-sample[0], 2) + 0.5*pow(x[1]-sample[1], 2) + 0.4*pow(x[2]-sample[2], 2) + 1.0*pow(x[3]-sample[3], 2))
                    distances.append(euc)

                indexOfClosest = distances.index(min(distances))

                record = self.sp.QtableCluster[indexOfClosest]
                #find in real Qtable this record
                for x in self.sp.Qtable.keys():
                    if (x[0][0] == record[0]) and (x[0][1] == record[1]) and (x[0][2] == record[2]) and (x[1][0] == record[3]) and (sp.Qtable[x] > 0):
                        finPrice =  x[1][1]

                self.sp.QtableCluster.pop(indexOfClosest)

            return finPrice



    def priceFormationBuy(self, amountMidRange, amount, qlearn, sample):
        if qlearn == False:
            formedPrice = None
            rnd.seed()

            while (formedPrice == None):
                if amount > max(amountMidRange):
                    for x in reversed(self.priceRange):
                        rnd.seed()
                        prob = rnd.uniform(0, 1)
                        betaProb = np.random.beta(2, 4)
                        if prob < betaProb:
                            #print (prob, betaProb)
                            formedPrice = x
                            break

                elif amount < min(amountMidRange):
                    for x in (self.priceRange):
                        rnd.seed()
                        prob = rnd.uniform(0, 1)
                        betaProb = np.random.beta(4, 2)
                        if prob < betaProb:
                            #print(prob, betaProb)
                            formedPrice = x
                            break

                else:
                    for x in reversed(self.priceRange):
                        rnd.seed()
                        prob = rnd.uniform(0, 1)
                        betaProb = np.random.beta(8, 8)
                        if prob < betaProb:
                            #print(prob, betaProb)
                            formedPrice = x
                            break

            return formedPrice #4

        else:
            self.sp.QtableCluster = []
            for x in self.sp.Qtable.keys():
                    self.sp.QtableCluster.append([x[0][0], x[0][1], x[0][2], x[1][0]]) #without price x[1][1]
            #print (sp.QtableCluster)

            finPrice = 0
            
            while (finPrice == 0):
                distances = []
                
                for x in self.sp.QtableCluster:
                    euc = math.sqrt(0.5*pow(x[0]-sample[0], 2) + 0.5*pow(x[1]-sample[1], 2) + 0.4*pow(x[2]-sample[2], 2) + 1.0*pow(x[3]-sample[3], 2))
                    distances.append(euc)

                indexOfClosest = distances.index(min(distances))

                record = self.sp.QtableCluster[indexOfClosest]
                #find in real Qtable this record
                for x in sp.Qtable.keys():
                    if (x[0][0] == record[0]) and (x[0][1] == record[1]) and (x[0][2] == record[2]) and (x[1][0] == record[3]) and (sp.Qtable[x] > 0):
                        finPrice =  x[1][1]

                self.sp.QtableCluster.pop(indexOfClosest)

            return finPrice

    def formMidRange(self):
        midRange = [4000,12000]

        if self.hour == 23 or self.hour in range(0,6):
            midRange = [2000,5000]
        if self.hour in range(6,10):
            midRange = [3000,4000]
        if self.hour in range(10,17):
            midRange = [5000,12000]
        if self.hour in range(17,23):
            midRange = [5000,9000]

        return midRange


#-----------------------------------------------------------------------------------------
    def run(self):

        self.current_day = 1

        while (self.current_day <= self.days_to_sim):
            self.hour = 0

            while (self.hour <= 23): #23

                #0. Generate weather multiplier for current hour
                hourWeatherKey = np.random.choice(self.keysW, p=self.wKeyProb)
                hourWeather = (hourWeatherKey, self.weatherType[hourWeatherKey])

                # 1. Generate home status
                for x in self.sp.households:
                    x.status = x.getHomeProbStatus(self.hour)
                    #also got status for ruler

                print("Current day: {0}, hour: {1}".format(self.current_day, self.hour))

                # 2.1 Get production number for current hour
                # 2.2 Get production number for current hour

                #get consumption number from ruler agent for next hour
                #get production number from ruler agent for past hour
                consumption = dict.fromkeys(self.sp.addresses)
                production = dict.fromkeys(self.sp.addresses)
                avgCons = dict.fromkeys(self.sp.addresses)

                for x in self.sp.households:
                    consumption[x.address] = x.ruler.getNextHourConsumption(self.hour, hourWeather)
                    production[x.address] = x.ruler.getLastHourProduction(self.hour, hourWeather)

                    #avg consumption
                    x.ruler.avgConsRateList.append(consumption[x.address])
                    if (len(x.ruler.avgConsRateList) > self.avgWindow):
                        x.ruler.avgConsRateList = x.ruler.avgConsRateList[1:]
                        avgCons[x.address] = float(sum(x.ruler.avgConsRateList)) / self.avgWindow

                    else:
                        avgCons[x.address] = 0.0

                # 3. Update info about PRODUCTION (ONLY) to smart contract
                # update about consumption after buying/selling!!!!!!!!!!!!!
                #check for overflow energy
                
                for x in self.sp.households:
                    if (production[x.address] + x.ruler.batteryBalance > x.ruler.batteryCap):
                        self.sellToOuterGrid(x.address, production[x.address] + x.ruler.batteryBalance - x.ruler.batteryCap)
                    if (production[x.address] > 0):
                        self.produceEnergy(x.address, production[x.address])

                applicationList = dict.fromkeys(self.sp.addresses)

                #calculate need and action to do (using battery info, (prod-cons), weather, profile, away/home(hour))
                # 4. Calculate future expences, determine action to do
                for x in self.sp.households:
                    balanceAfterConsumption = x.ruler.batteryBalance - consumption[x.address]
                    #print ("Balance after consumption, before auction: ", balanceAfterConsumption)

                    # go sell (auction or outer grid) or quit
                    if (balanceAfterConsumption >= 0):
                        if balanceAfterConsumption <= x.ruler.batteryCap * self.batteryTH: # *0.1
                            #print ("Comparison: ", balanceAfterConsumption, "<=", x.ruler.batteryCap * self.batteryTH)
                            applicationList.pop(x.address)
                            #print ("Removed application, go to next hour") # go to next hour / no need to buy/sell

                        else: #balanceAfterConsumption > x.ruler.batteryCap * 0.1:
                            #print ("Comparison: ", balanceAfterConsumption, ">", x.ruler.batteryCap * self.batteryTH)
                            #print ("Selling energy above 30%")
                            #selling energy above 30%

                            #get available amount to sell
                            possibleAmountToSell = balanceAfterConsumption - x.ruler.batteryCap * self.batteryTH # *0.3

                            #round to 100
                            possibleAmountToSell = self.roundToWh(possibleAmountToSell)

                            #get price rate
                            #Through Qlearn or exploration

                            if (self.sp.currentTimeStamp < 2400): #100 days
                                qlearnTime = False
                            else:
                                qlearnTime = True

                            sample = [self.hour, round(x.ruler.batteryBalance / x.ruler.batteryCap, 3), avgCons[x.address], 0]
                            priceSellRate = self.priceFormationSell(self.formMidRange(), possibleAmountToSell, qlearnTime, sample)


                            #send application to auction
                            applicationList[x.address] = ['sell', possibleAmountToSell, priceSellRate]


                    # go buy (from auction or outer grid)
                    else: #balanceAfterConsumption < 0
                        #print ("Comparison: ", balanceAfterConsumption, "<", 0)
                        #print ("Need to buy energy")
                        needValueToBuy = self.roundToWh(math.fabs(balanceAfterConsumption))

                        if (self.sp.currentTimeStamp < 2400): #100 days
                                qlearnTime = False
                        else:
                                qlearnTime = True

                        #sample = [14, 0.047, 700, 0]
                        sample = [self.hour, round(x.ruler.batteryBalance / x.ruler.batteryCap, 3), avgCons[x.address], 0]
                        priceBuyRate = self.priceFormationBuy(self.formMidRange(), needValueToBuy, qlearnTime, sample)

                        #amountPriceMult
                        totalCost = priceBuyRate * needValueToBuy

                        #check coin balance
                        self.checkValidCoinBalance(x.address, totalCost)

                        #send application to auction
                        applicationList[x.address] = ['buy', needValueToBuy, priceBuyRate]


                #----------------------------------------------------------------------------------
                # Auction process
                print ("Application list before auction ['buy/sell', needValueToBuy, priceBuyRate]")
                for x in applicationList:
                    print (applicationList[x])

                #for plot demand/supply
                self.sp.transactionList[self.sp.currentTimeStamp] = applicationList

                if self.auctionType == 'loyal':
                    #print ("Going loyal")
                    #form bids/sells from applicationList
                    #collect and form buylist and selllist
                    buyListL = []
                    sellListL = []

                    loyalDict = dict.fromkeys(self.sp.addresses)

                    #create dictionary with loyalty numbers
                    for x in self.sp.households:
                        loyalDict[x.address] = x.loyalty

                    #generate buy/sell lists [addr, loyal, amount, rate]
                    #print ("Applications")
                    for x in applicationList: # key: x - address
                        #print (x)
                        if applicationList[x][0] == 'buy':
                            buyListL.append([x,loyalDict[x],applicationList[x][1],applicationList[x][2]])
                            #print ("Added to buy list")
                        if applicationList[x][0] == 'sell':
                            sellListL.append([x,loyalDict[x],applicationList[x][1],applicationList[x][2]])
                            #print ("Added to sell list")

                    #perform auction on bids/sells
                    if (len(buyListL) and len(sellListL) != 0):

                        #perform auction
                        retList = self.sp.loyaltyDA(buyListL, sellListL, self.divNum)
                        # [returnBuyList, returnSellList, cutSellList, cutBuyList, transactionsSummed]

                        #transactions
                        print ("Transactions to exeucute",retList[4])

                        #execute chosen transactions
                        self.executeTransactions(retList[4])

                        tempList = []
                        for x in retList[4]:
                            tempList.append(x)
                        if len(tempList) != 0:
                            self.sp.approvedTransactions[self.sp.currentTimeStamp] = tempList


                        #eqAuction parameter
                        self.sp.eqAuction.append(retList[5]) 

                        #upd loyalty for successful transaction to both sides
                        for x in self.sp.households:
                            for y in retList[4]:
                                if x.address == y[0]:
                                    x.loyalty *= 1.02
                                if x.address == y[1]:
                                    x.loyalty *= 1.02

                        #collect signals
                        #signalsAgent = dict.fromkeys(addresses)

                        #go for sp q-table

                        '''
                        state = (hour, batteryPercentage, consumption)
                        action = ('buy', price)
                        qKey = (state,action)
                        sp.Qtable[qKey] = reward from eval of returnList
                        '''
                        
                        for x in retList[4]:
                            for y in self.sp.households:
                                if (y.address == x[0]):

                                    state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                    # 0 - buy, 1 - sell
                                    action = (0, x[3])
                                    key = (state, action)
                                    self.sp.Qtable[key] = self.sp.Qtable[key] * y.loyalty + 0.1

                                if (y.address == x[1]):
                                    state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[1]])
                                    action = (1, x[3])
                                    key = (state, action)
                                    self.sp.Qtable[key] = self.sp.Qtable[key] * y.loyalty + 0.1

                        if (len(retList[0]) == 0): #returnBuyList
                            #print ("All approved buyers got needed energy from auction!")
                            #evaluate returnBuyList - empty if all approved have got their needed energy
                            pass
                        else:
                            #need to buy from outer grid
                            retList[0] = self.sp.sumUpVolumeInList(retList[0])

                            #update loyalty
                            for x in self.sp.households:
                                for y in retList[0]:
                                    if (x.address == y[0]):
                                        x.loyalty *= 1.01

                            #perform action on outer grid
                            for x in retList[0]:
                                self.buyFromOuterGrid(x[0], x[2])

                            #update Qtable
                            for x in retList[0]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (0, x[3])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] * y.loyalty + 0.05

                                
                        if (len(retList[1]) == 0): #returnSellList
                            #print ("All approved amount sold!")
                            #evaluate returnSellList - empty if all approved amount is sold
                            pass
                        else:
                            #sell to outer grid / or don do anything
                            retList[1] = self.sp.sumUpVolumeInList(retList[1])

                            #update loyalty
                            for x in self.sp.households:
                                for y in retList[1]:
                                    if (x.address == y[0]):
                                        x.loyalty *= 1.01

                            #perform action on outer grid
                            for x in retList[1]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        if (y.ruler.batteryBalance + x[2] > y.ruler.batteryCap):
                                            self.sellToOuterGrid(x[0], x[2])
                                        else:
                                            pass

                            #update Qtable
                            for x in retList[1]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (1, x[3])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] * y.loyalty + 0.05

                        if (len(retList[2]) == 0): #cutSellList
                            #evaluate cutSellList - too high requests - rejected - need to low them - send this signal
                            pass
                        else:
                            retList[2] = self.sp.sumUpVolumeInList(retList[2])
                            #update loyalty
                            for x in self.sp.households:
                                for y in retList[2]:
                                    if (x.address == y[0]):
                                        x.loyalty *= 0.95
                            #handle unused energy
                            for x in retList[2]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        if y.ruler.batteryBalance + x[2] > y.ruler.batteryCap:
                                            self.sellToOuterGrid(x[0], x[2])
                                        else:
                                            pass

                            #update Qtable
                            for x in retList[2]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (1, x[3])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] * y.loyalty - 1

                        if (len(retList[3]) == 0): #cutBuyList
                            #evaluate cutBuyList - too low bids - rejected - need to increase them - send this signal
                            pass
                        else:
                            retList[3] = self.sp.sumUpVolumeInList(retList[3])
                            #update loyalty
                            for x in self.sp.households:
                                for y in retList[3]:
                                    if (x.address == y[0]):
                                        x.loyalty *= 0.99

                            #handle needed energy
                            for x in retList[3]:
                                self.buyFromOuterGrid(x[0], x[2])

                            #update Qtable
                            for x in retList[3]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (0, x[3])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] * y.loyalty - 1
                        
                        
                    #execute additional transactions on outer grid if neeeded
                    elif len(buyListL) == 0: #no buys, sellers -> og selling needed
                        for x in sellListL:
                            for y in self.sp.households:
                                if (x[0] == y.address):
                                    if y.ruler.batteryBalance + x[2] > y.ruler.batteryCap:
                                        self.sellToOuterGrid(x[0], x[2])

                    elif len(sellListL) == 0: #no sells -> og buys needed
                        for x in buyListL:
                            self.buyFromOuterGrid(x[0], x[2])

                    #perform consumation
                    for x in self.sp.households:
                        if (consumption[x.address] > 0):
                            self.consumeEnergy(x.address, consumption[x.address])
                    #-----------------------------------------------------
                    #update info in smart contract and agents
                    updateInfoSProvider(self)
                    #-------------------------------------------
                    
                    #add info to graph lists for this hour
                    for x in self.sp.households:
                        self.graph_data_batteryBalance[x.address].append(x.ruler.batteryBalance)
                        self.graph_data_consumption[x.address].append(consumption[x.address])
                        self.graph_data_production[x.address].append(production[x.address])
                        self.graph_data_coins[x.address].append(self.getCoinBalance(x.address))
                        self.graph_data_money[x.address].append(self.getMoneyBalance(x.address))

                        if (len(self.graph_data_consumptionC[x.address]) != 0):
                            self.graph_data_consumptionC[x.address].append(self.graph_data_consumptionC[x.address][-1] + consumption[x.address])
                            self.graph_data_productionC[x.address].append(self.graph_data_productionC[x.address][-1] + production[x.address])
                            self.graph_data_coinsC[x.address].append(self.getCoinBalance(x.address) + self.graph_data_coinsC[x.address][-1])
                            self.graph_data_moneyC[x.address].append(self.getMoneyBalance(x.address) + self.graph_data_moneyC[x.address][-1])
                        else:
                            self.graph_data_consumptionC[x.address].append(consumption[x.address])
                            self.graph_data_productionC[x.address].append(production[x.address])
                            self.graph_data_coinsC[x.address].append(self.getCoinBalance(x.address))
                            self.graph_data_moneyC[x.address].append(self.getMoneyBalance(x.address))

                    #Finished

                #-------------------------------------------------------------------------    
                if self.auctionType == 'simple':
                    #print ("going simple")
                    #form bids/sells from applicationList
                    #collect and form buylist and selllist
                    buyList = []
                    sellList = []

                    #generate buy/sell lists [addr, amount, rate]
                    for x in applicationList: # key: x - address
                        if applicationList[x][0] == 'buy':
                            buyList.append([x,applicationList[x][1],applicationList[x][2]])
                        if applicationList[x][0] == 'sell':
                            sellList.append([x,applicationList[x][1],applicationList[x][2]])

                    #print (buyList)
                    #print (sellList)

                    #perform auction on bids/sells
                    if (len(buyList) and len(sellList) != 0):

                        #perform auction
                        retList = self.sp.simpleDReduceAuction(buyList, sellList)
                        # [returnBuyList, returnSellList, cutSellList, cutBuyList, transactionsSummed]

                        #transactions
                        #print ("transactions to execute")
                        #print (retList[4])
                        
                        #execute chosen transactions
                        executeTransactions(retList[4])

                        tempList = []
                        for x in retList[4]:
                            tempList.append(x)
                        if len(tempList) != 0:
                            self.sp.approvedTransactions[self.sp.currentTimeStamp] = tempList

                        #eqAuction parameter
                        self.sp.eqAuction.append(retList[5]) 
                        
                        #collect signals
                        #signalsAgent = dict.fromkeys(addresses)

                        #go for sp q-table

                        '''
                        state = [hour, balanceE, price, production, consumption]
                        action = 'buy'
                        qKey = (state,action)
                        sp.Qtable[qKey] = reward from eval of returnList
                        '''
                        for x in retList[4]:
                            for y in self.sp.households:
                                if (y.address == x[0]):
                                    state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                    action = (0, x[2]) #(buy, price)
                                    key = (state, action)
                                    self.sp.Qtable[key] = self.sp.Qtable[key] + 0.1

                                if (y.address == x[1]):
                                    state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[1]])
                                    action = (1, x[2])
                                    key = (state, action)
                                    self.sp.Qtable[key] += self.sp.Qtable[key] + 0.1

                        if (len(retList[0]) == 0): #returnBuyList
                            #print ("All approved buyers got needed energy from auction!")
                            #evaluate returnBuyList - empty if all approved have got their needed energy
                            pass
                        else:
                            #need to buy from outer grid
                            #perform action on outer grid
                            for x in retList[0]:
                                self.buyFromOuterGrid(x[0], x[1])

                            #update Qtable
                            for x in retList[0]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (0, x[2])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] + 0.05

                                
                        if (len(retList[1]) == 0): #returnSellList
                            #print ("All approved amount sold!")
                            #evaluate returnSellList - empty if all approved amount is sold
                            pass
                        else:
                            #perform action on outer grid
                            for x in retList[1]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        if (y.ruler.batteryBalance + x[1] > y.ruler.batteryCap):
                                            self.sellToOuterGrid(x[0], x[1])
                                        else:
                                            pass

                            #update Qtable
                            for x in retList[1]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (1, x[2])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] + 0.05

                        if (len(retList[2]) == 0): #cutSellList
                            #evaluate cutSellList - too high requests - rejected - need to low them - send this signal
                            pass
                        else:
                            #handle unused energy
                            for x in retList[2]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        if y.ruler.batteryBalance + x[1] > y.ruler.batteryCap:
                                            self.sellToOuterGrid(x[0], x[1])
                                        else:
                                            pass

                            #update Qtable
                            for x in retList[2]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (1, x[2])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] - 1

                        if (len(retList[3]) == 0): #cutBuyList
                            #evaluate cutBuyList - too low bids - rejected - need to increase them - send this signal
                            pass
                        else:
                            #handle needed energy
                            for x in retList[3]:
                                self.buyFromOuterGrid(x[0], x[1])

                            #update Qtable
                            for x in retList[3]:
                                for y in self.sp.households:
                                    if (y.address == x[0]):
                                        state = (self.hour, round(y.ruler.batteryBalance / y.ruler.batteryCap, 3), consumption[x[0]])
                                        action = (0, x[2])
                                        key = (state, action)
                                        self.sp.Qtable[key] = self.sp.Qtable[key] - 1
                        
                        
                    #execute additional transactions on outer grid if neeeded
                    elif len(buyList) == 0: #no buys, sellers -> og selling needed
                        for x in sellList:
                            for y in self.sp.households:
                                if (x[0] == y.address):
                                    if y.ruler.batteryBalance + x[1] > y.ruler.batteryCap:
                                        self.sellToOuterGrid(x[0], x[1])

                    elif len(sellList) == 0: #no sells -> og buys needed
                        for x in buyList:
                            self.buyFromOuterGrid(x[0], x[1])

                    #perform consumation
                    for x in self.sp.households:
                        #print (x.address, consumption[x.address], getEnergyBalance(x.address))
                        if (consumption[x.address] > 0):
                            self.consumeEnergy(x.address, consumption[x.address])
                    #-----------------------------------------------------
                    #update info in smart contract and agents
                    updateInfoSProvider(self)
                    #-------------------------------------------
                    
                    #add info to graph lists for this hour
                    for x in self.sp.households:
                        self.graph_data_batteryBalance[x.address].append(x.ruler.batteryBalance)
                        self.graph_data_consumption[x.address].append(consumption[x.address])
                        self.graph_data_production[x.address].append(production[x.address])
                        self.graph_data_coins[x.address].append(self.getCoinBalance(x.address))
                        self.graph_data_money[x.address].append(self.getMoneyBalance(x.address))

                        if (len(self.graph_data_consumptionC[x.address]) != 0):
                            self.graph_data_consumptionC[x.address].append(self.graph_data_consumptionC[x.address][-1] + consumption[x.address])
                            self.graph_data_productionC[x.address].append(self.graph_data_productionC[x.address][-1] + production[x.address])
                            self.graph_data_coinsC[x.address].append(self.getCoinBalance(x.address) + self.graph_data_coinsC[x.address][-1])
                            self.graph_data_moneyC[x.address].append(self.getMoneyBalance(x.address) + self.graph_data_moneyC[x.address][-1])
                        else:
                            self.graph_data_consumptionC[x.address].append(consumption[x.address])
                            self.graph_data_productionC[x.address].append(production[x.address])
                            self.graph_data_coinsC[x.address].append(self.getCoinBalance(x.address))
                            self.graph_data_moneyC[x.address].append(self.getMoneyBalance(x.address))
                    #Finished

            
                print("Functions executed")

                
                #decay factor for QTable
                self.performDecay()


                # time.sleep(5)  # Delay for 5 sec
                self.sp.currentTimeStamp += 1
                self.hour += 1

            #time.sleep(15)  # Delay for 15 sec
            self.current_day += 1

        print("Simulation finished")
        
#------------------------------------------------------------------------------------------
# Helpful functions

def generateRulers(number, rcap):
    rulersListTemp = []
    for i in range(1, number+1):  # 1-9 indices
        rulersListTemp.append(house.RulerAgent(i, rcap)) 
    rulersList = rulersListTemp
    return rulersList


def generateHouses(number, addressList, rulers):
    housesListTemp = []
    for i in range(1, number+1):
        if (i % 2 == 0):
            pv = True
        else:
            pv = False
        houseInst = house.Household(i, addressList[i-1], rulers[i-1])
        houseInst.pv = pv

        if (houseInst.pv):
            rnd.seed()
            houseInst.ruler.pvSq = 1 * rnd.randint(1,3) #may be 3-4 times bigger PV panel
        else:
            houseInst.ruler.pvSq = 0

        housesListTemp.append(houseInst)
    housesList = housesListTemp
    return housesList

def updateInfoSProvider(sm):
        for x in sm.sp.households:
            #update info from smart contract to entities - house and rulerAgent
            #energyBalance - #check capacity
            x.ruler.batteryBalance = sm.getEnergyBalance(x.address)
            #moneyBalance
            x.ruler.moneyBalance = sm.getMoneyBalance(x.address)
            #coinBalance
            x.ruler.tokenBalance = sm.getCoinBalance(x.address)
            #energyProduction for current hour
            x.ruler.production = sm.getEnergyProduction(x.address)
            #energyConsumption for current hour
            x.ruler.consumption = sm.getEnergyConsumption(x.address)

def setInitialConditions(self, energy, tokens, sm):
    for x in sm.sp.households:
        txhash = eMarketC.transact().setInitialEnergyInMemberStorage(x.address, energy)
        chain.wait.for_receipt(txhash)
        txhash = eTokenC.transact().transfer(x.address, tokens)
        chain.wait.for_receipt(txhash)
    #update info in serviceProvider     
    updateInfoSProvider(sm)
    #---------
    #for x in self.sp.households:
        #x.ruler.batteryBalance = energy
        #x.ruler.tokenBalance = tokens

def setInitialRandConditions(households, energyMaxDiv, tokens, sm):
    for x in sm.sp.households:
        rnd.seed()
        eBal = rnd.randint(1, energyMaxDiv) * 100
        txhash = eMarketC.transact().setInitialEnergyInMemberStorage(x.address, eBal)
        chain.wait.for_receipt(txhash)
        txhash = eTokenC.transact().transfer(x.address, tokens)
        chain.wait.for_receipt(txhash)
    #update info in serviceProvider     
    updateInfoSProvider(sm)
    #----------
    #for x in households:
        #rnd.seed()
        #eBal = rnd.randint(5, energyMaxDiv) * 100
        #x.ruler.batteryBalance = eBal
        #x.ruler.tokenBalance = tokens

#------------------------------------------------------------------------------------------
# Simulation preparation
# Initial parameters
simDays = 1
num_of_households = 4
rulerCap = 15000.0
initEnergy = 8000 # 8 kWh
maxEnergyDiv = 80 #init max energy / 100
initCoins = 20000
aucType = 'loyal'

project = Project()

with project.get_chain('testrpc') as chain:
    #print (chain.get_web3_config())

    accounts = chain.web3.eth.accounts
    assert (accounts[0]==chain.web3.eth.coinbase)
    addresses = list(accounts[1:])
    spAccount = accounts[0] 
    addresses = list(addresses[:num_of_households])


    #Token deploy
    args_for_token_contract = [1000000000, 'EEthToken', 2, 'EET'] #1_000_000_000
    eTokenC, addrToken = chain.provider.get_or_deploy_contract('eToken', deploy_args=args_for_token_contract)
    gas = chain.wait.for_receipt(addrToken)
    print("Contract eTokenC deployment cost: {}".format(gas['gasUsed']))

    #Market deploy
    eMarketC, addrMarket = chain.provider.get_or_deploy_contract('EthEnergyMarketH')
    gas = chain.wait.for_receipt(addrMarket)
    print("Contract eMarketC deployment cost: {}".format(gas['gasUsed']))

    assert (chain.provider.is_contract_available('eToken') == True)
    assert (chain.provider.is_contract_available('EthEnergyMarketH') == True)

    
    rulers = generateRulers(num_of_households, rulerCap) #9 agents
    households = generateHouses(num_of_households, addresses, rulers) #9 households
    sp = sp.ServiceProvider(0, spAccount, addresses, households)

    assert (sp.address == accounts[0] == spAccount)
    assert (households[0].address == addresses[0])

    sim = Simulation(sp, simDays, aucType, eTokenC, eMarketC)
    setInitialRandConditions(households, maxEnergyDiv, initCoins, sim)
    #setInitialConditions(households, maxEnergyDiv, initCoins)
    updateInfoSProvider(sim)

    print ("Done initializing")

    print (len(accounts), accounts)
    print ("---")
    print (sp.address)
    print ("---")
    print (len(addresses), addresses)

    #time.sleep(10.5)

    sim.run()
    #print("Simulation finished")

    #------------------------------------------------------------------------------------------
    # Building basic graphs
    # get data from households/sc
    # build graphs for multiple houses
    hhbuild = households[:]
    buildGraph(hhbuild, sim.graph_data_batteryBalance, 'Balance, Wh', 'Battery balance', True)
    buildGraph(hhbuild, sim.graph_data_consumption, 'Consumption, Wh', 'Consumption profiles', True)
    buildGraph(hhbuild, sim.graph_data_production, 'Production, Wh', 'Production profiles', True)
    buildGraph(hhbuild, sim.graph_data_coins, 'Energy Coins, coins', 'Energy coins', True)
    buildGraph(hhbuild, sim.graph_data_money, 'Money Balance, cents', 'Money balance', True)

    #------------------------------------------------------------------------------------------
    # Building loyalty graph
    if (aucType == 'loyal'):
        tempX = []
        tempY = []
        for i,hh in enumerate(households):
            tempX.append(i+1)
            tempY.append(hh.loyalty)
        plt.xlabel('Households')
        plt.ylabel('Loyalty parameter')
        plt.plot(tempX, tempY, '--go')
        plt.savefig('pics/Loyalty')
        plt.show()

    #------------------------------------------------------------------------------------------
    # Building approved prices graph
    print ("Approved prices distribution per hour")

    keysTr = sp.approvedTransactions.keys()
    keysTr.sort()
    y = []
    x = np.arange(0,sp.currentTimeStamp,1)
    for i in range(sp.currentTimeStamp):
        toappendval = 0
        if i in keysTr:
            listoftr = sp.approvedTransactions[i]
            denom = 0
            for elem in listoftr:
                toappendval+=elem[3]
                denom+=1
            sumavg = toappendval / denom
            y.append(sumavg)
        else:
            y.append(0)
            
    tup = buildSmoothXY(x, y)
    plt.xlabel('Time (hours)')
    plt.ylabel('Average price')
    plt.plot(x, y, '--ro')
    plt.savefig('pics/Prices distribution')
    plt.show()

    #------------------------------------------------------------------------------------------
    # Building graph for auction evaluation
    avgW = 10

    x_1 = np.arange(0, len(sp.eqAuction), 1)
    x_2 = np.arange(avgW, len(sp.eqAuction), 1)
    #plt.plot(x, sp.eqAuction)

    #transform for moving avg
    movAvgEqAuction = []
    for i in range(len(sp.eqAuction) - avgW):
        item = 0
        for j in range(avgW):
            item += sp.eqAuction[i+j]

        movAvgEqAuction.append(item/float(avgW))

    #print ("eqAuction")
    #print (sp.eqAuction)
    #print (len(sp.eqAuction))

    #print ("movAvgEq")
    #print (len(movAvgEqAuction))
    try:
        plt.plot (x_1, sp.eqAuction)
        try:
            tup = buildSmoothXY(x_2, movAvgEqAuction)
            plt.xlabel('Time (hours)')
            plt.ylabel('Avgerage auction utility')
            plt.plot(tup[0], tup[1])
            plt.savefig('pics/Auction evaluation')
            plt.show()
        except ValueError as verr:
            print (str(verr))
    except TypeError as terr:
        print ('Not enogh data for graph: ' + str(terr))

    #------------------------------------------------------------------------------------------
    # Basic information
    for x in hhbuild:
        print ("Household info: ", x.id, "ruler", x.ruler.id, "pv", x.pv, "pvsq", x.ruler.pvSq, "loyalty", x.loyalty)
        print ("Coins:", sim.getCoinBalance(x.address), "MoneyBal:", sim.getMoneyBalance(x.address))
    #print ("ADMCoins:", getCoinBalance(sp, spAccount), "ADMMoneyBal:", getMoneyBalance(sp, spAccount))
    #print ("--------")
    # Qtable
    #for x in sp.Qtable:
        #print (x, sp.Qtable[x])
    ''''''
    #print ("Total approved transactions", sp.approvedTransactions)
    #print (sp.currentTimeStamp)
    #print (sp.transactionList) #all transaction, demand/supply

    #print (sp.totalOuterGrid)
    #print (sp.totalSolarEnergy)

    print ("Total energy flow: ", sp.totalOuterGrid + sp.totalSolarEnergy, " Wh")
    print ("Carbon energy print: ", round(sp.totalOuterGrid / float(sp.totalOuterGrid + sp.totalSolarEnergy) * 100, 2), " %")
    print ("Solar energy print: ", round(sp.totalSolarEnergy / float(sp.totalOuterGrid + sp.totalSolarEnergy) * 100, 2), " %")

    #check updateInfoSProvider(households)
    #END