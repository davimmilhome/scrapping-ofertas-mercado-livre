from dotenv import load_dotenv
import os

from cfg import CFGLoader

class DbConfig:


    __instance = None
    __database_CFG = {}

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(DbConfig, cls).__new__(cls)

            cfg_env_path = CFGLoader.get_cfg_env_path()
            load_dotenv(cfg_env_path)

            database_1_cfg_dict = {
                'database_1': {
                    'db_type' : os.getenv("DB_1_TYPE"),
                    'url': os.getenv("DB_1_URL"),
                    'usr': os.getenv("DB_1_USR"),
                    'pswd': os.getenv("DB_1_PSWD"),
                    'db_name': os.getenv("DB_1_NAME")
                }
            }

            cls.__database_CFG.update(database_1_cfg_dict)

        return cls.__instance

    @property
    def _database_cfg(self):
        return self.__database_CFG

    def _get_specific_db_config(self, db_name):
        return self._database_cfg.get(db_name, {})

    def get_specific_db_url(self, db_name):

        db_config = self._get_specific_db_config(db_name)
        db_url = (
            db_config['db_type']
            + "://"
            + db_config['usr']
            + ':'
            + db_config['pswd']
            + "@"
            + db_config['url']
            + '/'
            + db_config['db_name']
        )

        return db_url

if __name__ == '__main__':
    db_config = DbConfig()
    url = db_config.get_specific_db_url('database_1')
    print(url)
    pass