from web3 import Web3, KeepAliveRPCProvider, IPCProvider
import eth_tester_client.client as cl

from ethereum import tester as t
from ethereum import utils
 
import populus


def mainRPC():
	# Note that you should create only one RPCProvider per
	# process, as it recycles underlying TCP/IP network connections between
	# your process and Ethereum node
	web3 = Web3(KeepAliveRPCProvider(host='localhost', port='8545'))

	# or for an IPC based connection
	#web3 = Web3(IPCProvider())

	print(web3.personal.listAccounts[0])

	#testing functions
	print(web3.personal.listAccounts)
	#print (web3.eth.blockNumber)

	help(cl)
	#for i in dir(cl): print i
	#print (dir(cl))

	newcl = cl.EthTesterClient()
	print(newcl.get_accounts())

def testerEth():
	pass

def populusTest():
	help(populus.utils)
	
#--------------------------------


#mainRPC()
#testerEth()
populusTest()
