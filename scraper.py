import tweepy
import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime

# Konfigurasi Tweepy dari environment variables
api_key = os.environ.get('API_KEY')  # Disesuaikan dengan nama env di Actions
api_secret_key = os.environ.get('API_SECRET_KEY')
access_token = os.environ.get('ACCESS_TOKEN')
access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')
bearer_token = os.environ.get('BEARER_TOKEN')

client = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=api_key,
    consumer_secret=api_secret_key,
    access_token=access_token,
    access_token_secret=access_token_secret
)

# Konfigurasi cookies dari environment variable
cookies = {
    'khongguan': os.environ.get('COOKIES_KHONGGUAN')
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def log_activity(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')

def load_last_grades():
    try:
        if not os.path.exists('last_grades.json'):
            log_activity('last_grades.json not found, creating new file')
            with open('last_grades.json', 'w') as f:
                json.dump({
                    "Big Data untuk Pertanian": "",
                    "Teknologi Produksi Bersih": "",
                    "Instrumentasi dan Pengendalian Sistem Hayati": "",
                    "Tugas Akhir Penelitian": "",
                    "Pemasaran Ramah Lingkungan": "",
                    "Manajemen Rekayasa Industri": ""
                }, f)
            return {}
        
        with open('last_grades.json', 'r') as f:
            content = f.read()
            if not content.strip():
                log_activity('last_grades.json is empty, initializing with empty dict')
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        log_activity(f'Error reading last_grades.json: {str(e)}. Creating new file.')
        with open('last_grades.json', 'w') as f:
            json.dump({}, f)
        return {}
    except Exception as e:
        log_activity(f'Unexpected error reading last_grades.json: {str(e)}')
        return {}

def save_last_grades(grades):
    try:
        with open('last_grades.json', 'w') as f:
            json.dump(grades, f, indent=2)
        log_activity('Successfully saved grades to last_grades.json')
    except Exception as e:
        log_activity(f'Error saving grades: {str(e)}')

def check_grades():
    try:
        log_activity('Starting grade check')
        last_grades = load_last_grades()
        log_activity(f'Loaded last grades: {last_grades}')
        
        url = "https://six.itb.ac.id/app/mahasiswa:11221051/statusmhs"
        response = requests.get(url, cookies=cookies, headers=headers)
        
        if response.status_code != 200:
            log_activity(f'Failed to fetch page: Status code {response.status_code}')
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        if len(tables) < 2:
            log_activity('Table not found in the response')
            return
        
        current_grades = {}
        rows = tables[1].find_all('tr')[1:]
        
        for row in rows:
            columns = row.find_all('td')
            if len(columns) >= 6:
                mata_kuliah = columns[1].text.strip()
                nilai = columns[5].text.strip()
                current_grades[mata_kuliah] = nilai
                log_activity(f'Found grade for {mata_kuliah}: {nilai}')
        
        # Check for new grades
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
        
        save_last_grades(current_grades)
        log_activity('Grade check completed successfully')
        
    except Exception as e:
        log_activity(f'Error during execution: {str(e)}')
        raise  # Re-raise exception untuk debugging

if __name__ == "__main__":
    check_grades()
