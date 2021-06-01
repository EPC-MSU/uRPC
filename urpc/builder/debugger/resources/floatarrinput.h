#ifndef FLOATARRINPUT_H
#define FLOATARRINPUT_H

#include <limits>
#include <stdint.h>

#include "validlineedit.h"
#include "base_io_widget.h"

namespace Ui {
class FloatArrInput;
}

class FloatArrInput : public base_io_widget
{
    Q_OBJECT

public:
    explicit FloatArrInput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "",
                           float minvalue = std::numeric_limits<int>::min(), float maxvalue = std::numeric_limits<int>::min(), int size = 0);
    ~FloatArrInput();

    ValidFloatLineEdit* ledit;

    void getValue(float*);

private:
    Ui::FloatArrInput *ui;
};

#endif // FLOATARRINPUT_H
