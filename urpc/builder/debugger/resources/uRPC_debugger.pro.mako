#-------------------------------------------------
#
# Project created by QtCreator 2016-07-01T13:49:01
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = uRPC_debugger
TEMPLATE = app


SOURCES += main.cpp\
    floatinput.cpp \
    mainwindow.cpp \
    intinput.cpp \
    iopanel.cpp \
    floatarrinput.cpp \
    intarrinput.cpp \
    floatoutput.cpp \
    intoutput.cpp \
    floatarroutput.cpp \
    intarroutput.cpp \
    multilist.cpp \
    validlineedit.cpp \
    base_io_widget.cpp \
    container.cpp

HEADERS  += \
    floatinput.h \
    mainwindow.h \
    intinput.h \
    iopanel.h \
    floatarrinput.h \
    intarrinput.h \
    floatoutput.h \
    intoutput.h \
    floatarroutput.h \
    intarroutput.h \
    multilist.h \
    validlineedit.h \
    base_io_widget.h \
    container.h

FORMS    += \
    floatinput.ui \
    mainwindow.ui \
    intinput.ui \
    iopanel.ui \
    floatarrinput.ui \
    intarrinput.ui \
    floatoutput.ui \
    intoutput.ui \
    floatarroutput.ui \
    intarroutput.ui \
    container.ui

unix|win32: LIBS += -L$$PWD/./ -l${library_shared_file(protocol)}