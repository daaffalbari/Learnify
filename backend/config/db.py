# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi
# from config.setting import mongo_uri

# def connect_to_database(url, database):
#     client = MongoClient(url, server_api=ServerApi('1'))
#     db = client[database]
#     return client, db


# client1, db1 = connect_to_database(mongo_uri, 'learning_app')

# client2, db2 = connect_to_database(mongo_uri, 'learning_app2')