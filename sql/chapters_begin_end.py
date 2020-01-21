import pymysql
conn = pymysql.connect(host = "localhost", user= "root", db = "quran" )



def main():
    cursor = conn.cursor()
    sql = ''' select q1.sura as 'sura', q1.`index` as 'start', (q2.`index` - 1) as 'end' from quran_text as q1, quran_text as q2 where q1.aya=1 and q2.aya=1 and q2.sura = q1.sura + 1'''
    cursor.execute(sql)
    with open("chapters_begin_end.txt", 'w', encoding="utf-8") as outFile:
        for row in cursor:
            outFile.write(f"{row[0]} {row[1]} {row[2]}\n")
        outFile.write(f"114 6231 6236\n")
main()