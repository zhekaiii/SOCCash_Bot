import psycopg2 as psql
from pybot import cur, con, logger, BASE_AMOUNT
mychatid = 0  # Your chat id, can use /me to find out
myusername = ''  # Your username, without the @


def resetdb(update=None, context=None):
    # create/reset database
    try:
        cur.execute(f"""
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS og;
            DROP TABLE IF EXISTS house;

            CREATE TABLE users (
                chat_id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                role INTEGER DEFAULT 0,
                username TEXT
            );

            CREATE TABLE og (
                id INTEGER NOT NULL,
                house_id INTEGER NOT NULL,
                points INTEGER DEFAULT {BASE_AMOUNT}
            );

            CREATE TABLE house (
                id INTEGER NOT NULL PRIMARY KEY UNIQUE,
                name TEXT UNIQUE
            );

            CREATE TABLE logs (
                id SERIAL NOT NULL PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                og_id INTEGER,
                house_id INTEGER,
                amount INTEGER NOT NULL,
                time TIMESTAMPTZ NOT NULL DEFAULT NOW()
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
                ({mychatid});
        """)

        for house_id in range(1, 7):  # Edit accordingly to how many houses you have
            for og_id in range(1, 7):  # Edit accoridngly to how many OGs per house you have
                cur.execute(f"""
                    INSERT INTO
                        og (id, house_id)
                    VALUES
                        ({og_id}, {house_id})
                """)
    except Exception as e:
        con.rollback()
        raise e  # to throw an error so the logger will log. otherwise unnecessary


def resetpoints():
    cur.execute(f"UPDATE og SET points = {BASE_AMOUNT}; DELETE FROM logs;")
    con.commit()


def legitUser(chat_id):
    cur.execute(f"SELECT role FROM users WHERE chat_id = {chat_id}")
    role = cur.fetchone()
    if role is None:
        return None
    role = role[0]
    return {0: "OComm", 1: "Station Master"}[role]


def isOComm(chat_id):
    cur.execute(
        f"SELECT (role = 0) AS isOcomm FROM users WHERE chat_id = {chat_id}")
    res = cur.fetchone()
    return res[0] if res else False


def addUser(chat_id, ocomm, username):
    username = f"'{username}'" if username else 'NULL'
    cur.execute(
        f"INSERT INTO users (chat_id, role, username) VALUES ({chat_id}, {0 if ocomm else 1}, {username}) ON CONFLICT DO NOTHING RETURNING 1")
    con.commit()
    return cur.fetchone() is not None


def getHouse(house_id):
    cur.execute(f'SELECT name FROM house WHERE id = {house_id}')
    return cur.fetchone()[0]


def getlogs(page=0):
    cur.execute('SELECT COUNT(*) FROM logs')
    count = cur.fetchone()[0]
    if count == 0:
        return [0, None]
    cur.execute(
        f'''SELECT COALESCE (u.username, cast (l.chat_id as text)) AS user, og_id, house_id, amount, time
        FROM logs l
        LEFT JOIN users u ON u.chat_id = l.chat_id
        ORDER BY time
        OFFSET {page * 20}
        LIMIT 20''')
    res = cur.fetchall()
    return [count, res] if res else [0, None]


def getPoints(house_id=None, og_id=None, mode='house'):
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


def addPoints(og_list, amt, user_id):
    if not og_list:
        return
    query = ''
    where = []
    for og in og_list:
        og_id = int(og[1])
        house = og[0].upper()
        where.append(f"(og.id = {og_id} AND name LIKE '{house}%')")
        query += f"UPDATE og o SET points = points + {amt} WHERE EXISTS (SELECT 1 FROM og JOIN house ON (o.house_id = house.id) WHERE o.id = {og_id} AND name LIKE '{house}%');\n"
        query += f"INSERT INTO logs (chat_id, amount, og_id, house_id) VALUES ({user_id}, {amt}, {og_id}, (SELECT id FROM house WHERE name LIKE '{house}%'));\n"
    try:
        cur.execute(query)
        con.commit()
    except Exception as e:
        con.rollback()
        raise e
    cur.execute(
        f"SELECT og.id, house.name, og.points FROM og JOIN house on (house_id = house.id) WHERE {' OR '.join(where)}")
    return cur.fetchall()


def getHouses():
    cur.execute('SELECT name FROM house')
    return [i[0][0] for i in cur.fetchall()]


def addAll(amt, user_id):
    cur.execute(f'''
    UPDATE og SET points = points + {amt};
    INSERT INTO logs (chat_id, amount) VALUES ({user_id}, {amt});
    ''')
    con.commit()


def getAdmins():
    cur.execute('SELECT chat_id, username, role FROM users')
    return cur.fetchall()


def revokeAdmin(idList):
    idList = [i for i in idList]
    where = f'({",".join(idList)})'
    cur.execute(
        f'DELETE FROM users WHERE chat_id IN {where} RETURNING username')
    revoked = [username[0] for username in cur.fetchall()]
    cur.execute('SELECT * FROM users')
    if cur.fetchall() is None:
        # as a precautionary measure
        cur.execute(
            f'''INSERT INTO users (chat_id, username) VALUES ({mychatid}, '{myusername}')''')
    con.commit()
    return revoked
