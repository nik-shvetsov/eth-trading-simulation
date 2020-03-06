from populus.project import Project
from populus.utils.wait import wait_for_transaction_receipt
from web3 import Web3
import sys
import time


project = Project()

with project.get_chain("testrpc") as chain:
    print(chain.get_web3_config())

    accounts = chain.web3.eth.accounts
    assert accounts[0] == chain.web3.eth.coinbase

    """
    #Soft market - centralized exchange

    eMarketC, addrMarket = chain.provider.get_or_deploy_contract('EthEnergyMarketS')
    gas = chain.wait.for_receipt(addrMarket)
    print("Contract eMarketC deployment cost: {}".format(gas['gasUsed']))
    print (chain.provider.is_contract_available('EthEnergyMarketS'))


    #call - static
    #transact - dynamic

    #1 scenario
    txhash = eMarketC.transact().setRate(100501)
    chain.wait.for_receipt(txhash)
    print (eMarketC.call({"from":accounts[9]}).kWh_rate())

    #2 scenario

    txhash = eMarketC.transact().setInitialEnergyInMemberStorage(accounts[1], 500)
    chain.wait.for_receipt(txhash)
    print (eMarketC.call({"from":accounts[1]}).getEnergyAccount())


    #3 scenario
    txhash = eMarketC.transact({"from":accounts[1]}).sellEnergy(400)
    chain.wait.for_receipt(txhash)
    print (eMarketC.call({"from":accounts[1]}).getEnergyAccount())
    print (eMarketC.call({"from":accounts[1]}).getCoinAccount())
    """
    # Token deploy
    args_for_token_contract = [10000, "EEthToken", 2, "EET"]
    eTokenC, addrToken = chain.provider.get_or_deploy_contract(
        "eToken", deploy_args=args_for_token_contract
    )
    gas = chain.wait.for_receipt(addrToken)
    print("Contract eTokenC deployment cost: {}".format(gas["gasUsed"]))
    print(chain.provider.is_contract_available("eToken"))

    # Market deploy
    eMarketC, addrMarket = chain.provider.get_or_deploy_contract("EthEnergyMarketH")
    gas = chain.wait.for_receipt(addrMarket)
    print("Contract eMarketC deployment cost: {}".format(gas["gasUsed"]))
    print(chain.provider.is_contract_available("EthEnergyMarketH"))

    # TESTING AND SCENARIOS---------------------------------------------

    # add some energy and coins
    # txhash = eMarketC.transact().setInitialEnergyInMemberStorage(accounts[1], 0)
    # chain.wait.for_receipt(txhash)
    txhash = eMarketC.transact().setInitialEnergyInMemberStorage(accounts[2], 1000)
    chain.wait.for_receipt(txhash)

    print("Test token addr")
    # print (addrToken.address)
    print(addrToken)
    print(eTokenC.address)

    print("Scenarios:")
    print("sc1")
    # scenario 1 - move coins from 0 to 1
    assert eTokenC.call().balanceOf(accounts[0]) == 10000
    print(eTokenC.call().balanceOf(accounts[0]))
    print(eTokenC.call().balanceOf(accounts[1]))

    txhash = eTokenC.transact().transfer(accounts[1], 500)
    chain.wait.for_receipt(txhash)

    print(eTokenC.call().balanceOf(accounts[0]))
    print(eTokenC.call().balanceOf(accounts[1]))

    # scenario 2
    print("sc2")
    print(eTokenC.call().balanceOf(accounts[0]))
    print(eTokenC.call().balanceOf(accounts[1]))

    # txhash = eTokenC.transact({"from":accounts[1]}).transfer(accounts[0], 500)
    txhash = eTokenC.transact().transferFrom(accounts[0], accounts[1], 50)
    chain.wait.for_receipt(txhash)

    print(eTokenC.call().balanceOf(accounts[0]))
    print(eTokenC.call().balanceOf(accounts[1]))

    print("sc3")
    # txhash = eMarketC.transact().setRate(2)
    # chain.wait.for_receipt(txhash)
    # buy energy for tokens - from 2 to 1
    print("Coin balance before:")
    print(eTokenC.call().balanceOf(accounts[1]))
    print(eTokenC.call().balanceOf(accounts[2]))
    print("Energy balance before:")
    print(eMarketC.call({"from": accounts[1]}).getEnergyBalance())
    print(eMarketC.call({"from": accounts[2]}).getEnergyBalance())

    print("Buy energy: 1(buyer) - 2(seller)")
    txhash = eMarketC.transact({"from": accounts[1]}).buyEnergy(
        eTokenC.address, accounts[2], 200
    )

    print("Coin balance after:")
    print(eTokenC.call().balanceOf(accounts[1]))
    print(eTokenC.call().balanceOf(accounts[2]))
    print("Energy balance after:")
    print(eMarketC.call({"from": accounts[1]}).getEnergyBalance())
    print(eMarketC.call({"from": accounts[2]}).getEnergyBalance())

    # error scenario
    print("Buy energy: 1(buyer) - 2(seller)")
    try:
        txhash = eMarketC.transact({"from": accounts[1]}).buyEnergy(
            eTokenC.address, accounts[2], 500
        )
        check = chain.wait.for_receipt(txhash)
        print(check)
    except ValueError:
        print("Value error:", sys.exc_info()[0])

    txhash = eMarketC.transact().sendCoin(eTokenC.address, accounts[1], accounts[2], 1)
    check = chain.wait.for_receipt(txhash)
    print(eTokenC.call().balanceOf(accounts[1]))
    print(eTokenC.call().balanceOf(accounts[2]))

    # print (eMarket.call().buyEnergy(accounts[0], accounts[1], 100))
    # set_txn_hash = bank.transact().deposit({from: accounts[1], value: fund})
    # chain.wait.for_receipt(set_txn_hash)
    # deposit = bank.call().get_deposit(accounts[0])
    # assert deposit == 0.05
