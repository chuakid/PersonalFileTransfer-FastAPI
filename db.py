import hashlib
from datetime import datetime, timedelta
from os import environ

import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv
import aiofiles

load_dotenv()

client = pymongo.MongoClient(environ.get("mongoserver"))
db = client['db']
files = db['files']


def insert_file(file) -> ObjectId:
    if file["password"]:
        file["password"] = hashlib.sha256(
            file["password"].encode('utf-8')).digest()

    file["tokens"] = []
    file["expiry"] = datetime.utcnow() + timedelta(hours=1)
    result = files.insert_one(file)
    return result.inserted_id


def get_filename(fileid):
    result = files.find_one({"_id": ObjectId(fileid)})
    if result:
        return result["filename"]
    else:
        return False


def get_filename_and_expiry(fileid):
    result = files.find_one({"_id": ObjectId(fileid)}, projection={
                            "filename": True, 'expiry': True})
    return result if result else False


def check_password(fileid, password=None):
    result = files.find_one({"_id": ObjectId(fileid)})
    if result:
        if result['password']:
            return hashlib.sha256(password.encode('utf-8')).digest() == result["password"]
        else:
            return True


def add_token(fileid, token):
    files.update({"_id": ObjectId(fileid)}, {"$push":
                                             {"tokens": token}
                                             })


def check_token(fileid, token):
    result = files.find_one({"_id": ObjectId(fileid)})
    if result:
        if token in result['tokens']:
            return True
    return False


def remove_token(fileid, token):
    result = files.find_one({"_id": ObjectId(fileid)})
    files.update({"_id": ObjectId(fileid)}, {"$pull":
                                             {"tokens": token}
                                             })


def check_password_needed(fileid):
    result = files.find_one({"_id": ObjectId(fileid)})
    return bool(result["password"])


def get_expired_files():
    result = files.find({"expiry": {"$lt": datetime.utcnow()}},
                        projection={"_id": 1, "filename": 1})
    return result


def delete_file(fileid):
    result = files.delete_one({"_id": ObjectId(fileid)})
    return result
