import sys
sys.path.append("../")
from dbmanager import DbManager as DB

import pymysql
conn = pymysql.connect(host = "localhost", user= "root", db = "quran" )


def main():
    cursor = conn.cursor()
    sql = "select text from startonly"
    cursor.execute(sql)
    with open('quran-startonly-simple-clean.text', 'w', encoding="utf-8") as outFile:
        for row in cursor:
            outFile.write(preprocess(row[0]))
            outFile.write('\n')
def preprocess(aya):
    return aya[23:]
if __name__ == "__main__":
    main()