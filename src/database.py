import mysql.connector
from json import dumps

# Konfigurasi database
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Ganti dengan username MySQL kamu
    "password": "",  # Ganti dengan password MySQL kamu
    "database": "gptscraper"  # Ganti dengan nama database yang ingin digunakan
}

conn = mysql.connector.connect(**DB_CONFIG)
def create_connection():
    try:
        if conn.is_connected():
            print("Koneksi ke MySQL berhasil!")
        return conn
    except mysql.connector.Error as e:
        print(f"Error saat menghubungkan ke MySQL: {e}")
        return None

# Tes koneksi


def createTable():
    """Create Scraper table if doesnt exist"""
    if conn:
        cursor = conn.cursor()
        cursor.execute(""" 
CREATE TABLE IF NOT EXISTS Scraper (
                       scraper_id INT AUTO_INCREMENT PRIMARY KEY, link TEXT, title VARCHAR(255), text LONGTEXT, lowercased_text LONGTEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
); """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Scraper table berhasil dibuat")

def insertScraper(title, link, text, lowercased_text):
    """Add scraper to database"""
    text = dumps(text)
    lowercased_text = dumps(lowercased_text)
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO Scraper (title, link, text, lowercased_text) VALUES (%s,%s,%s,%s)"
        cursor.execute(query(title,link,text,lowercased_text))
        conn.commit()
        cursor.close()
        conn.close()
        print("Scraper berhasil dimasukkan")

def getScraper():
    """Get all scraper from database"""
    conn = create_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Scraper")
        scraper = cursor.fetchall()
        cursor.close()
        conn.close()
        return scraper

def getScraperById(scraperId):
    """Get single scraper by ID from database"""
    conn = create_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM Scraper WHERE scraper_id = %s"
        cursor.execute(query,(scraperId))
        scraper = cursor.fetchone()
        cursor.close()
        conn.close()
        return scraper
    
def updateScraperById(scraperId, title):
    """Update 1 scraper by ID from database"""
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        query = "UPDATE Scraper SET title = %s WHERE scraper_Id = %s"
        cursor.execute(query,(title, scraperId))
        conn.commit()
        cursor.close()
        conn.close()
        print("Scraper berhasil diupdate")

def deleteScraperById(scraperId):
    """Delete 1 scraper by ID from database"""
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        query = "DELETE FROM Scraper WHERE scraper_id = %s"
        cursor.execute(query,(scraperId))
        conn.commit()
        cursor.close()
        conn.close()
        print("Scraper berhasil dihapus")

if __name__ == "__main__":
    connection = create_connection()
    #createTable() jalanin kodenya untuk membuat table scraper
    if connection:
        connection.close()