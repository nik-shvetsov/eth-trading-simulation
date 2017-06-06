pragma solidity ^0.4.9;

contract EthEnergyMarket {
    // Variables
    address public owner;
    uint public kWh_rate = 1000;
    uint public kWh_rate_external = 1100;
    uint public totalEnergyTransfered = 0;
    uint public energyStorage = 0;

    mapping (address => uint) energyAccount;
    mapping (address => uint) coinAccount;

    // Events
    event EnergyBought(address indexed from, uint amount);
    event EnergyBoughtExternal(address indexed from, uint amount);
    event EnergySold(address indexed from, uint amount);

    event InsufficientEnergy(uint energyAccount, uint requestedEnergy);
    event InsufficientCoin(uint coinAccount, uint requestedCoins);

    event InitialEnergySet(address addr, uint amount);
    
    // Functions
    function EthEnergyMarket() {
        owner = msg.sender;
        kWh_rate = 1000;
        kWh_rate_external = 1100;
        totalEnergyTransfered = 0;
        energyStorage = 0;
    }
    
    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _;
    }
    
    function setRate(uint rate) onlyOwner {
        kWh_rate = rate;
    }

    function setRateExternal(uint rate) onlyOwner {
        kWh_rate_external = rate;
    }

    // Selling some energy, will credit my account
    function sellEnergy(uint kwh) public {

        if (energyAccount[msg.sender] < kwh) {
            InsufficientEnergy(energyAccount[msg.sender], kwh);             
            throw;
        }

        coinAccount[msg.sender] += (kwh * kWh_rate);
        energyAccount[msg.sender] -= kwh;
        totalEnergyTransfered += kwh;
        energyStorage += kwh;

        EnergySold(msg.sender, kwh);
    }

    // Buying some energy, crediting my energy account
    function buyEnergy(uint kwh) {

        var coin = (kwh * kWh_rate);

        if (energyStorage < kwh){
            InsufficientEnergy(energyStorage, kwh);
            /* buyEnergyExternal(kwh); */
            /*
            throw;
            */
            coin = (kwh * kWh_rate_external);
        }

        if (coinAccount[msg.sender] < coin) {
            InsufficientCoin(coinAccount[msg.sender], coin);
            throw;
        }

        coinAccount[msg.sender] -= coin;
        energyAccount[msg.sender] += kwh;
        totalEnergyTransfered += kwh;

        if (energyStorage < kwh)
        {
            EnergyBoughtExternal(msg.sender, kwh);
        }
        else 
        {
            energyStorage -= kwh;
            EnergyBought(msg.sender, kwh);
        }
    }
    
    function getEnergyAccount() constant returns (uint kwh) {
        return energyAccount[msg.sender];
    }

    function getCoinAccount() constant returns (uint coin) {
        return coinAccount[msg.sender];
    }

    function getEnergyAccountAdmin(address account) constant onlyOwner returns (uint kwh)  {
        return energyAccount[account];
    }

    function getCoinAccountAdmin(address account) constant onlyOwner returns (uint coin)  {
        return coinAccount[account];
    }

    function setInitialEnergyInMemberStorage(address account, uint initialKwh) onlyOwner {
        energyAccount[account] = initialKwh;
        InitialEnergySet(account, initialKwh);
    }

/*
    function buyEnergyExternal(address account, uint kwh) {

        var coin = (kwh * kWh_rate_external);

        if (coinAccount[msg.sender] < coin) {
            InsufficientCoin(coinAccount[msg.sender], coin);
            throw;
        }
        coinAccount[msg.sender] -= coin;
        energyAccount[msg.sender] += kwh;
        totalEnergyTransfered += kwh;

        EnergyBoughtExternal(msg.sender, kwh);

    }
*/
}
