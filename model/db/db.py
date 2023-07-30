#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Link
# https://sqlitestudio.pl/index.rvt
# https://www.sqlitetutorial.net
# https://www.sqlitetutorial.net/sqlite-python
# https://www.w3schools.com/sql/default.asp

import os
import sqlite3


class Db:
    """SqLite-Datenbankintegration für die Verwaltung der Uebersetzungen."""

    def __init__(self, file_path=None):
        if file_path is None:
            absolute_path = (os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')
            self._file_path = absolute_path + '/db.sqlite'
        else:
            self._file_path = file_path

        self._db_connection = None
        self.connect()

    def connect(self):
        """Erstelle eine Verbindung zur SqLite-Datenbank."""
        try:
            self._db_connection = sqlite3.connect(self._file_path)
        except Exception as e:
            print('error db.connect:', e)

    def insert(self, value):
        """Einfügen von neuen Einträgen in die Datenbank."""
        try:
            sql = '''INSERT INTO translation(src, dest, src_lang, dest_lang)
                             VALUES(?,?,?,?)'''
            cursor = self._db_connection.cursor()
            cursor.execute(sql, value)
            self._db_connection.commit()
            # print(cursor.lastrowid)
            return cursor.lastrowid
        except Exception as e:
            print('error db.insert:', e)
            return -1

    def select_all(self):
        """Selektierung sämtlicher Einträge."""
        try:
            sql = '''SELECT * FROM translation ORDER BY id DESC'''
            cursor = self._db_connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print('error db.select_all:', e)
            return []

    def search(self, term):
        """Suche in der Datenbank nach Uebersetzungen mit dem Inhalt von term."""
        try:
            sql = '''SELECT * FROM translation WHERE 
                     src LIKE '%{:s}%' OR dest LIKE '%{:s}%' ORDER BY id DESC'''.format(term, term)
            cursor = self._db_connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print('error db.sarch:', e)
            return []

    def delete(self, id):
        """Lösche den Datensatz mit der id"""
        try:
            sql = '''DELETE FROM translation WHERE id=?'''
            cursor = self._db_connection.cursor()
            cursor.execute(sql, [id])

            self._db_connection.commit()
        except Exception as e:
            print('error db.delete:', e)


if __name__ == '__main__':
    db = Db()
    db.connect()
    # db.delete(174)
    db.insert(['hallo', 'hello', 'de', 'en'])
    # print(db.select_all()
    search = db.search('hello')
    print(len(search), search)



