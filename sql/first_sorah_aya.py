import pymysql
conn = pymysql.connect(host = "localhost", user= "root", db = "quran" )


selectSql = '''select CONCAT(
    t1.text, ' ',
    t2.text
    ) as text, t1.`index`, t1.aya, t1.sura from 
    quran_text as t1,
    quran_text as t2
    where 
        t1.aya = 1 and
        t2.aya = 2
        and t1.sura = t2.sura
    '''
# selectSql = '''select CONCAT(
#     t1.text, ' ',
#     t2.text, ' ',
#     t3.text
#     ) from 
#     quran_text as t1,
#     quran_text as t2,
#     quran_text as t3
#     where 
#         t1.aya = 1 and
#         t2.aya = 2 and
#         t3.aya = 3 and
#         and t1.sura = t2.sura
#         and t2.sura = t3.sura
#     '''
createTableSql = f'''create table startOnly {selectSql}'''
print(createTableSql)
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
# sql = createTableSql.format(name=f"quran_text_2", selecttemp=main(2, template))
# print(sql)