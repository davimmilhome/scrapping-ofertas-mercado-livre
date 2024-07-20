from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from models import Base
from cfg import DbConfig

class DBManager:
    def __init__(self):
        pass
        #self.engine = self._get_engine()
        #self.Session = sessionmaker(bind=self.engine)
        #self.session = self.Session()
        #self._create_tables()


    def _get_engine(self, database):

        db_config = DbConfig()
        url = db_config.get_specific_db_url(database)
        return create_engine(url)

    def get_specific_db_engine(self, database):
        return self._get_engine(database)

    def _create_session(self, engine):
        Session = sessionmaker(bind=engine)
        return Session()

    @contextmanager
    def session_scope(self, database):
        """Provide a transactional scope around a series of operations."""
        engine = self.get_specific_db_engine(database)
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            yield session
            session.commit()  # Commit if no exceptions occur
        except Exception as e:
            session.rollback()  # Rollback in case of exception
            print(f"Error occurred: {e}")
        finally:
            session.close()  # Ensure the session is always closed

    def test_connection(self, database):
        with self.session_scope(database) as session:
            try:
                session.execute(text('SELECT 1'))
                print("Connection working")
            except Exception as e:
                print(f"Error on connection to db: {e}")

if __name__ == '__main__':
    dbman = DBManager()
    engine = dbman.get_specific_db_engine('database_1')
    dbman.test_connection('database_1')
    session = dbman._create_session(engine)
