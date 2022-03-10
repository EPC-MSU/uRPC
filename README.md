# uRPC

[![Static Analysis Status](https://github.com/epc-msu/urpc/workflows/Linter/badge.svg)](https://github.com/epc-msu/urpc/actions?workflow=Linter)

https://v10.urpc.ximc.ru/help

uRPC - это RPC для работы с микроконтроллерами. Имея описание протокола (имя отправляемой команды, тип 
передаваемых данных и проч.) с помощью этого инструмента можно быстро сгенерировать: прошивку для микроконтроллера, 
C библиотеку для работы с микроконтроллером по описанному протоколу, Qt отладчик, документацию и проч.

## Запуск c помощью Docker

Запустить веб-интерфейс для генерации прошивок, библиотеки и проч. можно с помощью docker:

```bash
sudo docker build . -t urpc
sudo docker run --name urpc --publish 8888:8888 urpc
```

Сервер появится на http://localhost:8888

Для остановки сервера наберите в консоли Ctrl^C.
Далее чтобы контейнер не конфликтовал со следующими своими перезапусками его стоит убрать командой:

```bash
sudo docker container rm urpc
```

## Запуск без Docker

Для отладки может быть удобно запустить сервер без Docker

1. Для начала нужно установить python3 и сопутствующие:

```bash
sudo apt-get install python3
sudo apt-get install python3-pip
sudo apt-get install python3-venv
```

Сервер запускали и тестировали на python3.6, именно эту версию лучше и использовать

2. Создать venv для запуска сервера

```bash
python3.6 -m venv venv
```

(второй аргумент - путь до venv, в случае команды выше venv создастся в папке venv текущей директории)

3. В новосозданный venv установить все необходимые для работы пакеты:

```bash
./venv/bin/python -m pip install -r requirements.txt
```

Дождаться окончания установки.

3. Запустить сервер:

```bash
./venv/bin/python main.py
```

Если всё в порядке, никаких сообщений не появится, main.py просто запустится

По умолчанию сервер запустится на 127.0.0.1:8888.
Префикс и номер порта можно изменить. Для этого рядом с файлом main.py создать файл
settings.py и в него написать:
url_prefix = "<ПРЕФИКС>"
port = <НОМЕР_ПОРТА>

Если во время запуска возникают ошибки, убедитесь, что:
1. Вы используете именно python3 и pip3
2. На локальной машине не запущен другой сервер
3. Вы указали адекватные значения url_prefix и port (или не меняли их)
4. Вы скачали рабочую версию с репозитория xigen2

4. Всё готово. В любом браузере зайдите на 127.0.0.1:8888 (по умолчанию), увидите страницу uRPC.

Заметьте, нельзя запустить два сервера на одной машине, возникнет ошибка Address already in use, перед новым запуском 
нужно остановить рабочий сервер. Для этого нажать Ctrl+C в окне терминала, где он запущен.  

Запуск сервера на Windows
Общий смысл тот же, что и на linux: скачать python, установить все пакеты, запустить

1. Скачать python https://www.python.org/downloads/, желательно версии 3.6
2. Установить в любую папку
3. Открыть командную строку в папке, где лежит requirements.txt и создать окружение venv для запуска сервера:

```
python -m venv venv
```

4. Установить все зависимости:

```
venv\Scripts\python -m pip install -r requirements.txt
```
Для установки пакетов понадобятся права администратора, если вы установили python в один из системных путей.

4. Запустить сервер:

```
venv\Scripts\python main.py
```
Обратите внимание, что если вы используете python более новой версии, то может понадобится локальное обновление библиотек (mako, tornado и т.д.).