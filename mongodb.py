from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

uri = os.getenv("MONGODB_URI")

try:
    # Set tls=True and tlsAllowInvalidCertificates=True to bypass local SSL certificate issues
    client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
    client.admin.command("ping")
    print("Connected to MongoDB Atlas successfully")

    db = client[os.getenv("DATABASE_NAME")]
    print("Database:", db.name)

except Exception as e:
    print("Connection failed")
    print(e)
