/*
 * ERC20 interface
 * see https://github.com/ethereum/EIPs/issues/20
 */
contract ERC20 {
  //total supply of tokens
  uint public totalSupply;
  
  //check balance with address
  function balanceOf(address who) constant returns (uint);

  //transfer tokens to some adress
  function transfer(address to, uint value);

  //check how many tokens we can spend from other account
  function allowance(address owner, address spender) constant returns (uint);

  //transfer somebody's tokens, but allowed to transfer
  function transferFrom(address from, address to, uint value);

  //approve somebody to spend our tokens
  function approve(address spender, uint value);

  event Transfer(address indexed from, address indexed to, uint value);
  event Approval(address indexed owner, address indexed spender, uint value);
}


/////////////////////////////////////////////////////////////////////////////
contract StandardToken is ERC20 {
  
  //full token name
  string public constant name = "Token Name";

  //short name
  string public constant symbol = "TKN";

  //number of decimals (in ETH - 18)
  uint8 public constant decimals = 18; 

  //dictionary (adress:num of tokens)
  mapping (address => uint) balances;

  //dictionary (adreess:(adreess:available tokens))
  mapping (address => mapping (address => uint)) allowed;

  function transferFrom(address _from, address _to, uint _value) {
    var _allowance = allowed[_from][msg.sender];

    // Check is not needed because safeSub(_allowance, _value) will already throw if this condition is not met
    // if (_value > _allowance) throw;

    balances[_to] +=_value;
    balances[_from] -= _value;
    allowed[_from][msg.sender] -= _value;
    Transfer(_from, _to, _value);
  }

  function approve(address _spender, uint _value) {
    allowed[msg.sender][_spender] = _value;
    Approval(msg.sender, _spender, _value);
  }

  function allowance(address _owner, address _spender) constant returns (uint remaining) {
    return allowed[_owner][_spender];
  }

  function transfer(address _to, uint _value) {
    balances[msg.sender] -= _value;
    balances[_to] += _value;
    Transfer(msg.sender, _to, _value);
  }

  function balanceOf(address _owner) constant returns (uint balance) {
    return balances[_owner];
  }

  ////////////////////////////////////////////////////////////////////
  //Initial supply -> to contract creator
  function StandardToken() {
  balances[msg.sender] = 1000000;
  }


  //Buy tokens (1 eth = 1 token)
  function mint() payable external {
  if (msg.value == 0) throw;

  var numTokens = msg.value;
  totalSupply += numTokens;

  balances[msg.sender] += numTokens;

  Transfer(0, msg.sender, numTokens);
  }

}