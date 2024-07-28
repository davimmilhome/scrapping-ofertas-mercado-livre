from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from database.models import Base
from cfg import DbConfig

class DBManager:

    database = None
    engine = None

    def __init__(self, database):
        self.database = database
        self._create_tables(database)
        self._get_specific_db_engine()


    def _get_engine(self, database):

        db_config = DbConfig()
        url = db_config.get_specific_db_url(database)
        return create_engine(url)

    def _get_specific_db_engine(self):
        return self._get_engine(self.database)

    def _create_tables(self, database):
        """Create tables in the database."""
        engine = self._get_specific_db_engine()
        Base.metadata.create_all(engine)

    def _create_session(self, engine):
        Session = sessionmaker(bind=engine)
        return Session()

    @contextmanager
    def session_scope(self):

        engine = self._get_specific_db_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error occurred: {e}")
            return False
        finally:
            session.close()

    def test_connection(self):
        with self.session_scope() as session:
            try:
                session.execute(text('SELECT 1'))
                print("Connection working")
            except Exception as e:
                print(f"Error on connection to db: {e}")

if __name__ == '__main__':
    dbman = DBManager('database_1')
    dbman.test_connection()

