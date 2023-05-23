import asyncio

import psycopg2

from adgbot.model import *


class DatabaseException(Exception):
    pass


class Database:

    def __init__(self):
        self.conn = psycopg2.connect(database="ArtDeGraceDB", user="bot", password="aboba")
        self.init_db_tables()

    def init_db_tables(self):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''create table if not exists users
(
    id         int generated always as identity primary key,
    tg_user_id bigint unique
);''')
                curs.execute('''create table if not exists products
(
    id                    int generated always as identity primary key,
    contract_id           varchar        not null,
    seller_id             int references users (id),
    seller_eth_address    varchar        not null,
    name                  varchar        not null,
    main_photo_id         varchar        not null,
    description           varchar,
    price                 numeric(78, 0) not null,
    publication_timestamp timestamp      not null default current_timestamp
);''')
                curs.execute('''create table if not exists auctions
(
    product_id       int references products (id) primary key,
    duration_in_secs int     not null,
    visited_by_bot   boolean not null default false
);''')
                curs.execute('''create table if not exists addresses
(
    id          int primary key generated always as identity,
    destination varchar not null,
    recipient   varchar not null
);''')
                curs.execute('''create table if not exists wanted_products
(
    buyer_id          int references users (id),
    product_id        int references products (id),
    address_id        int references addresses (id),
    buyer_eth_address varchar not null,
    primary key (buyer_id, product_id)
);''')
                curs.execute('''create table if not exists product_additional_photos
(
    product_id int references products (id),
    photo_id   varchar not null,
    primary key (product_id, photo_id)
);''')
                curs.execute('''create table if not exists product_views
(
    user_id             int references users (id),
    product_id          int references products (id),
    views_count         int       not null default 1,
    liked               boolean   not null default false,
    last_view_timestamp timestamp not null default current_timestamp,
    primary key (user_id, product_id)
);''')
                curs.execute('''create table if not exists order_statuses
(
    status varchar primary key
);''')
                for status in OrderStatus:
                    curs.execute('''insert into order_statuses (status)
values (%s)
on conflict do nothing;''', (status,))
                curs.execute('''create table if not exists orders
(
    product_id        int references products (id) primary key,
    buyer_id          int references users (id),
    address_id        int references addresses (id),
    buyer_eth_address varchar   not null,
    order_timestamp   timestamp not null                         default current_timestamp,
    order_status      varchar references order_statuses (status) default %s
);''', (OrderStatus.PENDING,))
                curs.execute('''create table if not exists order_views
(
    user_id             int references users (id),
    order_id            int references orders (product_id),
    views_count         int       not null default 1,
    last_view_timestamp timestamp not null default current_timestamp,
    primary key (user_id, order_id)
);''')

    def validate_tg_user_registered(self, tg_user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select id
from users
where tg_user_id = %s;''', (tg_user_id,))
                user_row = curs.fetchone()
                if not user_row:
                    curs.execute('''insert into users (tg_user_id)
values (%s)
returning id;''', (tg_user_id,))
                    user_id = curs.fetchone()[0]
                else:
                    user_id = user_row[0]
        return user_id

    def user_id_from_tg_id(self, tg_user_id: int) -> int:
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select id
from users
where tg_user_id = %s;''', (tg_user_id,))
                return curs.fetchone()[0]

    def get_user(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select id, tg_user_id
from users
where id = %s;''', (user_id,))
                row = curs.fetchone()
                return User(id=row[0], tg_id=row[1])

    def buyer_address(self, order_id: int) -> int:
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select id
from users
where tg_user_id = %s;''', (order_id,))
                return curs.fetchone()[0]

    def create_product(self, product: Product):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''
insert into products (seller_id, name, main_photo_id, description, price, contract_id, seller_eth_address)
values (%s, %s, %s, %s, %s, %s, %s)
returning id;''', (product.seller.id, product.name, product.main_photo_id, product.description, product.price,
                   product.contract_id, product.seller_eth_address))
                product_id: int = curs.fetchone()[0]
                for additional_photo_id in product.additional_photo_ids:
                    curs.execute('''insert into product_additional_photos (photo_id, product_id)
values (%s, %s);''', (additional_photo_id, product_id))
                if product.auction_duration_in_secs:
                    curs.execute('''insert into auctions (product_id, duration_in_secs)
values (%s, %s);''', (product_id, product.auction_duration_in_secs))
        return product_id

    def get_product(self, product_id: int, with_additional_photos=False):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select p.id,
       p.seller_id,
       u.tg_user_id,
       p.name,
       p.main_photo_id,
       p.description,
       p.price,
       p.contract_id,
       p.seller_eth_address,
       p.publication_timestamp,
       a.duration_in_secs,
       a.visited_by_bot
from products p
         inner join users u on u.id = p.seller_id
         left join auctions a on p.id = a.product_id
where p.id = %s;''', (product_id,))
                product_row = curs.fetchone()
                if not product_row:
                    return None

                product = Product(id=product_row[0], seller=User(product_row[1], product_row[2]), name=product_row[3],
                                  main_photo_id=product_row[4], description=product_row[5], price=int(product_row[6]),
                                  contract_id=product_row[7], seller_eth_address=product_row[8],
                                  publication_timestamp=product_row[9], auction_duration_in_secs=product_row[10], visited_by_bot=product_row[11])
                if with_additional_photos:
                    curs.execute('''select photo_id
from product_additional_photos
where product_id = %s;''', (product_id,))
                    product.additional_photo_ids = [photo_row[0] for photo_row in curs.fetchall()]
        return product

    def is_possible_to_remove(self, product_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                res = self.query_possible_to_buy_or_remove(curs, product_id)
        return res

    def remove_product(self, product_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''delete
from product_views
where product_id = %s;''', (product_id,))
                curs.execute('''delete
from product_additional_photos
where product_id = %s;''', (product_id,))
                curs.execute('''delete
from auctions
where product_id = %s;''', (product_id,))
                curs.execute('''delete
from products
where id = %s;''', (product_id,))

    def get_next_recommended_product(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''with products_for_sale as (select *
                           from products p
                           where not exists(select * from orders where product_id = p.id)),
     next_product as (select p.id
                      from products_for_sale p
                               left join product_views pv on p.id = pv.product_id and pv.user_id = %s
                      where p.seller_id != %s
                      order by pv.last_view_timestamp is not null, pv.last_view_timestamp, p.publication_timestamp
                      limit 1)
insert
into product_views (user_id, product_id)
select %s, next_product.id
from next_product
on conflict (user_id, product_id) do update set views_count         = product_views.views_count + 1,
                                                last_view_timestamp = current_timestamp
returning product_id;''', (user_id, user_id, user_id))
                row = curs.fetchone()
                if row is None:
                    return None

                product_id = row[0]
        return self.get_product(product_id, with_additional_photos=True)

    def get_next_favorite_product(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''with products_for_sale as (select *
                           from products p
                           where not exists(select * from orders where product_id = p.id)),
     next_product as (select p.id
                      from products_for_sale p
                               left join product_views pv on p.id = pv.product_id and pv.user_id = %s
                      where p.seller_id != %s and liked
                      order by pv.last_view_timestamp is not null, pv.last_view_timestamp, p.publication_timestamp
                      limit 1)
insert
into product_views (user_id, product_id)
select %s, next_product.id
from next_product
on conflict (user_id, product_id) do update set views_count         = product_views.views_count + 1,
                                                last_view_timestamp = current_timestamp
returning product_id;''', (user_id, user_id, user_id))
                row = curs.fetchone()
                if row is None:
                    return None

                product_id = row[0]
        return self.get_product(product_id, with_additional_photos=True)

    def get_next_own_product(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''with products_for_sale as (select *
                           from products p
                           where not exists(select * from orders where product_id = p.id)),
     next_product as (select p.id
                      from products_for_sale p
                               left join product_views pv on p.id = pv.product_id and pv.user_id = %s
                      where p.seller_id = %s
                      order by pv.last_view_timestamp is not null, pv.last_view_timestamp, p.publication_timestamp
                      limit 1)
insert
into product_views (user_id, product_id)
select %s, next_product.id
from next_product
on conflict (user_id, product_id) do update set views_count         = product_views.views_count + 1,
                                                last_view_timestamp = current_timestamp
returning product_id;''', (user_id, user_id, user_id))
                row = curs.fetchone()
                if row is None:
                    return None

                product_id = row[0]
        return self.get_product(product_id, with_additional_photos=False)

    def _update_product_liked(self, user_id: int, product_id: int, liked: bool):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select liked
from product_views
where user_id = %s
  and product_id = %s;''', (user_id, product_id))
                was_liked: bool = curs.fetchone()[0]
                curs.execute('''update product_views
set liked = %s
where user_id = %s
  and product_id = %s
returning liked;''', (liked, user_id, product_id))
                liked: bool = curs.fetchone()[0]
                return liked != was_liked

    def get_order(self, order_id: int, with_address=False):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select product_id, buyer_id, u.tg_user_id, order_status, buyer_eth_address, order_timestamp, address_id
from orders
         inner join users u on u.id = orders.buyer_id
where product_id = %s;''', (order_id,))
                order_row = curs.fetchone()
                product_id = order_row[0]
                order = Order(buyer=User(order_row[1], order_row[2]), order_status=order_row[3],
                              buyer_eth_address=order_row[4], order_timestamp=order_row[5])
                if with_address:
                    address_id = order_row[6]
                    curs.execute('''select destination, recipient
from addresses
where id = %s;''', (address_id,))
                    address_row = curs.fetchone()
                    order.address = Address(address_row[0], address_row[1])
        order.product = self.get_product(product_id)
        return order

    def is_possible_to_pay(self, product_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                res = self.query_possible_to_buy_or_remove(curs, product_id)
        return res

    def query_possible_to_buy_or_remove(self, curs, product_id: int):
        return self.query_product_exists(curs, product_id) and self.query_product_not_ordered(curs, product_id)

    def query_product_exists(self, curs, product_id: int):
        curs.execute('''select count(*) > 0
from products
where id = %s;''', (product_id,))
        exists: bool = curs.fetchone()[0]
        return exists

    def query_product_not_ordered(self, curs, product_id: int):
        curs.execute('''select count(*) = 0
from orders
where product_id = %s;''', (product_id,))
        possible_to_order: bool = curs.fetchone()[0]
        return possible_to_order

    def require_payment(self, buyer_id: int, product_id: int, buyer_eth_address: str, address: Address):
        with self.conn:
            with self.conn.cursor() as curs:
                if not self.query_possible_to_buy_or_remove(curs, product_id):
                    raise DatabaseException("This product is unable to be ordered")

                curs.execute('''insert into addresses (destination, recipient)
values (%s, %s)
returning id;''', (address.destination, address.recipient))
                address_id = curs.fetchone()[0]
                curs.execute('''insert into wanted_products (buyer_id, product_id, address_id, buyer_eth_address)
values (%s, %s, %s, %s)
on conflict (buyer_id, product_id) do update set address_id = %s,
                                     buyer_eth_address = %s;''',
                             (buyer_id, product_id, address_id, buyer_eth_address, address_id,
                              buyer_eth_address))

    def get_wanted_products(self):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select u.id buyer, u.tg_user_id, buyer_eth_address, u2.id seller, u2.tg_user_id, p.id
from users u, users u2, wanted_products wp, products p
where u.id = wp.buyer_id and wp.product_id = p.id and p.seller_id = u2.id;''')
                rows = curs.fetchall()
        return [WantToBuy(User(row[0], row[1]), row[2], User(row[3], row[4]), self.get_product(row[5])) for row in rows]

    def get_products_possible_for_order(self):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select id
from products p
         left join auctions a on p.id = a.product_id
where exists(select * from wanted_products wp where wp.product_id = p.id)
  and not exists(select * from orders o where o.product_id = p.id)
  and ((a.duration_in_secs is null) or
       p.publication_timestamp + (interval '1 second' * a.duration_in_secs) <= current_timestamp);''')
                rows = curs.fetchall()
        return [self.get_product(row[0]) for row in rows]

    def visit_auction(self, product_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''update auctions
set visited_by_bot = true
where product_id = %s;''', (product_id,))

    def create_order(self, wanted_to_buy_product_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''delete
from wanted_products
where product_id = %s
returning buyer_id, buyer_eth_address, address_id;''', (wanted_to_buy_product_id,))
                buyer_id, buyer_eth_address, address_id = curs.fetchone()
                curs.execute('''insert into orders (product_id, buyer_id, address_id, buyer_eth_address)
values (%s, %s, %s, %s);''', (wanted_to_buy_product_id, buyer_id, address_id, buyer_eth_address))
                return buyer_id, buyer_eth_address

    def get_next_receiving(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''with next_receiving_order as (select o.product_id
                              from orders o
                                       left join order_views ov on o.product_id = ov.order_id and ov.user_id = %s
                              where o.buyer_id = %s and o.order_status = %s
                              order by ov.last_view_timestamp is not null, ov.last_view_timestamp, o.order_timestamp
                              limit 1)
insert
into order_views (user_id, order_id)
select %s, next_receiving_order.product_id
from next_receiving_order
on conflict (user_id, order_id) do update set views_count         = order_views.views_count + 1,
                                              last_view_timestamp = current_timestamp
returning order_id;''', (user_id, user_id, OrderStatus.PENDING, user_id))
                row = curs.fetchone()
                if row is None:
                    return None

                product_id = row[0]
        return self.get_order(product_id)

    def get_next_departure(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''with next_departure as (select o.product_id
                        from orders o
                                 inner join products p on p.id = o.product_id
                                 left join order_views ov on o.product_id = ov.order_id and ov.user_id = %s
                        where p.seller_id = %s and o.order_status = %s
                        order by ov.last_view_timestamp is not null, ov.last_view_timestamp, o.order_timestamp
                        limit 1)
insert
into order_views (user_id, order_id)
select %s, next_departure.product_id
from next_departure
on conflict (user_id, order_id) do update set views_count         = order_views.views_count + 1,
                                              last_view_timestamp = current_timestamp
returning order_id;''', (user_id, user_id, OrderStatus.PENDING, user_id))
                row = curs.fetchone()
                if row is None:
                    return None

                product_id = row[0]
        return self.get_order(product_id, with_address=True)

    def get_next_dispute(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''with next_dispute as (select o.product_id
                        from orders o
                                 inner join products p on p.id = o.product_id
                                 left join order_views ov on o.product_id = ov.order_id and ov.user_id = %s
                        where (p.seller_id = %s or o.buyer_id = %s) and o.order_status = %s
                        order by ov.last_view_timestamp is not null, ov.last_view_timestamp, o.order_timestamp
                        limit 1)
insert
into order_views (user_id, order_id)
select %s, next_dispute.product_id
from next_dispute
on conflict (user_id, order_id) do update set views_count         = order_views.views_count + 1,
                                              last_view_timestamp = current_timestamp
returning order_id;''', (user_id, user_id, user_id, OrderStatus.DISPUTE_OPENED, user_id))
                row = curs.fetchone()
                if row is None:
                    return None
                product_id = row[0]
        return self.get_order(product_id)

    def is_possible_to_open_dispute(self, order_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select order_status
from orders
where product_id = %s;''', (order_id,))
                status = curs.fetchone()[0]
        return status == OrderStatus.PENDING

    def update_order_status(self, order_id: int, status: OrderStatus):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''update orders
set order_status = %s
where product_id = %s;''', (status, order_id))

    def get_opened_disputes(self):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select product_id
from orders
where order_status = %s;''', (OrderStatus.DISPUTE_OPENED,))
                order_ids = [order_id_row[0] for order_id_row in curs.fetchall()]
        return [self.get_order(order_id) for order_id in order_ids]

    def get_possible_to_confirm_orders(self, order_duration_in_minutes: int):
        with self.conn:
            with self.conn.cursor() as curs:
                curs.execute('''select product_id
from orders
where order_status = %s
  and order_timestamp + (interval '1 minute' * %s) <= current_timestamp;''',
                             (OrderStatus.PENDING, order_duration_in_minutes))
                order_ids = [order_id_row[0] for order_id_row in curs.fetchall()]
        return [self.get_order(order_id) for order_id in order_ids]

    def get_main_menu_info(self, user_id: int):
        with self.conn:
            with self.conn.cursor() as curs:
                info = MainMenuInfo()
                curs.execute('''select count(*)
from products p
where p.seller_id = %s
  and not exists(select * from orders where product_id = p.id);''', (user_id,))
                info.published_count = curs.fetchone()[0]
                curs.execute('''select count(*)
from orders o
         inner join products p on p.id = o.product_id
where p.seller_id = %s
  and o.order_status in (%s, %s);''', (user_id, OrderStatus.DEAL_CLOSED, OrderStatus.DISPUTE_SOLVED_FOR_SELLER))
                info.sold_count = curs.fetchone()[0]
                curs.execute('''select count(*)
from orders o
where o.buyer_id = %s
  and o.order_status in (%s, %s);''', (user_id, OrderStatus.DEAL_CLOSED, OrderStatus.DISPUTE_SOLVED_FOR_SELLER))
                info.bought_count = curs.fetchone()[0]
                curs.execute('''select count(*)
from orders o
where o.buyer_id = %s
  and o.order_status = %s;''',
                             (user_id, OrderStatus.PENDING))
                info.receiving_count = curs.fetchone()[0]
                curs.execute('''select count(*)
from orders o inner join products p on p.id = o.product_id
where p.seller_id = %s
  and o.order_status = %s;''',
                             (user_id, OrderStatus.PENDING))
                info.departures_count = curs.fetchone()[0]
                curs.execute('''select count(*)
from orders o
         inner join products p on p.id = o.product_id
where (o.buyer_id = %s or p.seller_id = %s)
  and o.order_status = %s;''',
                             (user_id, user_id, OrderStatus.DISPUTE_OPENED))
                info.disputes_count = curs.fetchone()[0]
        return info

    def like_product(self, user_id: int, product_id: int):
        return self._update_product_liked(user_id, product_id, True)

    def dislike_product(self, user_id: int, product_id: int):
        return self._update_product_liked(user_id, product_id, False)

    def __del__(self):
        self.conn.commit()
        self.conn.close()


async def main():
    Database()


if __name__ == "__main__":
    asyncio.run(main())
