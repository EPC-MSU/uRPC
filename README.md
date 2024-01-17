# uRPC

[![Static Analysis Status](https://github.com/epc-msu/urpc/workflows/Linter/badge.svg)](https://github.com/epc-msu/urpc/actions?workflow=Linter)

https://v10.urpc.ximc.ru/help

uRPC - это RPC для работы с микроконтроллерами. Имея описание протокола (имя отправляемой команды, тип передаваемых данных и проч.), с помощью этого инструмента можно быстро сгенерировать: прошивку для микроконтроллера, C библиотеку для работы с микроконтроллером по описанному протоколу, Qt отладчик, документацию и проч.

Склонировать репозиторий uRPC, выбрать нужную ветку  и обновить подмодули:

~~~bash
```
git clone https://github.com/EPC-MSU/uRPC/
cd uRPC
git switch <ветка>
git submodule update --init --recursive
```
~~~

## Запуск c помощью Docker

Запустить веб-интерфейс для генерации прошивок, библиотеки и проч. можно с помощью docker:

```bash
sudo docker build . -t urpc
sudo docker run --name urpc --publish 8888:8888 urpc
```

Сервер появится на http://localhost:8888

Для остановки сервера наберите в консоли Ctrl+C.
Далее чтобы контейнер не конфликтовал со следующими своими перезапусками, его стоит убрать командой:

```bash
sudo docker container rm urpc
```

## Запуск без Docker

Для отладки может быть удобно запустить сервер без Docker.

#### Запуск сервера на Linux

1. Для начала нужно установить python3 и сопутствующие:

   ```bash
   sudo apt-get install python3
   sudo apt-get install python3-pip
   sudo apt-get install python3-venv
   ```

   Сервер запускали и тестировали на python3.6, именно эту версию лучше и использовать.

2. Создать окружение venv для запуска сервера:

   ```bash
   python3 -m venv venv
   ```

3. Установить все необходимые для работы пакеты:

   ```bash
   ./venv/bin/python -m pip install --upgrade pip
   ./venv/bin/python -m pip install -r requirements.txt
   ```

4. Запустить сервер:

   ```bash
   ./venv/bin/python main.py
   ```

   Если всё в порядке, никаких сообщений не появится, main.py просто запустится.


#### Запуск сервера на Windows

Общий смысл тот же, что и на Linux: скачать python, установить все пакеты, запустить.

1. Скачать python https://www.python.org/downloads/, желательно версии 3.6.

2. Установить в любую папку.

3. Открыть командную строку в папке, где лежит requirements.txt и создать окружение venv для запуска сервера:

   ```batch
   python -m venv venv
   ```

4. Установить все зависимости:

   ```batch
   venv\Scripts\python -m pip install --upgrade pip
   venv\Scripts\python -m pip install -r requirements.txt
   ```

   Для установки пакетов понадобятся права администратора, если вы установили python в один из системных путей.

5. Запустить сервер:

   ```batch
   venv\Scripts\python main.py
   ```

Обратите внимание, что если вы используете python более новой версии, то может понадобится локальное обновление библиотек (mako, tornado и т.д.).

#### Запуск сервера на macOS

Общий смысл тот же, что при запуске сервера на Linux: скачать python3, установить все пакеты, запустить.

1. Скачать python3 https://www.python.org/downloads/macos/, желательно версии 3.6.

2. Установить python3.

3. Открыть терминал в папке, где лежит **requirements.txt**, и создать окружение venv для запуска сервера:

   ```bash
   python3 -m venv venv
   ```

4. Установить необходимые зависимости в окружение:

   ```bash
   ./venv/bin/python -m pip install --upgrade pip
   ./venv/bin/python -m pip install -r requirements.txt
   ```

5. Запустить сервер:

   ```bash
   ./venv/bin/python main.py
   ```

6. Если при работе сервера возникнет ошибка "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verifiry failed", нужно завершить работу сервера и в терминале выполнить команды:

   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install certifi
   /Applications/Python\ 3.6/Install\ Certificates.command
   ```

#### Общая информация о запуске сервера

По умолчанию сервер запустится на 127.0.0.1:8888. В любом браузере зайдите на 127.0.0.1:8888, увидите страницу uRPC.

Префикс и номер порта можно изменить. Для этого рядом с файлом **main.py** нужно создать файл **settings.py** и в него написать:

```
url_prefix = "<ПРЕФИКС>"
port = <НОМЕР_ПОРТА>
```

Если во время запуска возникают ошибки, убедитесь, что:

- Вы используете именно python3 и pip3.
- На локальной машине не запущен другой сервер.
- Вы указали адекватные значения *url_prefix* и *port* (или не меняли их).
- Вы скачали рабочую версию с репозитория xigen2.

