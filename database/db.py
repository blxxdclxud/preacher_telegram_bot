import sqlite3
from CONSTANTS import ROOT_PATH

connection = sqlite3.connect(ROOT_PATH + "database/users.db")
cursor = connection.cursor()


def get_all_users(mailing=False):
    if not mailing:
        result = cursor.execute("SELECT user_id FROM users").fetchall()
    else:
        result = cursor.execute("SELECT user_id FROM users WHERE mailing = True").fetchall()
    return [i[0] for i in result]


def add_new_user(user_id):
    cursor.execute("INSERT INTO users(user_id) VALUES(?)", (user_id,))
    connection.commit()


def get_mailing_status_of_user(user_id):
    result = cursor.execute("SELECT mailing FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return result[0]


def change_mailing_status_of_user(user_id):
    cursor.execute("UPDATE users SET mailing = NOT mailing WHERE user_id = ?", (user_id,))
    connection.commit()


def add_to_posted_duas(link):
    cursor.execute("INSERT INTO posted_duas(link) VALUES(?)", (link,))
    connection.commit()


def get_posted_duas():
    result = cursor.execute("SELECT link FROM posted_duas").fetchall()
    return set(i[0] for i in result)
