from fastapi import FastAPI, Path, Query, HTTPException
import sqlite3

app = FastAPI()

def execute_db_querie(querie: str, paramaters: tuple):
    with sqlite3.connect('database.db') as db:
        db.row_factory = sqlite3.Row
        cur = db.cursor().execute(querie, paramaters)
    return cur
    
@app.get('/anime/{id}')
def get_anime_by_id(
    id: int = Path(gt=0)
):
    cur = execute_db_querie('SELECT * FROM anime WHERE anime.id=?', (id,))
    result = cur.fetchone()
    if not result: raise HTTPException(404, 'Not found')
    
    response = {
        'id': result['id'],
        'mal_id': result['mal_id'],
        'name': result['name']
    }
    return response

@app.get('/anime')
def get_anime_by_name(
    name: str = Query(min_length=5),
    limit: int = Query(10, gt=0),
    offset: int = Query(0, ge=0)
):
    cur = execute_db_querie(
        'SELECT * FROM anime WHERE anime.name LIKE ? LIMIT ? OFFSET ?',
        (f'{name}%', limit, offset)
    )
    result = cur.fetchall()
    if not result: raise HTTPException(404, 'Not found')
    
    response = [
        {
            'id': row['id'],
            'mal_id': row['mal_id'],
            'name': row['name']
        } for row in result
    ]
    return response

@app.get('/episode/{id}')
def get_episode_by_id(
    id: int = Path(gt=0)
):
    cur = execute_db_querie('SELECT * FROM episode WHERE episode.id=?', (id,))
    result = cur.fetchone()
    if not result: raise HTTPException(404, 'Not found')
    
    response = {
        'id': result['id'],
        'number': result['number'],
        'anime_id': result['anime_id']
    }
    return response

@app.get('/episode')
def get_episode_by_anime_id(
    anime_id: int = Query(gt=0),
    limit: int = Query(10, gt=0),
    offset: int = Query(0, ge=0)
):
    cur = execute_db_querie(
        'SELECT episode.id, episode.number FROM episode WHERE episode.anime_id=? LIMIT ? OFFSET ?',
        (anime_id, limit, offset)
    )
    result = cur.fetchall()
    if not result: raise HTTPException(404, 'Not found')
    
    response = [
        {
            'id': row['id'],
            'number': row['number'],
            'anime_id': anime_id
        } for row in result
    ]
    return response

@app.get('/source')
def get_source_by_episode_id(
    episode_id: int = Query(gt=0)
):
    cur = execute_db_querie('SELECT * FROM source WHERE source.episode_id=?', (episode_id,))
    result = cur.fetchall()
    if not result: raise HTTPException(404, 'Not found')
    
    response = [
        {
            'id': row['id'],
            'name': row['name'],
            'url': row['url'],
            'episode_id': episode_id
        } for row in result
    ]
    return response
