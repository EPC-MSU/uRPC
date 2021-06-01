#ifndef FLOATINPUT_H
#define FLOATINPUT_H

#include "base_io_widget.h"

#include <limits>
#include <stdint.h>

#include "validlineedit.h"

namespace Ui {
class FloatInput;
}

class FloatInput : public base_io_widget
{
    Q_OBJECT

public:
    explicit FloatInput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "float", float minvalue = std::numeric_limits<float>::min(), float maxvalue = std::numeric_limits<float>::max());
    ~FloatInput();

    float getValue();

private:
    Ui::FloatInput *ui;
};

#endif // FLOATINPUT_H
