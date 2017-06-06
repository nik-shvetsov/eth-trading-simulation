from populus.project import Project
# loads local `populus.json` file (if present)
project = Project()


#custom chain configuration
'''
#info

print (project.project_dir)
print (project.contracts_dir)

from populus.config import ChainConfig
from populus.config import Web3Config

web3_config = Web3Config()
web3_config.set_provider_class('ipc')
web3_config.provider_kwargs['ipc_path'] = '/path/to/geth.ipc'
web3_config.default_account = '0x0000000000000000000000000000000000000001'
project.config['chains.my-chain.web3'] = web3_config
project.write_config()  # optionally persist the configuration to disk

chain_config = ChainConfig()
chain_config.set_chain_class('tester')
chain_config['web3'] = web3_config  # see below for the Web3Config object
project.config['chains.my-chain'] = chain_config
'''


#get contracts ABI
with project.get_chain('testrpc') as chain:
    #help (chain)
    print (chain.get_web3_config())

    fund = chain.web3.toWei(1, 'ether')
    print (fund)

    #greet = chain.provider.get_contract_factory('Greeter')
    chain.provider.get_all_contract_data()

    greeter = chain.provider.get_contract_factory('Greeter')

    #print (greeter.abi)
    #print (greeter.bytecode)
    #print (greeter.bytecode_runtime)
    
    #chain.registrar.set_contract_address('Greeter', '0x322...')
    #print (chain.registrar.get_contract_addresses('Greeter'))

    #cgreeter = chain.provider.get_contract('Greeter')
    #print (cgreeter.address)
    
    gr, deploy_txn_hash_gr = chain.provider.deploy_contract('Greeter')
    em, deploy_txn_hash_em = chain.provider.deploy_contract('EthEMarket')
    print (gr.address) # 20 byte hex encoded address
    print (deploy_txn_hash_gr) # 32 byte hex encoded transaction hash

    print (chain.provider.is_contract_available('Greeter'))
    print (chain.provider.are_contract_dependencies_available('Greeter'))

    #running the tester blockchain
    '''
    print('coinbase:', chain.web3.eth.coinbase)
    print('blockNumber:', chain.web3.eth.blockNumber)
    chain.mine()
    print('blockNumber:', chain.web3.eth.blockNumber)
    snapshot_id = chain.snapshot()
    print('Snapshot:', snapshot_id)
    chain.mine()
    chain.mine()
    print('blockNumber:', chain.web3.eth.blockNumber)
    chain.revert(snapshot_id)
    print('blockNumber:', chain.web3.eth.blockNumber)
    '''

    #wait
    #chain.wait.for_unlock(account=chain.web3.eth.coinbase, timeout=120, poll_interval=None)

    #help(gr)
    print (gr.call().greet())


    print (em.call().getEnergyAccount())
    print (em.call().coinAccount.__dict__)

    print(chain.web3.eth.accounts)
    #ethervote = chain.web3.eth.contract(contractABI).at(contractAddress);




