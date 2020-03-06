from collections import defaultdict
import math


# aka board, environment, market, auction
class ServiceProvider(object):
    def __init__(self, idx, address, addresses, households):
        self.id = idx
        self.address = address
        self.addresses = addresses
        self.households = households

        self.tokenStorage = 1000000000
        self.moneyBalance = 0

        self.Qtable = defaultdict(lambda: 0)
        self.QtableCluster = []

        self.rate = 1  # 0.1 kwh - 100 wh - 1 token
        self.outer_rate = 10  # 0.1 kwh - 100 wh -  10 token

        self.sellPrice = 11  # 11 cents(or eth) for token - 100 wh - 0.1 kwh
        self.buyPrice = 9  # 9 cents(or eth) for token - 100 wh - 0.1 kwh

        # graph info
        self.currentTimeStamp = 0

        # demand supply
        self.transactionList = {}
        self.approvedTransactions = {}
        self.eqAuction = []

        self.totalOuterGrid = 0
        self.totalSolarEnergy = 0

        self.sellPriceHour = {}  # {house.address:priceSell}
        self.buyPriceHour = {}  # {house.address:priceBuy}

    def priceForm(self, listBuyItem, listSellItem):
        maxP = listBuyItem[3]
        minP = listSellItem[3]

        sumLoyal = float(listBuyItem[1] + listSellItem[1])

        # buyers weight according to loyalty
        wBuy = listBuyItem[1] / sumLoyal
        wSell = listSellItem[1] / sumLoyal

        totalPrice = (minP * wBuy) + (maxP * wSell)

        return int(round(totalPrice))

    def splitVolumeInList(self, listoflists, divNum):
        # ["1",1.0, 200, 7] split into simple records
        newlist = []
        for x in listoflists[:]:
            if x[2] > divNum:
                num = x[2] // divNum
                amount = x[2]
                for y in range(num):
                    newlist.append([x[0], x[1], divNum, x[3]])
            else:
                newlist.append(x)
        return newlist

    def sumUpVolumeInList(self, transactionList):  # use, if amount unified
        newlist = []
        for x in transactionList[:]:
            numOfElem = transactionList.count(x)
            checkElem = [x[0], x[1], x[2] * numOfElem, x[3]]
            if checkElem not in newlist:
                newlist.append(checkElem)
        return newlist

    # http://ai.eecs.umich.edu/people/dreeves/demo/report/proj/node5.html
    def loyaltyDA(self, buyListLoyal, sellListLoyal, divNum):
        # auction with loyalty price formation
        # buyListLoyal = [["1",1.0, 200, 7], ["2",1.0, 100, 7]]
        # only %100 wh available, so split amounts
        # divNum = 100

        eqAuction = 0
        buyListLoyal.sort(key=lambda x: (-x[3], -x[1], -x[2]))
        sellListLoyal.sort(key=lambda x: (x[3], -x[1], -x[2]))

        buyListL = self.splitVolumeInList(buyListLoyal, divNum)
        sellListL = self.splitVolumeInList(sellListLoyal, divNum)

        minOffers = min(len(buyListL), len(sellListL))  # 4
        k = 0

        for x in range(minOffers - 1):
            # print(x, k, buyListL[x][3], sellListL[x][3])
            if buyListL[x][3] >= sellListL[x][3]:
                k += 1
            elif buyListL[x][3] < sellListL[x][3]:
                k = k - 1
                break

        retList = []
        if k > -1:

            priceBuyers = int(math.floor((buyListL[k][3] + sellListL[k][3]) / 2.0))
            nonfixedPrice = (buyListL[k][3] + sellListL[k][3]) / 2.0
            # print("Price: ", priceBuyers, "||", buyListL[k][3], nonfixedPrice)

            returnBuyList = [x for x in buyListL if x[3] >= priceBuyers]
            returnSellList = [x for x in sellListL if x[3] <= priceBuyers]

            cutSellList = [x for x in sellListL if x[3] > priceBuyers]
            cutBuyList = [x for x in buyListL if x[3] < priceBuyers]

            transactions = []

            for x in returnBuyList:
                eqAuction += x[2] * math.fabs(x[3] - priceBuyers)
            for x in returnSellList:
                eqAuction += x[2] * math.fabs(x[3] - priceBuyers)

            while True:
                if (len(returnBuyList) == 0) or (len(returnSellList) == 0):
                    break

                minServed = min(len(returnBuyList), len(returnSellList))
                for x in range(minServed):
                    # returnBuyList[x]
                    # returnSellList[x]
                    newLoyalPrice = self.priceForm(returnBuyList[x], returnSellList[x])
                    # form transaction
                    transactions.append(
                        (
                            returnBuyList[x][0],
                            returnSellList[x][0],
                            divNum,
                            newLoyalPrice,
                        )
                    )
                    # move to next supplier/seller pair
                    returnSellList.remove(returnSellList[x])
                    returnBuyList.remove(returnBuyList[x])
                    break  # Break the inner loop

            # sum transations up
            transactionsSummed = self.sumUpVolumeInList(transactions)

            retList = [
                returnBuyList,
                returnSellList,
                cutSellList,
                cutBuyList,
                transactionsSummed,
                eqAuction,
            ]

        else:
            retList = [[], [], sellListLoyal, buyListLoyal, [], eqAuction]

        return retList

    # perform doubleAuction with bids and sells
    # return transaction list ....
    def simpleDReduceAuction(self, buyList, sellList):

        eqAuction = 0

        buyList.sort(key=lambda x: (-x[2], -x[1]))
        # higher amounts served first
        sellList.sort(key=lambda x: (x[2], -x[1]))

        minOffers = min(len(buyList), len(sellList))  # 4
        # maxOffers = max(len(buyList), len(sellList))
        # find k-index
        k = 0
        for x in range(minOffers - 1):
            if buyList[x][2] >= sellList[x][2]:
                k += 1
            elif buyList[x][2] < sellList[x][2]:
                k = k - 1
                break

        retList = []
        if k > -1:
            priceBuyers = int(math.ceil((buyList[k][2] + sellList[k][2]) / 2.0))

            # check = lambda x: x+1 if maxOffers%2 else x
            # cutIndex = check(k)
            # returnSellList = sellList[:cutIndex]

            returnBuyList = [x for x in buyList if x[2] >= priceBuyers]
            returnSellList = [x for x in sellList if x[2] <= priceBuyers]

            cutSellList = [x for x in sellList if x[2] > priceBuyers]
            cutBuyList = [x for x in buyList if x[2] < priceBuyers]

            transactions = []

            for x in returnBuyList:
                eqAuction += x[1] * math.fabs(x[2] - priceBuyers)
            for x in returnSellList:
                eqAuction += x[1] * math.fabs(x[2] - priceBuyers)

            while True:
                if (len(returnBuyList) == 0) or (len(returnSellList) == 0):
                    break

                for x in range(len(returnSellList)):
                    sellingEnergy = int(returnSellList[x][1])

                    for y in range(len(returnBuyList)):
                        neededEnergy = int(returnBuyList[y][1])

                        if neededEnergy == sellingEnergy:
                            # form transaction
                            newAvgPrice = (
                                returnBuyList[y][2] + returnSellList[x][2]
                            ) / 2
                            transactions.append(
                                (
                                    returnBuyList[y][0],
                                    returnSellList[x][0],
                                    sellingEnergy,
                                    newAvgPrice,
                                )
                            )
                            # move to next supplier/seller pair
                            returnSellList.remove(returnSellList[x])
                            returnBuyList.remove(returnBuyList[y])
                            break  # Break the inner loop
                        elif neededEnergy < sellingEnergy:
                            # form transaction
                            newAvgPrice = (
                                returnBuyList[y][2] + returnSellList[x][2]
                            ) / 2
                            transactions.append(
                                (
                                    returnBuyList[y][0],
                                    returnSellList[x][0],
                                    neededEnergy,
                                    newAvgPrice,
                                )
                            )
                            remainsSeller = math.fabs(neededEnergy - sellingEnergy)
                            # update x[1] - update seller
                            newObj = (
                                returnSellList[x][0],
                                remainsSeller,
                                returnSellList[x][2],
                            )
                            returnSellList[x] = newObj
                            # remove buyer
                            returnBuyList.remove(returnBuyList[y])
                            break
                        else:  # neededEnergy > sellingEnergy
                            # form transaction
                            newAvgPrice = (
                                returnBuyList[y][2] + returnSellList[x][2]
                            ) / 2
                            transactions.append(
                                (
                                    returnBuyList[y][0],
                                    returnSellList[x][0],
                                    sellingEnergy,
                                    newAvgPrice,
                                )
                            )
                            remainsBuyer = neededEnergy - sellingEnergy
                            # update x[1] - update buyer
                            newObj = (
                                returnBuyList[y][0],
                                remainsBuyer,
                                returnBuyList[y][2],
                            )
                            returnBuyList[y] = newObj
                            # remove seller
                            returnSellList.remove(returnSellList[x])
                            break
                    else:
                        continue  # Continue if the inner loop wasn't broken
                    break  # Inner loop was broken, break the outer

            retList = [
                returnBuyList,
                returnSellList,
                cutSellList,
                cutBuyList,
                transactions,
                eqAuction,
            ]
        else:  # if nobody had matched
            retList = [[], [], sellList, buyList, [], eqAuction]

        return retList
