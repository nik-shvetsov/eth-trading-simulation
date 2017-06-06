pragma solidity ^0.4.9;

//Used https://www.ethereum.org/token guide

contract eToken {
    /* Public variables of the token */
    address public owner;
    string public standard = 'Energy Token';
    string public name;
    string public symbol;
    uint8 public decimals;
    uint256 public totalSupply;

    uint256 public sellPrice = 11; // 11 cents(eth) for token - 100 wh - 0.1 kwh
    uint256 public buyPrice = 9; // 9 cents(eth) for token - 100 wh - 0.1 kwh

    mapping (address => bool) public frozenAccount;

    /* This creates an array with all balances */
    mapping (address => uint256) public balanceOf;

    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _;
    }

    /* This generates a public event on the blockchain that will notify clients */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /* This generates a public event on the blockchain that will notify clients */
    event FrozenFunds(address target, bool frozen);

    /* Initializes contract with initial supply tokens to the creator of the contract */
    function eToken(uint256 initialSupply, string tokenName, uint8 decimalUnits, string tokenSymbol) {
        owner = msg.sender;
        balanceOf[msg.sender] = initialSupply;              // Give the creator all initial tokens
        totalSupply = initialSupply;                        // Update total supply
        name = tokenName;                                   // Set the name for display purposes
        symbol = tokenSymbol;                               // Set the symbol for display purposes
        decimals = decimalUnits;                            // Amount of decimals for display purposes
    }

    /* Send coins */
    function transfer(address _to, uint256 _value) {
        if (balanceOf[msg.sender] < _value) throw;           // Check if the sender has enough
        if (balanceOf[_to] + _value < balanceOf[_to]) throw; // Check for overflows
        if (frozenAccount[msg.sender]) throw;                // Check if frozen
        balanceOf[msg.sender] -= _value;                     // Subtract from the sender
        balanceOf[_to] += _value;                            // Add the same to the recipient
        Transfer(msg.sender, _to, _value);                   // Notify anyone listening that this transfer took place
    }

    
    /* A contract attempts to get the coins */
    function transferFrom(address _from, address _to, uint256 _value) {
        if (frozenAccount[_from]) throw;                        // Check if frozen            
        if (balanceOf[_from] < _value) throw;                 // Check if the sender has enough
        if (balanceOf[_to] + _value < balanceOf[_to]) throw;  // Check for overflows
        balanceOf[_from] -= _value;                          // Subtract from the sender
        balanceOf[_to] += _value;                            // Add the same to the recipient
        Transfer(_from, _to, _value);
    }

    function mintToken(address target, uint256 mintedAmount) onlyOwner {
        balanceOf[target] += mintedAmount;
        totalSupply += mintedAmount;
        Transfer(0, this, mintedAmount);
        Transfer(this, target, mintedAmount);
    }

    function freezeAccount(address target, bool freeze) onlyOwner {
        frozenAccount[target] = freeze;
        FrozenFunds(target, freeze);
    }

    function setPrices(uint256 newSellPrice, uint256 newBuyPrice) onlyOwner {
        sellPrice = newSellPrice;
        buyPrice = newBuyPrice;
    }

    function buy() payable {
        uint amount = msg.value / buyPrice;                // calculates the amount
        if (balanceOf[this] < amount) throw;               // checks if it has enough to sell
        balanceOf[msg.sender] += amount;                   // adds the amount to buyer's balance
        balanceOf[this] -= amount;                         // subtracts amount from seller's balance
        Transfer(this, msg.sender, amount);                // execute an event reflecting the change
    }

    function sell(uint256 amount) {
        if (balanceOf[msg.sender] < amount ) throw;        // checks if the sender has enough to sell
        balanceOf[this] += amount;                         // adds the amount to owner's balance
        balanceOf[msg.sender] -= amount;                   // subtracts the amount from seller's balance
        if (!msg.sender.send(amount * sellPrice)) {        // sends ether to the seller. It's important
            throw;                                         // to do this last to avoid recursion attacks
        } else {
            Transfer(msg.sender, this, amount);            // executes an event reflecting on the change
        }               
    }

    /* This unnamed function is called whenever someone tries to send ether to it */
    function () {
        throw;     // Prevents accidental sending of ether
    }
}


contract EthEnergyMarketH {
    address public owner;
    //total energy cons/prod info
    mapping (address => uint) energyProduction;
    mapping (address => uint) energyConsumption;

    //mapping for coinBalance in eToken contract
    //current energyBalance
    mapping (address => uint) energyBalance;
    //just adhoc for outer grid
    mapping (address => int256) moneyBalance;

    uint private rate;
    uint private outer_rate;
    
    event Produce(address from, uint energy);
    event Consume(address from, uint energy);
    event Buy(address from, address to, uint energy);
    
    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _;
    }

    function EthEnergyMarketH() {
        // (1W = 1 EET coin)
        owner = msg.sender;
        //standardRates
        rate = 1; // 0.1 kwh - 100 wh - 1 token
        outer_rate = 10; // 0.1 kwh - 100 wh -  10 token
    }

    function transactMoney(address from, address to, uint money) onlyOwner {
        moneyBalance[from] -= int(money);
        moneyBalance[to] += int(money);
    }

    function setRate(uint whRate) onlyOwner {
        rate = whRate;
    }

    function setOuterRate(uint whRate) onlyOwner {
        outer_rate = whRate;
    }

    function sendCoin(address coinContractAddress, address energyBuyer, address energySeller, uint amountCoins) {
        eToken m = eToken(coinContractAddress);
        m.transferFrom(energyBuyer, energySeller, amountCoins);
    }

    function buyEnergy(address coinContractAddress, address seller, uint energy, uint aucRate) {

        if ( seller == msg.sender ) throw;
        if ( energy > energyBalance[seller] ) throw;

        var coins = (energy * (aucRate));

        sendCoin(coinContractAddress, msg.sender, seller, coins);

        energyBalance[msg.sender] += energy;
        energyBalance[seller]     -= energy;

        Buy(msg.sender, seller, energy);
    }

    function produceEnergy(uint energy) /*returns (uint EnergyBal)*/ {
        energyProduction[msg.sender] += energy;
        energyBalance[msg.sender] += energy;

        Produce(msg.sender, energy);
        /*return energyBalance[msg.sender];*/
    }

    function consumeEnergy(uint energy) /*returns (uint EnergyBal)*/ {

        if ( energy > energyBalance[msg.sender] ) throw;
        energyBalance[msg.sender] -= energy;
        energyConsumption[msg.sender] += energy;

        Consume(msg.sender, energy);
        /*return energyBalance[msg.sender];*/
    }

    function getMoneyBalance() returns (int moneyBal) {
        return moneyBalance[msg.sender];
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

    function getOuterRate() returns (uint energyRate) {
        return outer_rate;
    }

    function setInitialEnergyInMemberStorage(address account, uint initialWh) onlyOwner {
        energyBalance[account] = initialWh;
    }

    //function for interaction with outer grid
    function buyFromOuterGrid(address account, uint Wh) onlyOwner {
        energyBalance[account] += Wh;
        var money = int(Wh * (outer_rate));//buy using increased rate - 10
        moneyBalance[account] -= money;
    }
    
    function sellToOuterGrid(address account, uint Wh) onlyOwner{
        if ( Wh > energyBalance[account] ) throw;
        energyBalance[account] -= Wh;
        var money = int(Wh * (rate)); //sell using usual rate - 1
        moneyBalance[account] += money; 
    }
}