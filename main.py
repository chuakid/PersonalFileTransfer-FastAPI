from datetime import datetime
from secrets import token_urlsafe

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import (Body, FastAPI, File, Form, HTTPException, Request,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware

import db
import filestorage

app = FastAPI()

origins = [
    "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.put("/api/upload")
async def upload(file: UploadFile = File(...), password: str = Form(None)):
    file_id = db.insert_file(
        {"filename": file.filename, "password": password})
    filestorage.upload_file(file, file_id)
    return {"file_id": str(file_id)}


@app.get("/api/file_info/{file_id}")
async def file_info(file_id: str):
    file_info = db.get_filename_and_expiry(file_id)
    if (file_info):
        passwordneeded = db.check_password_needed(file_id)
        timeleft = file_info['expiry'] - datetime.utcnow()
        hours = timeleft.seconds//3600
        minutes = (timeleft.seconds//60) % 60
        return {"filename": file_info["filename"], "passwordneeded": passwordneeded, "hours": hours, "minutes": minutes}
    else:
        raise HTTPException(404, "File not found")


@app.post("/api/gettoken/{file_id}")
async def get_token(file_id: str, request: Request):
    json = await request.json()
    if not db.check_password(file_id, json["password"]):
        raise HTTPException(403, "Wrong password")
    token = token_urlsafe()  # generate token.
    db.add_token(file_id, token)  # add token to file document in db
    return {"token": token}


@app.get('/api/downloadfilewithtoken/{file_id}/{token}')
async def send_file_with_token(file_id, token):
    tokencorrect = db.check_token(file_id, token)
    if tokencorrect:
        tokencorrect = db.remove_token(file_id, token)
        filename = db.get_filename(file_id)
        return filestorage.download_file(file_id, filename)
    else:
        raise HTTPException(403, "Token invalid")


@app.get('/api/downloadfile/{file_id}')
async def send_file(file_id):
    if db.check_password_needed(file_id):
        raise HTTPException(403, "Password required")
    filename = db.get_filename(file_id)
    return filestorage.download_file(file_id, filename)

# Scheduling purging of files


scheduler = BackgroundScheduler()
scheduler.add_job(filestorage.purge_files, "interval", minutes=1)
scheduler.start()
