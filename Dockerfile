# Базовый образ
FROM jacobalberty/firebird:2.5-ss

# Установка Python
RUN apt-get update && apt-get install -y python3 python3-pip 


RUN pip3 install psycopg2-binary python-dotenv requests
# Создание каталога для скрипта
RUN mkdir -p /scripts

# Копирование скрипта в контейнер
COPY .env /scripts/.env
COPY backup_script.py /scripts/backup_script.py

COPY healthcheck.py /scripts/healthcheck.py

# Создание каталога для резервных копий
RUN mkdir -p /ext_ssd_500/ks_backup

# Предоставление прав на запуск скрипта
RUN chmod +x /scripts/backup_script.py

RUN ln -snf /usr/share/zoneinfo/Europe/Moscow /etc/localtime && echo Europe/Moscow > /etc/timezone


# Добавление проверки состояния сервиса
HEALTHCHECK --interval=1h --timeout=3s \
  CMD python3 /scripts/healthcheck.py || exit 1

# Запуск скрипта
CMD ["python3", "/scripts/backup_script.py"]
