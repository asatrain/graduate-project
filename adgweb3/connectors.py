#!/usr/bin/3
import asyncio

from brownie import accounts, network, config, project
import random
import secrets
import requests

from web3 import Web3
import web3
import os
from dotenv import load_dotenv
import json


def get_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["account_owner"])


# order_duration_in_minutes = 28 дней в минутах
order_duration_in_minutes = 10


def validate_address(address):
    return Web3.isAddress(address)


class ConnectorADG:

    def __init__(self, net):
        load_dotenv()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.project = project.load()
        self.project.load_config()
        network.connect("matic_mumbai")
        with open("config.json", 'r') as f:
            self.config = json.load(f)
        os.chdir("..")

        self.net = net
        self.contract = self.project.ADGToken.at(self.config[self.net]["smartContractAddress"])
        self.account_owner = get_account()
        self.PINATA_JWT = os.getenv("PINATA_JWT", default=None)


    def get_smart_contract_address(self):
        return self.config[self.net]["smartContractAddress"]


    def upload_photo_to_IPFS(self, photo_path):
        pinata_pin_file_url = "https://api.pinata.cloud/pinning/pinFileToIPFS"

        payload = {
            'pinataOptions': '{"cidVersion": 1}'
        }

        with open(photo_path, 'rb') as fp:
            files = [
                (
                    'file',
                    (
                        'image.jpg',
                        fp,
                        'application/octet-stream'
                    )
                )
            ]

            headers = { 'Authorization': f'Bearer {self.PINATA_JWT}' }
            response = requests.request("POST", pinata_pin_file_url, headers=headers, data=payload, files=files)
            print(response.json())
            assert response.status_code == 200
            return "https://ipfs.io/ipfs/" + response.json()["IpfsHash"]


    def add_item(self, seller, price, name_of_item, auction_duration, photo_path):
        image_URI = self.upload_photo_to_IPFS(photo_path)
        tx = self.contract.addItem(seller, price, name_of_item, auction_duration, image_URI, {"from": self.account_owner})
        print(tx.info())
        item_id = tx._events["AddedItem"]["id"]

        return item_id


    async def add_item_async(self, seller, price, name_of_item, auction_duration, photo_bytes_rb):
        return await asyncio.to_thread(self.add_item, seller, price, name_of_item, auction_duration, photo_bytes_rb)
        # loop = asyncio.get_running_loop()
        # return loop.run_in_executor(None, self.add_item, seller, price, name_of_item, auction_duration)


    def remove_item(self, item_id):
        tx = self.contract.removeItem(item_id, {"from": self.account_owner})
        print(tx.info())


    async def remove_item_async(self, item_id):
        return await asyncio.to_thread(self.remove_item, item_id)


    def want_to_buy(self, buyer, item_id):
        tx = self.contract.setWantToBuyForUser(buyer, item_id, {"from": self.account_owner})
        print(tx.info())


    async def want_to_buy_async(self, buyer, item_id):
        return await asyncio.to_thread(self.want_to_buy, buyer, item_id)


    def open_dispute(self, item_id):
        tx = self.contract.openDispute(item_id, {"from": self.account_owner})
        print(tx.info())


    async def open_dispute_async(self, item_id):
        return await asyncio.to_thread(self.open_dispute, item_id)


    def resolve_dispute_for_buyer(self, item_id):
        tx = self.contract.resolveDisputeForBuyer(item_id, {"from": self.account_owner})
        print(tx.info())


    async def resolve_dispute_for_buyer_async(self, item_id):
        return await asyncio.to_thread(self.resolve_dispute_for_buyer, item_id)


    def resolve_dispute_for_seller(self, item_id):
        tx = self.contract.resolveDisputeForSeller(item_id, {"from": self.account_owner})
        print(tx.info())


    async def resolve_dispute_for_seller_async(self, item_id):
        return await asyncio.to_thread(self.resolve_dispute_for_seller, item_id)


    def try_to_confirm_by_time_passed(self, item_id):
        tx = self.contract.tryToConfirmByTimePassed(item_id, {"from": self.account_owner})
        print(tx.info())


    async def try_to_confirm_by_time_passed_async(self, item_id):
        return await asyncio.to_thread(self.try_to_confirm_by_time_passed, item_id)


    def create_finished_auction_order(self, item_id):
        tx = self.contract.createFinishedAuctionOrder(item_id, {"from": self.account_owner})
        print(tx.info())


    async def create_finished_auction_order_async(self, item_id):
        return await asyncio.to_thread(self.create_finished_auction_order, item_id)


    def get_item(self, item_id):
        tx = self.contract.getItem(item_id, {"from": self.account_owner})
        return tx


    def get_order(self, item_id):
        tx = self.contract.getOrder(item_id, {"from": self.account_owner})
        return tx


    def check_order_created(self, item_id):
        return self.get_order(item_id)[3]


    def get_order_state(self, item_id):
        return self.get_order(item_id)[2]


    def mintNFT(self, address_to, item_id):
        tx = self.contract.mintNft(item_id, {"from": self.account_owner})
        print(tx.info())


    def tokenURI(self, item_id):
        tx = self.contract.tokenURI(item_id, {"from": self.account_owner})
        return tx
