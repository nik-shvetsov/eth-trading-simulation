pragma solidity ^0.4.9;

contract EthEnergyMarket2 {

    mapping (address => uint) energyProduction;
    mapping (address => uint) energyBalance;
    mapping (address => uint) energyConsumption;

    uint private rate;
    bool private transactionOK;

    event Produce(address from, uint energy);
    event Consume(address from, uint energy);
    event Buy(address from, address to, uint energy);


    function EthEnergyMarket2() {
        // (1W = 1 EET coin)
        rate = 1; 
    }

	function sendCoin(address coinContractAddress, address energyBuyer, address energySeller, uint amount) 
    returns (bool success) {
		eToken m = eToken(coinContractAddress);
		success = m.transferFrom(energyBuyer, energySeller, amount);
		return success;
	}

    function setProduction(uint energy) returns (uint EnergyBal) {
        energyProduction[msg.sender] += energy;
        energyBalance[msg.sender] += energy;

        Produce(msg.sender, energy);
        return energyBalance[msg.sender];
    }

    function consumeEnergy (uint energy) returns (uint EnergyBal) {

        if ( energy > energyBalance[msg.sender] ) throw;
        energyBalance[msg.sender]     -= energy;
        energyConsumption[msg.sender] += energy;

        Consume(msg.sender, energy);
        return energyBalance[msg.sender];
    }

    function buyEnergy(address coinContractAddress, address seller, uint energy) returns (bool transactionOK) {

        if ( energy > energyBalance[seller] ) throw;

        transactionOK = sendCoin(coinContractAddress, msg.sender, seller, energy);
        if (transactionOK != true) throw;

        energyBalance[msg.sender] += energy;
        energyBalance[seller]     -= energy;

        Buy(msg.sender, seller, energy);
        return transactionOK;
    }

    function getEnergyBalance() returns (uint energyBal) {
        return energyBalance[msg.sender];
    }

    function getEnergyConsumption() returns (uint energyBal) {
        return energyConsumption[msg.sender];
    }

    function getEnergyProduction() returns (uint energyBal) {
        return energyProduction[msg.sender];
    }
    
    function getRate() returns (uint energyRate) {
        return rate;
    }
}