from flask import Flask, request
import boto3
import psycopg2
import os
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
    aws_secret_access_key=os.environ['AWS_SECRET_KEY'],
)

bucket = os.environ['S3_BUCKET']

conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASS']
)

@app.route("/")
def home():
    return "AWS DevOps Demo App Running!"

@app.route("/upload", methods=["POST"])
def upload():

    file = request.files['file']

    s3.upload_fileobj(file, bucket, file.filename)

    cur = conn.cursor()
    cur.execute("INSERT INTO files(name) VALUES(%s)", (file.filename,))
    conn.commit()

    return "File Uploaded Successfully"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)