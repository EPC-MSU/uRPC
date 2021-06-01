# Пример для микроконтроллера StellarisWare LM3S5R31

Этот сгенерированный пример кода демонстрирует работу системы uRPC.
Микропрограмма написана для чипа LM3S5R31. Предполагается, что
установлен внешний кварцевый резонатор на 16 МГц. Далее эта частота
преобразуется в частоту ядра 80 МГц.

Для коммуникации настраивается интерфейс USB0. Используется Специальные пины USB0DM(70), USB0DP(71), USB0RBIAS(73). Рекомендуемые параметры
открытия порта 115200/8-N-1.

## Сборка проекта

Сборка делается в среде IAR 7.30. Копию дистрибутива можно скачать тут: https://download.urpc.kea.su/firmware/common/EWARM-CD-7303-8062.exe 

Для работы с периферией используется стандартная библиотека производителя. 

Архив можно скачать по ссылке: https://download.urpc.kea.su/firmware/ti/lm3s5r31/SW-LM3S-10636.exe


-   Разместить пример так, чтобы данный файл имел следующую вложенность
    **C:\projects\example\README.md**
    
-   Библиотеки нужно установить в папку **C:\ti** (должно получиться что-то типа **C:\ti\StellarisWare**).
    
- Открыть в среде IAR рабочее окружение **C:\projects\example\workspace.eww**

- Используя пакетную сборку (клавиша <F8>) собрать библиотеку и микропрограмму

-   Прошить микропрограмму в чип <Ctrl + D>
