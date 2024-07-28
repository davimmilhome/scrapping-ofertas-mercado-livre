from sqlalchemy import and_
from datetime import datetime, timedelta

from database.utils import (
    IDCreator,
)

from utils import (
    TimeUtils
)

from database.models import Offers

class OfferOperations:

    db_manager = None

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def is_offer_exists(self, title_offer, value_offer, date_time_offer):
        with self.db_manager.session_scope() as session:

            # Vamos fazer o seguinte arranjo para driblar a coluna
            # do tipo datetime. E utiliza-la como se fosse somente date
            # Obserque que utilizaremos o intervalo exclusivo
            date_time_offer = datetime.fromisoformat(date_time_offer)

            date_start = date_time_offer - timedelta(days=1)
            date_end = date_time_offer + timedelta(days=1)

            offer = session.query(Offers).filter(
                and_(
                    Offers.title_offer == title_offer,
                    Offers.value_offer == value_offer,
                    Offers.date_time_offer > date_start,
                    Offers.date_time_offer < date_end,
                )
            ).first()
            if offer:
                return offer.id_offer

            return False

    def add_offer(self, **kwargs):
        with self.db_manager.session_scope() as session:

            new_id = IDCreator.get_new_id(number_of_digits=7)

            new_offer = Offers(
                id_offer = new_id,
                **kwargs,
            )
            session.add(new_offer)
        return new_id


if __name__ == '__main__':
    from database import DBManager
    dbman = DBManager('database_1')
    o = OfferOperations(dbman)

    offer_data = {
        'title_offer' : 'teste',
        'value_offer' : '54.32',
        'discount_offer_decimals' : '0.7',
        'number_of_offer_page' : '4',
        'previous_value': '55',
        'link_offer' : 'aaaa',
        'date_time_offer' : '2024-07-20 20:35:55.137',
        'fk_product_id_product' : '8109313',
        'fk_marketplace_id_marketplace': '1',
        'fk_store_id_store': '9040257',
    }

    #o.add_offer(**offer_data)
    print(o.is_offer_exists(offer_data['title_offer'], offer_data['value_offer'], '2024-07-20'))

