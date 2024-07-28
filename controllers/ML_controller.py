from datetime import datetime
import pandas as pd
pd.set_option('display.max_columns', None)

from  scrappers import (
    MLScrapper
)

from database import (
    DBManager
)


from database.crud import (
    StoreOperations,
    ProductOperations,
    OfferOperations,
)


class MLController:
    db_manager = None

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self

    @staticmethod
    def update_store_product_offer_data():

        db_manager = DBManager('database_1')
        db_manager.test_connection()

        store_operations = StoreOperations(db_manager)
        product_operations = ProductOperations(db_manager)
        offers_operations = OfferOperations(db_manager)

        #ml_pages_results = MLScrapper.get_ML_pages_results()
        ml_pages_results = MLScrapper.get_ML_pages_results(1)
        df = pd.DataFrame.from_dict(ml_pages_results, orient='index')
        df.reset_index(inplace=True)

        MLController._update_id_store(df, store_operations)
        MLController._update_id_product(df, product_operations)
        MLController._update_offer(df, offers_operations)

    @staticmethod
    def _update_id_store(df, store_operations):

        df['fk_id_store'] = df['name_store'].map(
            lambda name_store: store_operations.is_name_store_exists(name_store)
        )

        unregistered_stores = df[df['fk_id_store'] == False]

        for name_store in unregistered_stores['name_store']:
            new_id_store = store_operations.add_store(name_store=name_store)
            df.loc[df["name_store"] == name_store, "fk_id_store"] = new_id_store



    @staticmethod
    def _update_id_product(df, product_operations):

        df['fk_id_product'] = df['name_product'].map(
            lambda name_product: product_operations.is_name_product_exists(name_product)
        )

        unregistered_products = df[df['fk_id_product'] == False]

        for name_product in unregistered_products['name_product']:
            new_id_product = product_operations.add_product(name_product=name_product)
            df.loc[df["name_product"] == name_product, "fk_id_product"] = new_id_product



    @staticmethod
    def _update_offer(df, offers_operations):

        df.drop(columns=['name_store',],inplace=True)
        #df.reset_index(drop=True, inplace=True)
        offer_records = df.to_dict(orient='records')

        # Dropando o índice para ele não atrapalhar na inserção
        for offer in offer_records:
            if 'index' in offer:
                del offer['index']
            if 'name_product' in offer: # Renomeando a chave
                offer['title_offer'] = offer.pop('name_product')

        # Itera sobre cada dicionário e insere a oferta no banco de dados
        for offer in offer_records:
            offer_exist = offers_operations.is_offer_exists(
                title_offer=offer.get('title_offer'),
                value_offer=offer.get('value_offer'),
                date_time_offer=offer.get('date_time_offer')
            )
            if not offer_exist:
                offers_operations.add_offer(**offer)


if __name__ == '__main__':
    MLController.update_store_product_offer_data()