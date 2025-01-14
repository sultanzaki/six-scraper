# scraper.py
import tweepy
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Konfigurasi Tweepy dari environment variables
api_key = os.getenv('API_KEY')
api_secret_key = os.getenv('API_SECRET_KEY')
access_token = os.getenv('ACCESS_TOKEN')
access_token_secret = os.getenv('ACCESS_TOKEN_SECRET')
bearer_token = os.getenv('BEARER_TOKEN')

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret_key,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# Konfigurasi cookies dan headers
cookies = {
    'khongguan': os.getenv('COOKIES_KHONGGUAN')
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Fungsi untuk memuat nilai terakhir dari file JSON
def load_last_grades():
    try:
        with open('last_grades.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Fungsi untuk menyimpan nilai terbaru ke file JSON
def save_last_grades(grades):
    with open('last_grades.json', 'w') as f:
        json.dump(grades, f)

# Fungsi untuk mencatat log aktivitas
def log_activity(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')  # Output ke console (untuk log di GitHub Actions)
    with open('scraper.log', 'a') as f:
        f.write(f'[{timestamp}] {message}\n')

# Fungsi untuk memeriksa nilai baru
def check_grades():
    try:
        # Load nilai terakhir
        last_grades = load_last_grades()
        
        # Mengirim permintaan ke website akademik
        url = "https://six.itb.ac.id/app/mahasiswa:11221051/statusmhs"
        response = requests.get(url, cookies=cookies, headers=headers)
        
        if response.status_code != 200:
            log_activity(f'Failed to fetch page: Status code {response.status_code}')
            return
        
        # Parsing HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            log_activity('Table not found in the response')
            return
        
        current_grades = {}
        rows = tables[1].find_all('tr')[1:]  # Abaikan header row
        
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 6:
                mata_kuliah = columns[1].text.strip()
                nilai = columns[5].text.strip()
                current_grades[mata_kuliah] = nilai
        
        # Memeriksa nilai baru
        for mata_kuliah, nilai in current_grades.items():
            if mata_kuliah in last_grades:
                last_nilai = last_grades[mata_kuliah]
                if not last_nilai and nilai:
                    tweet = f"Nilai mata kuliah {mata_kuliah} sudah keluar, selamat melihat di SIX!"
                    try:
                        client.create_tweet(text=tweet)
                        log_activity(f'Successfully tweeted about new grade for {mata_kuliah}')
                    except Exception as e:
                        log_activity(f'Error posting tweet: {str(e)}')
        
        # Simpan nilai terbaru
        save_last_grades(current_grades)
        log_activity('Grade check completed successfully')
        
    except Exception as e:
        log_activity(f'Error during execution: {str(e)}')

if __name__ == "__main__":
    check_grades()
