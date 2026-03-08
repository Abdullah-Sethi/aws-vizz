from flask import Flask, request
import boto3
import psycopg2
import os

app = Flask(__name__)

# --- Initialize S3 only if secrets are present ---
s3 = None
bucket = None
if os.environ.get("AWS_ACCESS_KEY") and os.environ.get("AWS_SECRET_KEY") and os.environ.get("S3_BUCKET"):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
        aws_secret_access_key=os.environ['AWS_SECRET_KEY'],
    )
    bucket = os.environ['S3_BUCKET']

# --- Initialize RDS connection ---
try:
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASS'],
        port=int(os.environ.get('DB_PORT', 5432))
    )
except Exception as e:
    conn = None
    db_error = str(e)
else:
    db_error = None

# --- Routes ---

@app.route("/")
def home():
    return "AWS DevOps Demo App Running!"

@app.route("/check-db")
def check_db():
    if not conn:
        return f"Failed to connect to RDS: {db_error}", 500
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        return "RDS connection verified successfully!"
    except Exception as e:
        return f"RDS connection failed: {e}", 500

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return "No file provided", 400
    file = request.files['file']

    if s3 and bucket:
        # Upload to S3
        s3.upload_fileobj(file, bucket, file.filename)
    else:
        # fallback: save locally
        UPLOAD_FOLDER = "uploads"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, file.filename))

    # Save filename in RDS
    if conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS files(name TEXT);")
        cur.execute("INSERT INTO files(name) VALUES(%s)", (file.filename,))
        conn.commit()

    return "File Uploaded Successfully"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)