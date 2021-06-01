#ifndef FLOATARROUTPUT_H
#define FLOATARROUTPUT_H

#include "base_io_widget.h"

namespace Ui {
class FloatArrOutput;
}

class FloatArrOutput : public base_io_widget
{
    Q_OBJECT

public:
    explicit FloatArrOutput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "");
    ~FloatArrOutput();

    void setValue(float* f, int size);

private:
    Ui::FloatArrOutput *ui;
};

#endif // FLOATARROUTPUT_H
