from cfg import DbConfig

db_config = DbConfig()
db_login_info = db_config.get_specific_db_config('database_1',)
print(db_login_info['url'])


#print(c)
