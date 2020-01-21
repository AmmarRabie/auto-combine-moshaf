import sys
sys.path.append("../")
from dbmanager import DbManager as DB

import pymysql
conn = pymysql.connect(host = "localhost", user= "root", db = "quran" )


template = '''SELECT CONCAT({t}) as "text", a1.`index`, a1.`sura`, a1.`aya` FROM {f} WHERE {w}'''
createTemp = '''CREATE TABLE {name} {selecttemp}'''
def main(ngram, temp):
    cursor = conn.cursor()
    if ngram <= 1:
        return
    
    t = "a1.`text`"
    f = "quran_text as a1"
    w = "TRUE"
    for a in range(2, ngram + 1): # if ngram = 2, you need a1, a2
        an = f"a{a}"
        t += f", ' ', {an}.`text`"
        f += f", quran_text as {an}"
        w += f" and {an}.`index`=a1.`index`+{a - 1}"
    return temp.format(t=t, f=f, w=w)
    # cursor.execute('SELECT * FROM quran_text where `index`=2')
sql = createTemp.format(name=f"quran_text_2", selecttemp=main(2, template))
# print(sql)