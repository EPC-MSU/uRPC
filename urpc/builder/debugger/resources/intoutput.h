#ifndef INTOUTPUT_H
#define INTOUTPUT_H

#include <QLineEdit>
#include <QList>

#include "base_io_widget.h"
#include "multilist.h"
#include "stdint.h"

namespace Ui {
class IntOutput;
}

class IntOutput : public base_io_widget
{
    Q_OBJECT

public:
    explicit IntOutput(QWidget *parent = 0, QString ArgName = "", QString ArgType = "");
    ~IntOutput();


    template <typename T> void setValue(T i)
    {
        this->GetEditor()->setText(QString::number(i));
    }
    void AddConst(QString ConstName, int ConstValue);

private:
    Ui::IntOutput *ui;

    MultiListWidget* cbox;

    QMap<QString, int64_t> *cboxconsts;

    QList<QPair<int64_t, QString> > * sorted_consts;

private slots:
    void EditChanged();

};

#endif // INTOUTPUT_H
