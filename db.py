import psycopg2 as psql
from pybot import cur, con
from contextlib import ExitStack

def resetdb(update = None, context = None):
    with ExitStack() as stack:
        stack.callback(con.commit)
        cur.execute("""
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS og;
            DROP TABLE IF EXISTS house;

            CREATE TABLE users (
                chat_id INTEGER NOT NULL PRIMARY KEY UNIQUE
            );

            CREATE TABLE og (
                id INTEGER NOT NULL,
                house_id INTEGER NOT NULL,
                points INTEGER DEFAULT 0
            );

            CREATE TABLE house (
                id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                name TEXT UNIQUE
            );

            INSERT INTO house VALUES (1, 'Ilent');
            INSERT INTO house VALUES (2, 'Barg');
            INSERT INTO house VALUES (3, 'Etlas');
            INSERT INTO house VALUES (4, 'Aikon');
            INSERT INTO house VALUES (5, 'Geolog');
            INSERT INTO house VALUES (6, 'Trewitt');

            INSERT INTO
                users (chat_id)
            VALUES
                (129464681);
        """)

        for house_id in range(1, 7):
            for og_id in range(1, 7):
                cur.execute(f"""
                    INSERT INTO
                        og (id, house_id)
                    VALUES
                        ({og_id}, {house_id})
                """)

def resetpoints():
    cur.execute("UPDATE og SET points = 0")
    con.commit()

def legitUser(chat_id):
    cur.execute(f"SELECT * FROM users WHERE chat_id = {chat_id}")
    return cur.fetchone() is not None

def adduser(chat_id):
    with ExitStack() as stack:
        stack.callback(con.commit)
        cur.execute(f'INSERT INTO users (chat_id) VALUES ({chat_id})')

def getHouse(house_id):
    cur.execute(f'SELECT name FROM house WHERE id = {house_id}')
    return cur.fetchone()[0]

def getPoints(house_id = None, og_id = None, mode = 'house'):
    where = ''
    order = ''
    if house_id and og_id:
        if house_id.isnumeric():
            where = f'WHERE house_id = {house_id} AND og.id = {og_id}'
        else:
            where = f'WHERE house_id LIKE {house_id}% AND og.id = {og_id}'
    elif mode == 'house':
        order = 'ORDER BY house_id ASC, og.id ASC'
    else:
        order = 'ORDER BY points DESC'
    cur.execute(f'''
    SELECT og.id, points, name
    FROM og
    JOIN house ON (og.house_id = house.id)
    {where} {order}
    ''')
    return cur.fetchall()

def addPoints(og_list, amt):
    if not og_list:
        return
    query = ''
    where = []
    for og in og_list:
        og_id = int(og[1])
        house = og[0]
        where.append(f"(og.id = {og_id} AND name LIKE '{house}%')")
        query += f"UPDATE og o SET points = points + {amt} WHERE EXISTS (SELECT 1 FROM og JOIN house ON (o.house_id = house.id) WHERE o.id = {og_id} AND name LIKE '{house}%');\n"
    with ExitStack() as stack:
        stack.callback(con.commit)
        cur.execute(query)
    cur.execute(f"SELECT og.id, house.name, og.points FROM og JOIN house on (house_id = house.id) WHERE {' OR '.join(where)}")
    return cur.fetchall()

def getHouses():
    cur.execute('SELECT name FROM house')
    return [i[0][0] for i in cur.fetchall()]

def addAll(amt):
    cur.execute(f'UPDATE og SET points = points + {amt}')
    con.commit()
