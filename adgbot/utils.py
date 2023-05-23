import enum
from enum import auto

from telegram import *
from telegram.ext import *

from adgbot.model import Product


class MainConvState(enum.Enum):
    NO_ACTIVE_CONVERSATION = auto()


class RequirePaymentConvState(enum.Enum):
    BUYER_DELIVERY_DESTINATION = auto()
    BUYER_DELIVERY_RECIPIENT = auto()
    BUYER_ETH_ADDRESS = auto()


class PublishConvState(enum.Enum):
    PRODUCT_NAME = auto()
    PRODUCT_DESCRIPTION = auto()
    PRODUCT_MAIN_PHOTO = auto()
    PRODUCT_ADDITIONAL_PHOTOS = auto()
    PRODUCT_TYPE = auto()
    PRODUCT_AUCTION_DURATION = auto()
    PRODUCT_PRICE = auto()
    PRODUCT_SELLER_ETH_ADDR = auto()
    CONFIRMING = auto()


class CallbackData(enum.Enum):
    NEXT_OWN_PRODUCT = auto()
    NEXT_RECOMMENDED_PRODUCT = auto()
    NEXT_FAVORITE_PRODUCT = auto()
    NEXT_RECEIVING = auto()
    NEXT_DEPARTURE = auto()
    NEXT_DISPUTE = auto()
    PUBLISH = auto()
    PUBLISH_ADDITIONAL_PHOTOS_DONE = auto()
    PUBLISH_CONFIRMED = auto()


class ProductTypeCallback:
    def __init__(self, is_auction: bool):
        self.is_auction = is_auction


class AuctionDurationCallback:
    def __init__(self, duration_in_secs: int):
        self.duration_in_secs = duration_in_secs


class LikeCallback:
    def __init__(self, product_id: int):
        self.product_id = product_id


class DislikeCallback:
    def __init__(self, product_id: int):
        self.product_id = product_id


class RequirePaymentCallback:
    def __init__(self, product_id: int):
        self.product_id = product_id


class CurrentBidCallback:
    def __init__(self, product_id: int):
        self.product_id = product_id


class OpenDisputeCallback:
    def __init__(self, order_id: int):
        self.order_id = order_id


class RemoveProductCallback:
    def __init__(self, product_id: int):
        self.product_id = product_id


class RequirePaymentConvInfo:
    def __init__(self):
        self.product_to_pay_id: int | None = None
        self.product_to_pay_mes_id: int | None = None
        self.destination: str | None = None
        self.recipient: str | None = None


class UserData:
    def __init__(self):
        self.product: Product | None = None
        self.additional_photos_mes: Message | None = None
        self.require_payment_conv_info: RequirePaymentConvInfo | None = None


class CustomContext(CallbackContext[ExtBot, UserData, dict, dict]):
    pass


main_menu_keyboard_markup = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("My products 💎", callback_data=CallbackData.NEXT_OWN_PRODUCT),
        InlineKeyboardButton("Publish product 📝", callback_data=CallbackData.PUBLISH)
    ],
    [
        InlineKeyboardButton("Feed 🔍", callback_data=CallbackData.NEXT_RECOMMENDED_PRODUCT),
        InlineKeyboardButton("Favorites ❤️", callback_data=CallbackData.NEXT_FAVORITE_PRODUCT),
    ],
    [
        InlineKeyboardButton("Receiving 📭", callback_data=CallbackData.NEXT_RECEIVING),
        InlineKeyboardButton("Departures 📦", callback_data=CallbackData.NEXT_DEPARTURE),
        InlineKeyboardButton("Disputes ⚖️", callback_data=CallbackData.NEXT_DISPUTE)
    ]
])

additional_photos_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Done", callback_data=CallbackData.PUBLISH_ADDITIONAL_PHOTOS_DONE),
    ]
])


def common_product_keyboard(product_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️", callback_data=LikeCallback(product_id)),
            InlineKeyboardButton("Buy 💵", callback_data=RequirePaymentCallback(product_id)),
            InlineKeyboardButton("Next", callback_data=CallbackData.NEXT_RECOMMENDED_PRODUCT),
        ]
    ])


def auction_product_keyboard(product_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❤️", callback_data=LikeCallback(product_id)),
            InlineKeyboardButton("Current bid 📈", callback_data=CurrentBidCallback(product_id))
        ],
        [
            InlineKeyboardButton("Bet 💵", callback_data=RequirePaymentCallback(product_id)),
            InlineKeyboardButton("Next", callback_data=CallbackData.NEXT_RECOMMENDED_PRODUCT)
        ]
    ])


def favorite_common_product_keyboard(product_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖤", callback_data=DislikeCallback(product_id)),
            InlineKeyboardButton("Buy 💵", callback_data=RequirePaymentCallback(product_id)),
            InlineKeyboardButton("Next", callback_data=CallbackData.NEXT_FAVORITE_PRODUCT),
        ]
    ])


def favorite_auction_product_keyboard(product_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🖤", callback_data=DislikeCallback(product_id)),
            InlineKeyboardButton("Current bid 📈", callback_data=CurrentBidCallback(product_id))
        ],
        [
            InlineKeyboardButton("Bet 💵", callback_data=RequirePaymentCallback(product_id)),
            InlineKeyboardButton("Next", callback_data=CallbackData.NEXT_FAVORITE_PRODUCT)
        ]
    ])


def receiving_feed_keyboard(order_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Open dispute ⚖️", callback_data=OpenDisputeCallback(order_id)),
            InlineKeyboardButton("Next 📭", callback_data=CallbackData.NEXT_RECEIVING)
        ]
    ])


def own_common_products_feed_keyboard(product_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Remove ❌", callback_data=RemoveProductCallback(product_id)),
            InlineKeyboardButton("Next 💎", callback_data=CallbackData.NEXT_OWN_PRODUCT)
        ]
    ])


own_auction_product_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Next 💎", callback_data=CallbackData.NEXT_OWN_PRODUCT)]])

product_type_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Auction 📈", callback_data=ProductTypeCallback(is_auction=True)),
        InlineKeyboardButton("Common 🛒", callback_data=ProductTypeCallback(is_auction=False))
    ]
])

secs_in_day = 86400

auction_duration_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton(f"{days}", callback_data=AuctionDurationCallback(duration_in_secs=days * secs_in_day)) for
     days in range(1, 7 + 1)]
])

confirm_publish_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Publish ✅", callback_data=CallbackData.PUBLISH_CONFIRMED),
    ]
])

departure_feed_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Next 📦", callback_data=CallbackData.NEXT_DEPARTURE)
    ]
])

dispute_feed_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Next ⚖️", callback_data=CallbackData.NEXT_DISPUTE)
    ]
])
