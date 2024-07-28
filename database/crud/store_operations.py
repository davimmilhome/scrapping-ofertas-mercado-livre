from database.utils import (
    IDCreator,
)

from utils import (
    time_utils
)

from database.models import Store


class StoreOperations:

    db_manager = None

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def is_name_store_exists(self, name_store):
        """Check if a store name exists in the products table."""
        with self.db_manager.session_scope() as session:
            store = session.query(Store).filter(Store.name_store == name_store).first()
            if store:
                return store.id_store

        return False

    def add_store(self, name_store):

        existing_store_id = self.is_name_store_exists(name_store)
        if existing_store_id:
            return False

        new_id = IDCreator.get_new_id(number_of_digits=7)

        with self.db_manager.session_scope() as session:

            new_store = Store(
                id_store = new_id,
                name_store= name_store
            )
            session.add(new_store)

        return new_id


if __name__ == '__main__':
    from database import DBManager
    dbman = DBManager('database_1')
    c = StoreOperations(dbman)
    #print(c.is_name_product_exists('teste'))
    #print(c.is_name_store_exists('teste_store'))
    print(c.is_name_store_exists('produto_pythonico1'))
    #print(c.is_name_store_exists('loja_pythonica_5'))
    print(c.add_store('produto_pythonico1'))

