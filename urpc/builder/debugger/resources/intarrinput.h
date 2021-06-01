#ifndef INTARRINPUT_H
#define INTARRINPUT_H

#include <QWidget>
#include <QDebug>
#include <QSpacerItem>

#include <validlineedit.h>

#include <limits>
#include <stdint.h>

#include <QVBoxLayout>
#include <QBoxLayout>

#include "ui_intarrinput.h"
#include "base_io_widget.h"

namespace Ui {
class IntArrInput;
}

class IntArrInput : public base_io_widget
{
    Q_OBJECT

public:
    template <typename Tc> explicit IntArrInput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "", Tc minvalue = std::numeric_limits<Tc>::min(), Tc maxvalue = std::numeric_limits<Tc>::min(), int size = 0) :
        base_io_widget(ArgName, ArgType, parent),
        ui(new Ui::IntArrInput)
    {
        ui->setupUi(this);

        this->SetLabel(ui->Label);

        QBoxLayout* bl = new QBoxLayout(QBoxLayout::TopToBottom);
        this->setLayout(bl);

        this->SetEditor(new ValidIntLineEdit(this, minvalue, maxvalue, size));

        this->GetEditor()->sizePolicy().setVerticalPolicy(QSizePolicy::Minimum);

        bl->addWidget(this->GetLabel(), 1);
        bl->addWidget(this->GetEditor(), 5);

        this->sizePolicy().setVerticalStretch(1);
        this->sizePolicy().setVerticalPolicy(QSizePolicy::Maximum);

    }

    ~IntArrInput();

    template <typename T> T extract(QString &str);



    template<typename Tn> void getValue(Tn* t)
    {
        QStringList slist = this->GetText().split(" ");
        for(int i=0;i<slist.size();i++)
            t[i] = extract<Tn>(slist[i]);
    }

private:
    Ui::IntArrInput *ui;
};

template <> inline int64_t IntArrInput::extract<int64_t>(QString &str)      { return str.toLongLong(); }
template <> inline uint64_t IntArrInput::extract<uint64_t>(QString &str)    { return str.toULongLong(); }
template <> inline int32_t IntArrInput::extract<int32_t>(QString &str)      { return str.toLong(); }
template <> inline uint32_t IntArrInput::extract<uint32_t>(QString &str)    { return str.toULong(); }
template <> inline int16_t IntArrInput::extract<int16_t>(QString &str)      { return str.toInt(); }
template <> inline uint16_t IntArrInput::extract<uint16_t>(QString &str)    { return str.toInt(); }
template <> inline int8_t IntArrInput::extract<int8_t>(QString &str)        { return str.toInt(); }
template <> inline uint8_t IntArrInput::extract<uint8_t>(QString &str)      { return str.toInt(); }

#endif // INTARRINPUT_H
