#ifndef intinput_H
#define intinput_H

#include <QLineEdit>
#include <QComboBox>
#include <QBoxLayout>

#include "multilist.h"
#include "validlineedit.h"

#include "ui_intinput.h"

#include <limits>
#include <stdint.h>

#include "base_io_widget.h"

namespace Ui {
class intinput;
}

class IntInput : public base_io_widget
{
    Q_OBJECT

private:
    Ui::intinput *ui;

    MultiListWidget* cbox;

    QMap<QString, int64_t> *cboxconsts;

    QList<QPair<int64_t, QString> > * sorted_consts;

public:
    template <typename T> explicit IntInput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "",
                                            T minvalue = std::numeric_limits<T>::min(),
                                            T maxvalue = std::numeric_limits<T>::max()):
        base_io_widget(ArgName, ArgType, parent),
        ui(new Ui::intinput)
    {

        ui->setupUi(this);

        this->SetLabel(ui->Label);

        QBoxLayout* bl = new QBoxLayout(QBoxLayout::TopToBottom);
        this->setLayout(bl);

        bl->addWidget(this->GetLabel(),1);

        this->SetEditor(new ValidIntLineEdit(this,minvalue,maxvalue));
        this->GetEditor()->sizePolicy().setVerticalPolicy(QSizePolicy::Minimum);

        this->cbox = 0;
        this->cboxconsts = 0;

        bl->addWidget(this->GetEditor(),5);
    }

    ~IntInput();

    template <typename T> T getValue();

    void AddConst(QString ConstName, int ConstValue);

private slots:
    void cBoxChanged();
    void EditChanged();


};

template <> inline int64_t IntInput::getValue<int64_t>()      { return this->GetEditor()->text().toLongLong(); }
template <> inline uint64_t IntInput::getValue<uint64_t>()    { return this->GetEditor()->text().toULongLong(); }
template <> inline int32_t IntInput::getValue<int32_t>()      { return this->GetEditor()->text().toLong(); }
template <> inline uint32_t IntInput::getValue<uint32_t>()    { return this->GetEditor()->text().toULong(); }
template <> inline int16_t IntInput::getValue<int16_t>()      { return this->GetEditor()->text().toInt(); }
template <> inline uint16_t IntInput::getValue<uint16_t>()    { return this->GetEditor()->text().toInt(); }
template <> inline int8_t IntInput::getValue<int8_t>()        { return this->GetEditor()->text().toInt(); }
template <> inline uint8_t IntInput::getValue<uint8_t>()      { return this->GetEditor()->text().toInt(); }

#endif // intinput_H
