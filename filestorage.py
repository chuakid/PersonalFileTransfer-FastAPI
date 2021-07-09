from os import getcwd, makedirs, path
from shutil import copyfileobj, rmtree

from fastapi.responses import FileResponse

import db

UPLOAD_FOLDER = getcwd() + "/files"


def purge_files():
    print("Purging files")
    expiredfiles = db.get_expired_files()
    for file in expiredfiles:
        db.delete_file(file["_id"])
        rmtree(path.join(
            UPLOAD_FOLDER, str(file["_id"])))


def download_file(fileid, filename) -> FileResponse:
    return FileResponse(path=path.join(UPLOAD_FOLDER, fileid, filename), filename=filename)


def upload_file(file, fileid):
    try:
        # make folder for file
        makedirs(path.join(UPLOAD_FOLDER, str(fileid)))
    except OSError:
        pass
    with open(path.join(
            UPLOAD_FOLDER, str(fileid), file.filename), "wb+") as f:
        copyfileobj(file.file, f)
