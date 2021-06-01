#ifndef INTARROUTPUT_H
#define INTARROUTPUT_H

#include <QLineEdit>

#include "base_io_widget.h"

namespace Ui {
class IntArrOutput;
}

class IntArrOutput : public base_io_widget
{
    Q_OBJECT

public:
    explicit IntArrOutput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "");
    ~IntArrOutput();

    template<typename Tn> void setValue(Tn* t, int size)
    {
        QString str = "";

        str += QString::number(t[0]);

        for(int i = 1; i < size; i++)
        {
            str += " ";
            str += QString::number(t[i]);
        }

        this->GetEditor()->setText(str);
    }

private:
    Ui::IntArrOutput *ui;
};

#endif // INTARROUTPUT_H
