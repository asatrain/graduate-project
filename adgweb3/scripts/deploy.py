#!/usr/bin/3
from brownie import ADGToken
from connectors import get_account


def main(): 
    # Fetch the account 
    account = get_account()
    print(account)
    # Deploy contract 
    deploy_contract = ADGToken.deploy("Art de Grace", "ADG", {"from" : account}, publish_source=True) 
    # Print contract address 
    print(f"contract deployed at {deploy_contract}")
