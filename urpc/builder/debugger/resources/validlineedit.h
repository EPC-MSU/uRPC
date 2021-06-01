#ifndef VALIDLINEEDIT_H
#define VALIDLINEEDIT_H

#include <QWidget>
#include <QLineEdit>

const int DEFAULT_MAX_MIN = 1000000;

#include <limits>
#include <stdint.h>

//------------------------classes


////------------------int class
class ValidIntLineEdit : public QLineEdit
{
    Q_OBJECT
public:
    template <typename T> explicit ValidIntLineEdit(QWidget *parent = 0, T minvalue = std::numeric_limits<T>::min(), T maxvalue= std::numeric_limits<T>::max(), int sizevalue = 0)
            : QLineEdit(parent)
    {
        min = minvalue;
        max= maxvalue;
        size = sizevalue;


        QObject::connect(this,SIGNAL(textChanged(QString)),this,SLOT(Edited(QString)));


    }

private:
    QPalette plt;

    long long int min;
    unsigned long long int max;
    int size;

    bool Valid(QString str);

signals:

public slots:
    void Edited(QString str);
};


//--------------------------------

////-----------------------float class
class ValidFloatLineEdit : public QLineEdit
{
    Q_OBJECT
public:
    explicit ValidFloatLineEdit(QWidget *parent = 0,float minvalue= -DEFAULT_MAX_MIN, float maxvalue= DEFAULT_MAX_MIN, int sizevalue= 0);

private:
    QPalette plt;

    float min;
    float max;
    int size;

    bool Valid(QString str);

signals:

public slots:
    void Edited(QString str);
};


#endif // VALIDLINEEDIT_H
