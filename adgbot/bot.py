import decimal
import io
import logging
import random
import uuid
from decimal import *

from telegram import *
from telegram import constants
from telegram.ext import *
from telegram.ext import filters

import adgbot.utils as utils
import adgweb3.connectors
from adgbot import model
from adgbot.database import *
from adgbot.model import *
from adgbot.utils import *
from adgweb3.connectors import *


class ArtDeGraceBot:

    def __init__(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
        self.db = Database()
        self.adg_connector = ConnectorADG(net="mumbai")
        self.contact_address = self.adg_connector.get_smart_contract_address()
        self.images_folder = "Images/"
        self.application = Application.builder().token(
            "5714863178:AAEbLZWgoJdInkS62p8shB9uVe2E5u9UCgU").arbitrary_callback_data(4096).persistence(
            PicklePersistence("persistence")).context_types(
            ContextTypes(context=CustomContext, user_data=UserData)).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.main_menu),
                          CommandHandler("menu", self.main_menu)],
            states={
                MainConvState.NO_ACTIVE_CONVERSATION: [],
                PublishConvState.PRODUCT_NAME: [MessageHandler(filters.TEXT, callback=self.publish_product_name)],
                PublishConvState.PRODUCT_DESCRIPTION: [
                    MessageHandler(filters.TEXT, callback=self.publish_product_descr)],
                PublishConvState.PRODUCT_MAIN_PHOTO: [
                    MessageHandler(filters.PHOTO, callback=self.publish_product_main_photo)],
                PublishConvState.PRODUCT_ADDITIONAL_PHOTOS:
                    [MessageHandler(filters.PHOTO, callback=self.publish_product_additional_photo),
                     CallbackQueryHandler(self.publish_product_additional_photo_done,
                                          pattern=lambda cd: cd == CallbackData.PUBLISH_ADDITIONAL_PHOTOS_DONE)],
                PublishConvState.PRODUCT_TYPE:
                    [CallbackQueryHandler(self.publish_product_type,
                                          pattern=ProductTypeCallback)],
                PublishConvState.PRODUCT_AUCTION_DURATION:
                    [CallbackQueryHandler(self.publish_product_auction_duration,
                                          pattern=AuctionDurationCallback)],
                PublishConvState.PRODUCT_PRICE:
                    [MessageHandler(filters.TEXT, self.publish_product_price)],
                PublishConvState.PRODUCT_SELLER_ETH_ADDR:
                    [MessageHandler(filters.TEXT, callback=self.publish_seller_eth_address)],
                PublishConvState.CONFIRMING:
                    [CallbackQueryHandler(self.publish_product_confirm,
                                          pattern=lambda cd: cd == CallbackData.PUBLISH_CONFIRMED)],
                RequirePaymentConvState.BUYER_DELIVERY_DESTINATION:
                    [MessageHandler(filters.TEXT, callback=self.pay_product_destination)],
                RequirePaymentConvState.BUYER_DELIVERY_RECIPIENT:
                    [MessageHandler(filters.TEXT, callback=self.pay_product_recipient)],
                RequirePaymentConvState.BUYER_ETH_ADDRESS:
                    [MessageHandler(filters.TEXT, callback=self.pay_product_buyer_eth_address)]
            },
            fallbacks=[CallbackQueryHandler(self.next_recommended_product,
                                            pattern=lambda cd: cd == CallbackData.NEXT_RECOMMENDED_PRODUCT),
                       CallbackQueryHandler(self.next_favorite_product,
                                            pattern=lambda cd: cd == CallbackData.NEXT_FAVORITE_PRODUCT),
                       CallbackQueryHandler(self.next_receiving,
                                            pattern=lambda cd: cd == CallbackData.NEXT_RECEIVING),
                       CallbackQueryHandler(self.next_departure,
                                            pattern=lambda cd: cd == CallbackData.NEXT_DEPARTURE),
                       CallbackQueryHandler(self.next_own_product,
                                            pattern=lambda cd: cd == CallbackData.NEXT_OWN_PRODUCT),
                       CallbackQueryHandler(self.next_dispute,
                                            pattern=lambda cd: cd == CallbackData.NEXT_DISPUTE),
                       CallbackQueryHandler(self.like_product, pattern=LikeCallback, block=False),
                       CallbackQueryHandler(self.dislike_product, pattern=DislikeCallback, block=False),
                       CallbackQueryHandler(self.pay_product, pattern=RequirePaymentCallback),
                       CallbackQueryHandler(self.remove_product, pattern=RemoveProductCallback),
                       CallbackQueryHandler(self.open_dispute, pattern=OpenDisputeCallback),
                       CallbackQueryHandler(self.current_bid, pattern=CurrentBidCallback, block=False),
                       CallbackQueryHandler(self.publish_product, pattern=lambda cd: cd == CallbackData.PUBLISH),
                       CallbackQueryHandler(self.inactive_button, pattern=InvalidCallbackData, block=False),
                       CallbackQueryHandler(self.inactive_button, block=False)],
            allow_reentry=True,
            name="MainConv",
            persistent=True
        )
        self.application.add_handler(conv_handler)

    async def main_menu(self, update: Update, context: CustomContext):
        user_id = self.db.validate_tg_user_registered(update.effective_user.id)
        main_menu_info = self.db.get_main_menu_info(user_id)

        reply_markup = utils.main_menu_keyboard_markup

        await update.message.reply_text(
            f"▫️ {main_menu_info.published_count} products published on sale\n"
            f"▫️ {main_menu_info.receiving_count} receiving orders\n"
            f"▫️ {main_menu_info.departures_count} departures\n"
            f"▫️ {main_menu_info.disputes_count} opened disputes\n\n"
            f"Totally, you have bought {main_menu_info.bought_count} and sold {main_menu_info.sold_count} products.",
            reply_markup=reply_markup
        )
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def next_own_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        next_product = self.db.get_next_own_product(user_id)
        if next_product is None:
            await query.answer("You have no products for sale")
            return

        photos = [next_product.main_photo_id]
        if not next_product.is_active_auction:
            reply_markup = utils.own_common_products_feed_keyboard(next_product.id)
            caption = f"Your published product:\n\nName: {next_product.name}\nDescription: {next_product.description}\nID: #`{next_product.contract_id}`\nSeller address: `{next_product.seller_eth_address}`"
            lower_caption = f"Price: {next_product.price_to_eth_str}"
        else:
            reply_markup = utils.own_auction_product_keyboard
            caption = f"Your auction:\n\nName: {next_product.name}\nDescription: {next_product.description}\nID: #`{next_product.contract_id}`\nSeller address: `{next_product.seller_eth_address}`\n\nAuction is active till {next_product.auction_till_datetime_str}"
            lower_caption = f"Minimal price: {next_product.price_to_eth_str}"
        media_mes = (await query.message.reply_media_group(
            [InputMediaPhoto(photo_id) for photo_id in photos],
            caption=caption, parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text(lower_caption, reply_markup=reply_markup,
                                   reply_to_message_id=media_mes.id)
        await query.answer()
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def next_recommended_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        next_product = self.db.get_next_recommended_product(user_id)
        if next_product is None:
            await query.answer("No products to show")
            return

        photos = [next_product.main_photo_id]
        photos += next_product.additional_photo_ids
        if not next_product.is_active_auction:
            reply_markup = utils.common_product_keyboard(next_product.id)
            caption = f"Name: {next_product.name}\nDescription: {next_product.description}\nID: #`{next_product.contract_id}`\nSeller address: `{next_product.seller_eth_address}`"
            lower_caption = f"Price: {next_product.price_to_eth_str}"
        else:
            reply_markup = utils.auction_product_keyboard(next_product.id)
            caption = f"Auction:\n\nName: {next_product.name}\nDescription: {next_product.description}\nID: #`{next_product.contract_id}`\nSeller address: `{next_product.seller_eth_address}`\n\nAuction is active till {next_product.auction_till_datetime_str}"
            lower_caption = f"Minimal price: {next_product.price_to_eth_str}"
        media_mes = (await query.message.reply_media_group(
            [InputMediaPhoto(photo_id) for photo_id in photos],
            caption=caption, parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text(lower_caption, reply_markup=reply_markup,
                                   reply_to_message_id=media_mes.id)
        await query.answer()
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def next_favorite_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        next_product = self.db.get_next_favorite_product(user_id)
        if next_product is None:
            await query.answer("No favorite products")
            return

        photos = [next_product.main_photo_id]
        photos += next_product.additional_photo_ids
        if not next_product.is_active_auction:
            reply_markup = utils.favorite_common_product_keyboard(next_product.id)
            caption = f"Name: {next_product.name}\nDescription: {next_product.description}\nID: #`{next_product.contract_id}`\nSeller address: `{next_product.seller_eth_address}`"
            lower_caption = f"Price: {next_product.price_to_eth_str}"
        else:
            reply_markup = utils.favorite_auction_product_keyboard(next_product.id)
            caption = f"Auction:\n\nName: {next_product.name}\nDescription: {next_product.description}\nID: #`{next_product.contract_id}`\nSeller address: `{next_product.seller_eth_address}`\n\nAuction is active till {next_product.auction_till_datetime_str}"
            lower_caption = f"Minimal price: {next_product.price_to_eth_str}"
        media_mes = (await query.message.reply_media_group(
            [InputMediaPhoto(photo_id) for photo_id in photos],
            caption=caption, parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text(lower_caption, reply_markup=reply_markup,
                                   reply_to_message_id=media_mes.id)
        await query.answer()
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def next_receiving(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        order = self.db.get_next_receiving(user_id)
        if order is None:
            await query.answer("No receiving orders")
            return

        photos = [order.product.main_photo_id]
        reply_markup = utils.receiving_feed_keyboard(order.product.id)
        caption = f"You are currently receiving this product:\n\nName: {order.product.name}\nID: #`{order.product.contract_id}`\nSeller address: `{order.product.seller_eth_address}`"
        media_mes = (await query.message.reply_media_group(
            [InputMediaPhoto(photo_id) for photo_id in photos],
            caption=caption, parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text(
            f"You will be able to open dispute until {order.open_dispute_till_datetime}",
            reply_markup=reply_markup,
            reply_to_message_id=media_mes.id)
        await query.answer()
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def next_departure(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        order = self.db.get_next_departure(user_id)
        if order is None:
            await query.answer("No departures")
            return

        photos = [order.product.main_photo_id]
        reply_markup = utils.departure_feed_keyboard
        caption = f"Departure:\n\nName: {order.product.name}\nID: #`{order.product.contract_id}`\nSeller address: `{order.product.seller_eth_address}`\n\nDestination: {order.address.destination}\nRecipient: {order.address.recipient}"
        media_mes = (await query.message.reply_media_group(
            [InputMediaPhoto(photo_id) for photo_id in photos],
            caption=caption, parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text(
            f"This product must be delivered to recipient by {order.open_dispute_till_datetime}",
            reply_markup=reply_markup,
            reply_to_message_id=media_mes.id)
        await query.answer()
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def next_dispute(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        order = self.db.get_next_dispute(user_id)
        if order is None:
            await query.answer("No disputes")
            return

        photos = [order.product.main_photo_id]
        reply_markup = utils.dispute_feed_keyboard
        caption = f"Opened dispute:\n\nProduct name: {order.product.name}\nProduct ID: #`{order.product.contract_id}`\nSeller address: `{order.product.seller_eth_address}`\nBuyer address: `{order.buyer_eth_address}`"
        media_mes = (await query.message.reply_media_group(
            [InputMediaPhoto(photo_id) for photo_id in photos],
            caption=caption, parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text(
            f"This product was ordered on {order.order_datetime}. Pending investigation.",
            reply_markup=reply_markup,
            reply_to_message_id=media_mes.id)
        await query.answer()
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def current_bid(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: CurrentBidCallback = query.data
        if not self.db.is_possible_to_pay(data.product_id):
            await query.answer("This product is unable to be ordered")
            return

        product = self.db.get_product(data.product_id)
        contract_item = self.adg_connector.get_item(product.contract_id)
        for_sale = contract_item[3]
        if not for_sale:
            await query.answer("This product is unable to be ordered")
        elif not product.is_active_auction:
            await query.answer(f"This is now a common sale for a price of {product.price_to_eth_str}")
        else:
            product.price = contract_item[1]
            await query.answer(f"Current minimal possible bid is {product.price_to_eth_str}")

    async def like_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: LikeCallback = query.data
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        updated = self.db.like_product(user_id, data.product_id)
        await query.answer("Added to favorites" if updated else "Already in favorites")

    async def dislike_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: DislikeCallback = query.data
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        updated = self.db.dislike_product(user_id, data.product_id)
        await query.answer("Removed from favorites" if updated else "Already not in favorites")

    async def publish_product(self, update: Update, context: CustomContext):
        query = update.callback_query

        context.user_data.product = Product()
        text = "Send me the name of your product:"
        await query.message.reply_text(text)
        await query.answer()
        return PublishConvState.PRODUCT_NAME

    async def publish_product_name(self, update: Update, context: CustomContext):
        product = context.user_data.product
        product.name = update.message.text
        if not (5 < len(product.name.strip()) < 30):
            text = "Product name must have at least 5 and at most 30 characters. Try again:"
            state = PublishConvState.PRODUCT_NAME
        else:
            text = "Thank you. Send me description of your product:"
            state = PublishConvState.PRODUCT_DESCRIPTION
        await update.message.reply_text(text)
        return state

    async def publish_product_descr(self, update: Update, context: CustomContext):
        product = context.user_data.product
        product.description = update.message.text
        if not (10 <= len(product.description.strip()) <= 100):
            text = "Description must have at least 10 and at most 100 characters. Try again:"
            state = PublishConvState.PRODUCT_DESCRIPTION
        else:
            text = "Thank you. Send me main photo of your product:"
            state = PublishConvState.PRODUCT_MAIN_PHOTO
        await update.message.reply_text(text)
        return state

    async def publish_product_main_photo(self, update: Update, context: CustomContext):
        photo = update.message.photo[-1]
        context.user_data.product.main_photo_id = photo.file_id
        context.user_data.photo_height = photo.height
        context.user_data.photo_width = photo.width

        text = "Thank you. Send me additional photos of your product. When you are done, press this button"
        reply_markup = utils.additional_photos_keyboard
        additional_photos_mes = await update.message.reply_text(text, reply_markup=reply_markup)
        context.user_data.additional_photos_mes = additional_photos_mes
        return PublishConvState.PRODUCT_ADDITIONAL_PHOTOS

    async def publish_product_additional_photo(self, update: Update, context: CustomContext):
        photo = update.message.photo[-1]
        product = context.user_data.product
        product.additional_photo_ids.append(photo.file_id)
        additional_photos_mes = context.user_data.additional_photos_mes
        reply_markup = utils.additional_photos_keyboard
        await additional_photos_mes.edit_text(
            f"I got {len(product.additional_photo_ids)} additional photos. When you upload all photos, press Done",
            reply_markup=reply_markup)
        return PublishConvState.PRODUCT_ADDITIONAL_PHOTOS

    async def publish_product_additional_photo_done(self, update: Update, context: CustomContext):
        query = update.callback_query
        product = context.user_data.product
        await query.message.edit_text(f"Got your {len(product.additional_photo_ids)} additional photos!")
        await query.answer()
        await query.message.reply_text("Choose the type of publication:", reply_markup=utils.product_type_keyboard)
        return PublishConvState.PRODUCT_TYPE

    async def publish_product_type(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: ProductTypeCallback = query.data
        edited_text = "We are publishing a common product!" if not data.is_auction else "We are publishing an auction!"
        await query.edit_message_text(edited_text)
        await query.answer()
        if data.is_auction:
            await query.message.reply_text("How many days will the auction last?",
                                           reply_markup=utils.auction_duration_keyboard)
            return PublishConvState.PRODUCT_AUCTION_DURATION
        else:
            await query.message.reply_text("Send me your price in MATIC:")
            return PublishConvState.PRODUCT_PRICE

    async def publish_product_auction_duration(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: AuctionDurationCallback = query.data
        product = context.user_data.product
        product.auction_duration_in_secs = data.duration_in_secs
        await query.edit_message_text(f"The auction will last {int(data.duration_in_secs / utils.secs_in_day)} days!")
        await query.answer()
        await query.message.reply_text("Send me your price in MATIC:")
        return PublishConvState.PRODUCT_PRICE

    async def publish_product_price(self, update: Update, context: CustomContext):
        product = context.user_data.product
        try:
            product.price = int(Decimal(update.message.text) * Decimal(1e18))
        except decimal.InvalidOperation:
            await update.effective_message.reply_text("Price must be a number. Try again:")
            return PublishConvState.PRODUCT_PRICE

        if not (0 < product.price <= 1000 * 1e18):
            await update.effective_message.reply_text("Price must be in (0, 1000] MATIC. Try again:")
            return PublishConvState.PRODUCT_PRICE

        await update.effective_message.reply_text("Thank you. Send me your wallet address:")
        return PublishConvState.PRODUCT_SELLER_ETH_ADDR

    async def publish_seller_eth_address(self, update: Update, context: CustomContext):
        product = context.user_data.product
        product.seller_eth_address = update.effective_message.text
        if not validate_address(product.seller_eth_address):
            await update.effective_message.reply_text("You must send a valid wallet address. Try again:")
            return PublishConvState.PRODUCT_SELLER_ETH_ADDR

        reply_markup = utils.confirm_publish_keyboard
        photos = [product.main_photo_id]
        photos += product.additional_photo_ids
        caption = f"Name: {product.name}\nDescription: {product.description}\n\nSeller wallet address: `{product.seller_eth_address}`\n\nPrice: {product.price_to_eth_str}"
        media_mes = (
            await update.message.reply_media_group([InputMediaPhoto(photo_id) for photo_id in photos], caption=caption,
                                                   parse_mode=constants.ParseMode.MARKDOWN))[0]
        await media_mes.reply_text("Is it correct?", reply_markup=reply_markup, reply_to_message_id=media_mes.id)
        return PublishConvState.CONFIRMING

    async def publish_product_confirm(self, update: Update, context: CustomContext):
        query = update.callback_query
        user_id = self.db.user_id_from_tg_id(query.from_user.id)
        product = context.user_data.product
        product.seller = model.User(id=user_id)
        publishing_mes = await query.message.reply_text("Publishing your product...")
        await query.answer()
        await query.message.edit_text("Got it!")
        context.application.create_task(self.register_new_product(context, publishing_mes))
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def register_new_product(self, context: CustomContext, publishing_mes: Message):
        try:
            product = context.user_data.product
            product.auction_duration_in_secs = 300 if product.auction_duration_in_secs else 0
            tg_file = await context.bot.get_file(product.main_photo_id)
            file_path = self.images_folder + str(uuid.uuid1()) + ".jpg"
            await tg_file.download_to_drive(file_path)
            contract_id = await self.adg_connector.add_item_async(product.seller_eth_address, product.price,
                                                                  product.name, product.auction_duration_in_secs,
                                                                  file_path)
            product.contract_id = contract_id
            product.id = self.db.create_product(product)
            await publishing_mes.edit_text(
                f"Product \"{product.name}\" with ID #`{product.contract_id}` has been successfully published!",
                parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            await publishing_mes.edit_text("Could not publish your product, something went wrong")
            raise e

    async def remove_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: RemoveProductCallback = query.data
        if not self.db.is_possible_to_remove(data.product_id):
            await query.answer("This product is unable to be removed")
            return

        await query.answer()
        removing_mes = await query.message.reply_text("Removing this product from marketplace...",
                                                      reply_to_message_id=query.message.id)
        product = self.db.get_product(data.product_id)
        context.application.create_task(self.remove_product_task(product, removing_mes))
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def pay_product(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: RequirePaymentCallback = query.data
        if not self.db.is_possible_to_pay(data.product_id):
            await query.answer("This product is unable to be ordered")
            return

        buy_conv_info = RequirePaymentConvInfo()
        buy_conv_info.product_to_pay_id = data.product_id
        buy_conv_info.product_to_pay_mes_id = query.message.id
        context.user_data.require_payment_conv_info = buy_conv_info
        await query.answer()
        await query.message.reply_text("Send the delivery address destination:",
                                       reply_to_message_id=buy_conv_info.product_to_pay_mes_id)
        return RequirePaymentConvState.BUYER_DELIVERY_DESTINATION

    async def open_dispute(self, update: Update, context: CustomContext):
        query = update.callback_query
        data: OpenDisputeCallback = query.data
        if not self.db.is_possible_to_open_dispute(data.order_id):
            await query.answer("You can not open dispute on this order")
            return

        await query.answer()
        disputing_mes = await query.message.reply_text("Opening dispute for this order...",
                                                       reply_to_message_id=query.message.id)
        order = self.db.get_order(data.order_id)
        context.application.create_task(self.open_dispute_task(order, disputing_mes, context))
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def pay_product_destination(self, update: Update, context: CustomContext):
        buy_conv_info = context.user_data.require_payment_conv_info
        buy_conv_info.destination = update.effective_message.text
        if not (10 <= len(buy_conv_info.destination.strip()) <= 50):
            await update.effective_message.reply_text(
                "Destination must have at least 10 and at most 50 characters. Try again:")
            return RequirePaymentConvState.BUYER_DELIVERY_DESTINATION

        await update.effective_message.reply_text("Send the delivery recipient:",
                                                  reply_to_message_id=buy_conv_info.product_to_pay_mes_id)
        return RequirePaymentConvState.BUYER_DELIVERY_RECIPIENT

    async def pay_product_recipient(self, update: Update, context: CustomContext):
        buy_conv_info = context.user_data.require_payment_conv_info
        buy_conv_info.recipient = update.effective_message.text
        if not (5 <= len(buy_conv_info.recipient.strip()) <= 30):
            await update.effective_message.reply_text(
                "Recipient must have at least 5 and at most 30 characters. Try again:")
            return RequirePaymentConvState.BUYER_DELIVERY_RECIPIENT

        await update.effective_message.reply_text("Send your wallet address from which payment will come:",
                                                  reply_to_message_id=buy_conv_info.product_to_pay_mes_id)
        return RequirePaymentConvState.BUYER_ETH_ADDRESS

    async def pay_product_buyer_eth_address(self, update: Update, context: CustomContext):
        buy_conv_info = context.user_data.require_payment_conv_info
        buyer_eth_address = update.effective_message.text
        if not validate_address(buyer_eth_address):
            await update.effective_message.reply_text("You must send a valid wallet address. Try again:")
            return RequirePaymentConvState.BUYER_ETH_ADDRESS

        product_to_buy = self.db.get_product(buy_conv_info.product_to_pay_id)
        if product_to_buy.seller_eth_address == buyer_eth_address:
            await update.effective_message.reply_text(
                "You must send a wallet address different from seller. Try again:")
            return RequirePaymentConvState.BUYER_ETH_ADDRESS

        want_to_buy_mes = await update.effective_message.reply_text("Requiring payment for this product...",
                                                                    reply_to_message_id=buy_conv_info.product_to_pay_mes_id)
        user_id = self.db.user_id_from_tg_id(update.effective_user.id)
        context.application.create_task(
            self.require_payment_task(user_id, buyer_eth_address, product_to_buy,
                                      Address(buy_conv_info.destination, buy_conv_info.recipient), want_to_buy_mes))
        return MainConvState.NO_ACTIVE_CONVERSATION

    async def require_payment_task(self, buyer_id: int, buyer_eth_address: str, product: Product, address: Address,
                                   want_to_buy_mes: Message):
        try:
            await self.adg_connector.want_to_buy_async(buyer_eth_address, int(product.contract_id, 0))
            self.db.require_payment(buyer_id, product.id, buyer_eth_address, address)
            await want_to_buy_mes.edit_text(
                f"Payment required for product \"{product.name}\" with ID #`{product.contract_id}`. Send {product.price_to_eth_str} to address `{self.contact_address}` to pay for this product.",
                parse_mode=constants.ParseMode.MARKDOWN)
        except DatabaseException as e:
            await want_to_buy_mes.edit_text(f"Could not requre payment: {e}")
        except Exception as e:
            await want_to_buy_mes.edit_text("Could not requre payment")
            raise e

    async def remove_product_task(self, product: Product, removing_mes: Message):
        try:
            await self.adg_connector.remove_item_async(int(product.contract_id, 0))
            self.db.remove_product(product.id)
            await removing_mes.edit_text(
                f"Product \"{product.name}\" with ID #`{product.contract_id}` has been successfully removed!",
                parse_mode=constants.ParseMode.MARKDOWN)
        except DatabaseException as e:
            await removing_mes.edit_text(f"Could not remove product: {e}")
        except Exception as e:
            await removing_mes.edit_text("Could not remove product")
            raise e

    async def open_dispute_task(self, order: Order, disputing_mes: Message, context: CallbackContext):
        try:
            await self.adg_connector.open_dispute_async(int(order.product.contract_id, 0))
            self.db.update_order_status(order.product.id, OrderStatus.DISPUTE_OPENED)
            await disputing_mes.edit_text(
                f"Successfully opened dispute on product \"{order.product.name}\" with ID #`{order.product.contract_id}`! Pending investigation.",
                parse_mode=constants.ParseMode.MARKDOWN)
            await context.bot.send_message(order.product.seller.tg_id,
                                           f"User `{order.buyer_eth_address}` opened dispute on product \"{order.product.name}\" with ID #`{order.product.contract_id}`! Pending investigation.",
                                           parse_mode=constants.ParseMode.MARKDOWN)
        except DatabaseException as e:
            await disputing_mes.edit_text(f"Could not open dispute: {e}")
        except Exception as e:
            await disputing_mes.edit_text("Could not open dispute")
            raise e

    async def inactive_button(self, update: Update, context: CustomContext):
        query = update.callback_query
        await query.answer("This button is no longer active")

    async def try_end_auction(self, product):
        if product.auction_duration_in_secs and not product.visited_by_bot:
            try:
                await self.adg_connector.create_finished_auction_order_async(product.contract_id)
                self.db.visit_auction(product.id)
            except:
                print(f"Auction {product.contract_id} is not confirmable yet")

    async def check_payment(self, context: CallbackContext, product_possible_for_order: Product):
        print(f"Checking payment, product {product_possible_for_order.id}")
        await self.try_end_auction(product_possible_for_order)
        paid = self.adg_connector.check_order_created(int(product_possible_for_order.contract_id, 0))
        if paid:
            buyer_id, buyer_eth_address = self.db.create_order(product_possible_for_order.id)
            buyer = self.db.get_user(buyer_id)
            await context.bot.send_message(buyer.tg_id,
                                           f"You successfully ordered product with ID #`{product_possible_for_order.contract_id}`!",
                                           parse_mode=constants.ParseMode.MARKDOWN)
            await context.bot.send_message(product_possible_for_order.seller.tg_id,
                                           f"User with address `{buyer_eth_address}` ordered your product with ID #`{product_possible_for_order.contract_id}`!",
                                           parse_mode=constants.ParseMode.MARKDOWN)

    async def check_payments(self, context: CallbackContext):
        products_possible_for_order = self.db.get_products_possible_for_order()
        for product_possible_for_order in products_possible_for_order:
            context.application.create_task(self.check_payment(context, product_possible_for_order))

    async def check_dispute(self, context: CallbackContext, dispute: Order):
        print(f"Checking dispute, product {dispute.product.id}")
        order_state = self.adg_connector.get_order_state(int(dispute.product.contract_id, 0))
        new_status = None
        seller_mes = None
        buyer_mes = None
        if order_state == 1:
            print("Solved for seller")
            new_status = OrderStatus.DISPUTE_SOLVED_FOR_SELLER
            buyer_mes = f"We are sorry, but we have resolved dispute on product #`{dispute.product.contract_id}` in favor of seller!"
            seller_mes = f"Congratulations! We have resolved dispute on product #`{dispute.product.contract_id}` in your favor, check out your wallet `{dispute.product.seller_eth_address}`."
        elif order_state == 3:
            print("Solved for buyer")
            new_status = OrderStatus.DISPUTE_SOLVED_FOR_BUYER
            buyer_mes = f"Congratulations! We have resolved dispute on product #`{dispute.product.contract_id}` in your favor, check out your wallet `{dispute.buyer_eth_address}`."
            seller_mes = f"We are sorry, but we have resolved dispute on product #`{dispute.product.contract_id}` in favor of buyer!"
        if new_status:
            self.db.update_order_status(dispute.product.id, new_status)
            await context.bot.send_message(dispute.buyer.tg_id, buyer_mes, parse_mode=constants.ParseMode.MARKDOWN)
            await context.bot.send_message(dispute.product.seller.tg_id, seller_mes,
                                           parse_mode=constants.ParseMode.MARKDOWN)

    async def check_disputes(self, context: CallbackContext):
        disputes = self.db.get_opened_disputes()
        for dispute in disputes:
            context.application.create_task(self.check_dispute(context, dispute))

    async def try_confirm_order(self, context: CallbackContext, order: Order):
        print(f"Trying order confirmation, product {order.product.contract_id}")
        try:
            await self.adg_connector.try_to_confirm_by_time_passed_async(int(order.product.contract_id, 0))
            new_status = OrderStatus.DEAL_CLOSED
            buyer_mes = f"The order of product #`{order.product.contract_id}` has been automatically confirmed! Check out your wallet `{order.buyer_eth_address}`."
            seller_mes = f"Congratulations! Buyer `{order.buyer_eth_address}` automatically confirmed receiving of product #`{order.product.contract_id}`, check out your wallet `{order.product.seller_eth_address}`."
            self.db.update_order_status(order.product.id, new_status)
            await context.bot.send_message(order.buyer.tg_id, buyer_mes, parse_mode=constants.ParseMode.MARKDOWN)
            await context.bot.send_message(order.product.seller.tg_id, seller_mes,
                                           parse_mode=constants.ParseMode.MARKDOWN)
        except Exception as e:
            print(f"Could not confirm order: {e}")

    async def try_confirm_orders(self, context: CallbackContext):
        possible_to_confirm_orders = self.db.get_possible_to_confirm_orders(order_duration_in_minutes)
        for confirmed_order in possible_to_confirm_orders:
            context.application.create_task(self.try_confirm_order(context, confirmed_order))

    def start(self) -> None:
        self.application.job_queue.run_repeating(self.check_payments, interval=20, first=0)
        self.application.job_queue.run_repeating(self.check_disputes, interval=20, first=5)
        self.application.job_queue.run_repeating(self.try_confirm_orders, interval=20, first=10)
        self.application.run_polling()
