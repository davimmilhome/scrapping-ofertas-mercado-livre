from database.utils import (
    IDCreator,
)

from database.models import Product

class ProductOperations:

    db_manager = None

    def __init__(self, db_manager):
        self.db_manager = db_manager


    def is_name_product_exists(self, name_product):
        """Check if a product name exists in the products table."""
        with self.db_manager.session_scope() as session:
            product = session.query(Product).filter(Product.name_product == name_product).first()
            if product:
                return product.id_product

        return False


    def add_product(self, name_product):

        existing_product_id = self.is_name_product_exists(name_product)
        if existing_product_id:
            return False

        with self.db_manager.session_scope() as session:

            new_id = IDCreator.get_new_id(number_of_digits=7)

            new_product = Product(
                id_product = IDCreator.get_new_id(number_of_digits=7),
                name_product=name_product,
            )

            session.add(new_product)

        return new_id


if __name__ == '__main__':
    from db_manager import DBManager
    dbman = DBManager('database_1')
    c = ProductOperations(dbman)
    #print(c.is_name_product_exists('teste'))
    #print(c.is_name_store_exists('teste_store'))
    print(c.is_name_product_exists('produto_pythonico1'))
    #print(c.is_name_store_exists('loja_pythonica_5'))
    print(c.add_store('produto_pythonico1'))
    print(c.add_product('deu certo sa porra'))

