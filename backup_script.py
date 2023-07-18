import os
import subprocess
import datetime
import psycopg2
import time
from datetime import timedelta
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
USER_DB = os.getenv('USER_DB')
PASSWORD_DB = os.getenv('PASSWORD_DB')
HOST_DB = os.getenv('HOST_DB')
PORT_DB = os.getenv('PORT_DB')

USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

LOG_URL = os.getenv('LOG_URL')

def send_log(message, log_level, system_name):
    url = LOG_URL  # Замените на URL вашего сервера, если он развернут не локально
    auth = HTTPBasicAuth(USERNAME, PASSWORD)  # Замените на ваши данные для аутентификации
    params = {
        "message": message,
        "log_level": log_level,
        "system_name": system_name
    }
    response = requests.post(url, auth=auth, params=params)
    if response.status_code == 200:
        print("Log successfully sent")
    else:
        print(f"Failed to send log, status code: {response.status_code}, message: {response.text}")


def log_to_db(descr, log_level):
    sql = """
    INSERT INTO public.logs_table
    (descr, dt, log_level)
    VALUES(%s, CURRENT_TIMESTAMP, %s);
    """

    try:
        con = psycopg2.connect(database=DB_NAME, user=USER_DB,
                               password=PASSWORD_DB, host=HOST_DB, port=PORT_DB)
        cursor = con.cursor()

        cursor.execute(sql, (descr, log_level))

        con.commit()
        
        send_log(descr,log_level,'KS_BACKUP')
        
        print("Log successfully written to database")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error while working with PostgreSQL: {error}")

    finally:
        if con is not None:
            cursor.close()
            con.close()


# параметры подключения к БД
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('FDB_DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')



# путь до утилиты gbak
gbak_path = "/usr/local/firebird/bin/gbak"

# путь до каталога, куда будут сохраняться резервные копии
backup_dir = "/ext_ssd_500/ks_backup"


def backup_and_clean():
    # формируем имя файла резервной копии
    backup_file = f"{backup_dir}/backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.fbk"

    # команда для создания резервной копии
    command = f'{gbak_path} -b -v -user {db_user} -password {db_password} {db_host}/{db_port}:{db_name} {backup_file}'

    # запускаем процесс создания резервной копии
    process = subprocess.Popen(command, shell=True)
    output, error = process.communicate()

    if process.returncode != 0:
        print(f"Ошибка при создании резервной копии: {error}")
        log_to_db(f"Ошибка при создании резервной копии: {error}", 'ERROR')
    else:
        print(f"Резервная копия успешно создана: {backup_file}")
        log_to_db(f"Резервная копия успешно создана: {backup_file}", 'INFO')

        # Удаление резервных копий, которые старше 3 дней
        command = f'find {backup_dir} -name "*.fbk" -mtime +3 -delete'
        process = subprocess.Popen(command, shell=True)
        output, error = process.communicate()

        if process.returncode != 0:
            print(f"Ошибка при удалении старых резервных копий: {error}")
            log_to_db(f"Ошибка при удалении старых резервных копий: {error}", 'ERROR')
        else:
            print("Старые резервные копии успешно удалены.")
            log_to_db("Старые резервные копии успешно удалены.", 'INFO')


while True:
    # текущее время
    now = datetime.datetime.now()
    
    # время начала и окончания резервного копирования
    start_time = now.replace(hour=8, minute=0)
    end_time = now.replace(hour=18, minute=30)

    # проверяем, находится ли текущее время в заданном интервале
    if start_time.time() <= now.time() <= end_time.time():
        # выполняем резервное копирование и чистку
        backup_and_clean()

        # следующее резервное копирование через 1 час
        sleep_time = 3600
    else:
        # если текущее время больше времени окончания, то следующее резервное копирование
        # начнется на следующий день в 8:00
        if now.time() > end_time.time():
            next_backup = start_time + timedelta(days=1) 
        else:  # иначе, следующее резервное копирование начнется сегодня в 8:00
            next_backup = start_time 

        sleep_time = (next_backup - now).seconds

    time.sleep(sleep_time)
