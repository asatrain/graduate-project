from datetime import *
from enum import auto
from strenum import StrEnum
import web3

from adgweb3.connectors import order_duration_in_minutes


class OrderStatus(StrEnum):
    PENDING = auto()
    DEAL_CLOSED = auto()
    DISPUTE_OPENED = auto()
    DISPUTE_SOLVED_FOR_BUYER = auto()
    DISPUTE_SOLVED_FOR_SELLER = auto()

    @classmethod
    def from_string(cls, value):
        for v in cls.__members__.values():
            print(v)
            if v == value:
                return v
        raise ValueError(f"'{cls.__name__}' enum not found for '{value}'")


class User:
    def __init__(self, id: int = None, tg_id: int = None):
        self.id = id
        self.tg_id = tg_id


class Product:
    def __init__(self, id: int = None, seller: User = None, name: str = None, description: str = None,
                 main_photo_id: str = None, additional_photo_ids: list[str] = None, price: int = 0,
                 seller_eth_address: str = None, contract_id: str = None, publication_timestamp: datetime = None,
                 auction_duration_in_secs: int = 0, visited_by_bot: bool = False):
        if additional_photo_ids is None:
            additional_photo_ids = []
        self.id = id
        self.seller = seller
        self.name = name
        self.description = description
        self.main_photo_id = main_photo_id
        self.additional_photo_ids = additional_photo_ids
        self.price = price
        self.seller_eth_address = seller_eth_address
        self.contract_id = contract_id
        self.publication_timestamp = publication_timestamp
        self.auction_duration_in_secs = auction_duration_in_secs
        self.visited_by_bot = visited_by_bot

    @property
    def price_to_eth_str(self):
        eth_price = web3.Web3.fromWei(self.price, "ether")
        return f"{eth_price} MATIC"

    @property
    def auction_till_datetime(self):
        return self.publication_timestamp + timedelta(
            seconds=self.auction_duration_in_secs if self.auction_duration_in_secs else 0)

    @property
    def auction_till_datetime_str(self):
        return self.auction_till_datetime.strftime("%c")

    @property
    def is_active_auction(self):
        return datetime.now() <= self.auction_till_datetime


class Address:
    def __init__(self, destination: str, recipient: str):
        self.destination = destination
        self.recipient = recipient


class Order:
    def __init__(self, product: Product = None, buyer: User = None, buyer_eth_address: str = None,
                 address: Address = None, order_status: OrderStatus = None, order_timestamp: datetime = None):
        self.product = product
        self.buyer = buyer
        self.buyer_eth_address = buyer_eth_address
        self.address = address
        self.order_status = order_status
        self.order_timestamp = order_timestamp

    @property
    def open_dispute_till_datetime(self):
        return (self.order_timestamp + timedelta(minutes=order_duration_in_minutes)).strftime("%c")

    @property
    def order_datetime(self):
        return self.order_timestamp.strftime("%c")


class WantToBuy:
    def __init__(self, buyer: User, buyer_eth_address: str, seller: User, product: Product):
        self.buyer = buyer
        self.seller = seller
        self.product = product
        self.buyer_eth_address = buyer_eth_address


class MainMenuInfo:
    def __init__(self, published_count: int = None, sold_count: int = None, receiving_count: int = None,
                 departures_count: int = None, disputes_count: int = None, bought_count: int = None):
        self.published_count = published_count
        self.sold_count = sold_count
        self.bought_count = bought_count
        self.receiving_count = receiving_count
        self.departures_count = departures_count
        self.disputes_count = disputes_count