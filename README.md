# uRPC

Версия, развёрнутая на сервере: https://urpc.ximc.ru

## Запуск сервера на linux

Склонировать репозиторий uRPC, выбрать нужную ветку  и обновить подмодули:

	```
	git clone https://github.com/EPC-MSU/uRPC/
	git switch <ветка>
	git submodule update --init --recursive
	git submodule update --recursive
	```

### Запуск с помощью Docker (для системных администраторов)

1. Встать в директорию с проектом, собрать образ:
  `sudo docker build . -t <ТЕГ>`
  ТЕГ - это тег собираемого образа, можно присвоить любой удобный в зависимости от версии, например: `urpc-v07`, `urpc-v08`,
  `urpc-test` и т.д.

2. Удалить предыдущий контейнер, если он есть:
  `sudo docker rm -f <ТЕГ>`

3. Запустить:
`sudo docker run --name <ТЕГ> --publish 80xx:8888 --restart=always -d <ТЕГ>`
где `xx` - номер версии (например, `06` для версии 6, `07` для 7 и т.д.)

Команда запустит контейнер (с перезапуском) и пробросит порт 8888 из контейнера на порт 80xx запускающего контейнер сервера

### Классический запуск (для программистов)

1. Для начала нужно установить python3 и сопутствующие:

   ```
   sudo apt-get install python3
   sudo apt-get install python3-pip
   sudo apt-get install python3-venv
   ```
	
   Сервер запускали и тестировали на python3.6, именно эту версию лучше и использовать

2. Создать venv для запуска сервера

   ```
   python3.6 -m venv venv
   ```

   (второй аргумент - путь до venv, в случае команды выше venv создастся в папке venv текущей директории)

3. В новосозданный venv установить все необходимые для работы пакеты:

   ```
   ./venv/bin/python -m pip install -r requirements.txt
   ```
   Дождаться окончания установки.

4. Запустить сервер:

   ```
   ./venv/bin/python main.py
   ```

   Если всё в порядке, никаких сообщений не появится, main.py просто запустится.

   По умолчанию сервер запустится на `127.0.0.1:8888`.

   Префикс и номер порта можно изменить. Для этого рядом с файлом `main.py` создать файл `settings.py` и в него написать:

   ```
   url_prefix = "<ПРЕФИКС>"
   port = <НОМЕР_ПОРТА>
   ```

   Если во время запуска возникают ошибки, убедитесь, что:
   
      1. Вы используете именно `python3` и `pip3`.
      2. На локальной машине не запущен другой сервер.
      3. Вы указали адекватные значения `url_prefix` и `port` (или не  меняли их)
      4. Вы скачали рабочую версию с репозитория.

   4. Всё готово. В любом браузере зайдите на `127.0.0.1:8888` (по умолчанию), увидите страницу uRPC.

Заметьте, нельзя запустить два сервера на одной машине, возникнет ошибка `Address already in use`, перед новым запуском нужно остановить рабочий сервер. Для этого нажать `Ctrl+C` в окне терминала, где он запущен.  

## Запуск сервера на Windows

Общий смысл тот же, что и на linux: скачать python, cклонировать репозиторий uRPC, обновить подмодули, установить зависимости и запустить

	1. Скачать python https://www.python.org/downloads/, желательно версии 3.6.
	2. Установить в любую папку.
	3. Открыть командную строку и установить все зависимости:
		`<путь до python.exe> -m pip install -r <путь до requirements.txt из этого проекта>`
        Для установки пакетов понадобятся права администратора, если вы установили python в один из системных путей
	4. Склонировать или скачать репозиторий средствами git
	5. Обновиться на нужную ветку или коммит
	4. Запустить сервер: `<путь до python.exe> <пусть до main.py>`
