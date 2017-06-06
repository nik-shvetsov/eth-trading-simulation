pragma solidity ^0.4.2;

contract SupplierContract 
{
	enum EntityStatus { OnTarget, LowerThanTarget, HigherThanTarget }

	struct Role {
		uint deposited;
		uint fineRate;
		uint target;
		uint allowedRange;	
		uint pendingPayment;	
		EntityStatus status;
	}

	// Contract is owned by a supplier
	address owner;
	Role supplier;

	// Address that is supplier or consumer;
	mapping (address => bool) registered;

	mapping (address => Role) consumerList;
	
	function SupplierContract(supplierFineRate, supplierTarget, supplierAllowedRange);

	// Supplier add consumers to the contract
	function newConsumer(fineRate, target, allowedRange) onlyOwner;

	// Set status of supplier/cosumer according to the reported rate
	function reportGenerated() onlyOwner;
	function reportConsumed() onlyConsumer;

	// Calculate fines according to status
	function calculateFine() internal;

	// Deposit/withdraw for supplier/cosumer
	function deposit() onlyRegistered;
	function withdraw() payable onlyRegistered;
}

contract EnergyMarket {
	address[] contractList;

	function newContract(uint supplierFineRate, uint supplierTarget, uint supplierSafeRange);
}