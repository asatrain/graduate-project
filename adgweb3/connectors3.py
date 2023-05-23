import random
import secrets

from web3 import Web3
import web3
import os
from dotenv import load_dotenv
import json

# order_duration_in_minutes = 28 дней в минутах
order_duration_in_minutes = 5


def generate_random_item_id():
    return "0x" + secrets.token_hex(32)


def validate_address(address):
    return Web3.is_address(address)


class ConnectorADG:

    def __init__(self, net):
        load_dotenv()

        self.net = net
        if self.net == "goerli":
            self.node_url = os.getenv("GOERLI_API_URL", default=None)
            self.private_key = os.getenv("GOERLI_PRIVATE_KEY_0", default=None)
        elif self.net == "sepolia":
            self.node_url = os.getenv("SEPOLIA_API_URL", default=None)
            self.private_key = os.getenv("SEPOLIA_PRIVATE_KEY_0", default=None)
        elif self.net == "local":
            self.node_url = os.getenv("LOCAL_API_URL", default=None)
            self.private_key = os.getenv("LOCAL_PRIVATE_KEY_0", default=None)

        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        if self.w3.is_connected():
            print("-" * 50)
            print("Connection Successful")
            print("-" * 50)
        else:
            print("Connection Failed")

        with open("adgweb3/config.json", 'r') as f:
            self.config = json.load(f)

        self.contract_address = Web3.to_checksum_address(self.config[self.net]["smartContractAddress"])
        self.caller = self.config[self.net]["caller"]

        abi = None
        with open("adgweb3/artifacts/contracts/ADGToken.sol/ADGToken.json", 'r') as f:
            abi = json.load(f)["abi"]

        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)

    def add_item(self, seller, price, name_of_item, item_id=None):
        if item_id is None:
            item_id = int(generate_random_item_id(), 0)

        # initialize the chain id, we need it to build the transaction for replay protection
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.addItem(item_id, seller, price, name_of_item).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        # "maxFeePerGas": 108839382378 * 2})
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")
        
        return item_id

    def remove_item(self, item_id):
        # initialize the chain id, we need it to build the transaction for replay protection
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.removeItem(item_id).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        # "maxFeePerGas": 108839382378 * 2})
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def want_to_buy(self, buyer, itemId):
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.setWantToBuyForUser(buyer, itemId).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        ''' "gasPrice": self.w3.eth.gas_price, '''
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def mintNft(self, to, tokenId):
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.mintNft(to, tokenId).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        ''' "gasPrice": self.w3.eth.gas_price, '''
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def openDispute(self, buyer, itemId):
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.openDispute(buyer, itemId).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        ''' "gasPrice": self.w3.eth.gas_price, '''
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def resolveDisputeForBuyer(self, buyer, itemId):
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.resolveDisputeForBuyer(buyer, itemId).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        ''' "gasPrice": self.w3.eth.gas_price, '''
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def resolveDisputeForSeller(self, buyer, itemId):
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.resolveDisputeForSeller(buyer, itemId).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        ''' "gasPrice": self.w3.eth.gas_price, '''
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def tryToConfirm(self, seller, buyer, itemId):
        Chain_id = self.w3.eth.chain_id
        print(f"Chain_id: {Chain_id}")

        # Call your function
        call_function = self.contract.functions.botTryToConfirm(seller, buyer, itemId).build_transaction(
            {"chainId": Chain_id, "from": self.caller, "nonce": self.w3.eth.get_transaction_count(self.caller),
             "gasPrice": self.w3.eth.gas_price})
        ''' "gasPrice": self.w3.eth.gas_price, '''
        print(f"call_function: {call_function}")

        # Sign transaction
        signed_tx = self.w3.eth.account.sign_transaction(call_function, private_key=self.private_key)
        print(f"signed_tx: {signed_tx}")

        # Send transaction
        send_tx = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"send_tx: {send_tx}")

        # Wait for transaction receipt
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(send_tx)
        print(f"tx_receipt: {tx_receipt}")

        return tx_receipt["transactionHash"].hex()

    def get_item(self, itemId):
        return self.contract.functions.getItem(itemId).call({'from': self.caller})

    def get_order(self, buyer_id, item_id):
        return self.contract.functions.getOrder(buyer_id, item_id).call({'from': self.caller})

    def check_paid(self, buyer_id, item_id):
        return tuple(self.get_order(buyer_id, item_id)) != (0, 0, 0)

    def get_order_state(self, buyer_id, item_id):
        return self.get_order(buyer_id, item_id)[2]
