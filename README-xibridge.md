# Инструкция по использованию xibridge в проекте uRPC

клонировать и собрать проект xibridge, см. readme проекта xibridge (допустим, в папку c:/projects)

затем в папке проекта uRPC:

git switch t-64722
git sumbodule init
git submodule update --recursive

как обычно запустить uRPC-сервер;
как обычно сгенерировать проект библиотеки c помощью web-интерфейса;

## Cборка библиотеки под Windows

запустить cmake-gui;
нажать Configure (разрядность собираемой библиотеки должна совпадать с разрядностью, выбранной при сборке  xibridge);
добавить запись (Add entry): имя - XIBRIDGE_PATH, тип - string, значение - <путь к xibridge, допустим c:/projects/xibridge);  
поставить галочку ENABLE_XIBRIDGE;
нажать Generate;

## Cборка библиотеки под Linux

mkdir buid
cmake CMakeLists.txt -B build -DXIBRIDGE_PATH=<путь до xibridge> -DXIBRIDGE_ENABLE=On
cd build
make -j2

## Замечания по сборке и работе отладчика

Отладчик собирается как обычно, но ему для работы также требуется и библиотека xibridge (как и, например, urmc.dll или т.п.), т.е. из проекта 
xibridge нужно взять собранную библиотеку и скопировать (или установить) в тоже место, что и uRPC-библиотеку.

Чтобы простым образом проверить, как xibridge работает в составе urmc-отладчика под windows, можно сделать так:
заменить в папке собранного отладчика urmc.dll на новую собранную по данной инструкции urmc.dll и xibridge.dll.


 