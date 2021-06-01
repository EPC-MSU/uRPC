#ifndef FLOATOUTPUT_H
#define FLOATOUTPUT_H

#include "base_io_widget.h"

namespace Ui {
class FloatOutput;
}

class FloatOutput : public base_io_widget
{
    Q_OBJECT

public:
    explicit FloatOutput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "float");
    ~FloatOutput();

    void setValue(float v);

private:
    Ui::FloatOutput *ui;
};

#endif // FLOATOUTPUT_H
