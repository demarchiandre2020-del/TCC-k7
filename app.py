from flask import Flask, render_template
import mysql.connector as mysql
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Establish a database connection with error handling.
    Returns a connection object or None if connection fails.
    """
    try:
        connection = mysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "username"),
            password=os.getenv("DB_PASSWORD", "password"),
            database=os.getenv("DB_NAME", "almoxarifado"),
            autocommit=True,
            connection_timeout=10
        )
        return connection
    except Error as e:
        logger.error(f"Database connection failed: {e}")
        return None


@app.route("/")
def index():
    """
    Index route - displays data from the database.
    """
    connection = None
    data = []
    try:
        connection = get_db_connection()
        if connection is None:
            logger.warning("Index: Database connection unavailable")
            return render_template("index.html", data=data, error="Database connection failed")
        
        cursor = connection.cursor(dictionary=True)
      
        cursor.execute("SELECT * FROM items")
        data = cursor.fetchall()
        cursor.close()
    except Error as e:
        logger.error(f"Index - Database error: {e}")
        data = []
        return render_template("index.html", data=data, error="Failed to retrieve data")
    finally:
        if connection and connection.is_connected():
            connection.close()

    return render_template("index.html", data=data)


@app.route("/estoque")
def estoque():
    """
    Estoque route - displays inventory data.
    """
    connection = None
    data = []
    try:
        connection = get_db_connection()
        if connection is None:
            logger.warning("Estoque: Database connection unavailable")
            return render_template("estoque.html", data=data, error="Database connection failed")
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM estoque")
        data = cursor.fetchall()
        cursor.close()
    except Error as e:
        logger.error(f"Estoque - Database error: {e}")
        data = []
        return render_template("estoque.html", data=data, error="Failed to retrieve inventory data")
    finally:
        if connection and connection.is_connected():
            connection.close()

    return render_template("estoque.html", data=data)


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {error}")
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", "5000"))
    )
