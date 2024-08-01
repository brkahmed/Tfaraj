import sqlite3
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_anime(anime):
    conn = sqlite3.connect('animex.db', check_same_thread=False)
    cur = conn.cursor()
    
    try:
        print(f'ANIME: {anime["name"]}')
        try:
            mal_id = int(anime['MAL id'])
        except ValueError:
            mal_id = None
        
        # Begin transaction
        cur.execute('BEGIN TRANSACTION')
        
        cur.execute('INSERT INTO anime(mal_id, name) VALUES(?, ?)', (mal_id, anime['name']))
        an_id = cur.lastrowid
        
        for ep, source in anime['episodes'].items():
            cur.execute('INSERT INTO episode(number, anime_id) VALUES(?, ?)', (float(ep), an_id))
            ep_id = cur.lastrowid
            
            urls = source['watch']
            cur.executemany('INSERT INTO source(episode_id, name, url) VALUES(?, ?, ?)', 
                            [(ep_id, name, url) for name, url in urls.items()])
        
        # Commit transaction
        conn.commit()
    
    except Exception as e:
        # Rollback transaction in case of error
        conn.rollback()
        print(f"An error occurred: {e}")
    
    finally:
        cur.close()
        conn.close()

def main():
    START = time.time()
    
    # Load the JSON data
    with open('result.json') as f:
        data: list[dict] = json.load(f)
    
    # Use ThreadPoolExecutor to manage threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit tasks to the thread pool
        futures = [executor.submit(process_anime, anime) for anime in data]
        
        # Wait for all threads to complete
        for future in as_completed(futures):
            future.result()  # This will re-raise any exceptions raised in the thread
    
    print(f'Took: {time.time() - START}s')

if __name__ == "__main__":
    main()
