from flask import Flask, render_template, request
import requests
from requests.exceptions import RequestException
import mysql.connector

app = Flask(__name__)

statuses = {
    200: "Website is Authentic",
    301: "Permanent Redirect",
    302: "Temporary Redirect",
    404: "Not Found",
    500: "Internal Server Error",
    503: "Service Unavailable"
}

# Define your MySQL connection parameters
host = "localhost"  # The hostname of your MySQL server
user = "root"       # Your MySQL username
password = "root"   # Your MySQL password
database = "appproject"  # The name of the database you want to connect to

# Create a connection to the MySQL server
connection = mysql.connector.connect(
    host=host,
    user=user,
    password=password
)

# Create a cursor to execute SQL queries
cursor = connection.cursor()

# Create the appproject database if it doesn't exist
cursor.execute("CREATE DATABASE IF NOT EXISTS appproject")

# Use the appproject database
cursor.execute("USE appproject")

# Create the History table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS History (
        SrNo SERIAL,
        WEBSITE VARCHAR(100),
        ENTRY_TIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
connection.commit()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        website_urls = request.form.get("website_urls")
        if website_urls:
            website_urls = website_urls.split(',')
            results = []

            for url in website_urls:
                try:
                    web_response = requests.get(url)
                    status = statuses.get(web_response.status_code, "Unknown Status")
                    insert_query = "INSERT INTO History (WEBSITE) VALUES (%s)"
                    data_to_insert = (url,)

                    # Execute the INSERT statement
                    cursor.execute(insert_query, data_to_insert)

                    # Commit the changes to the database
                    connection.commit()

                except RequestException:
                    status = "Error"

                # Insert data into the MySQL table
                results.append((url, status))

            # Delete duplicate entries based on the WEBSITE column and rearrange SrNo
            cursor.execute("""
                DELETE h1
                FROM History h1
                JOIN (
                    SELECT WEBSITE, MAX(SrNo) AS max_SrNo
                    FROM History
                    GROUP BY WEBSITE
                ) h2 ON h1.WEBSITE = h2.WEBSITE AND h1.SrNo < h2.max_SrNo
            """)
            cursor.execute("SET @serial = 0;")
            cursor.execute("UPDATE History SET SrNo = @serial := @serial + 1;")
            connection.commit()

            return render_template("index.html", results=results)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
