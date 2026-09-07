#include "floatinput.h"
#include "ui_floatinput.h"

#include <QDoubleValidator>

#define DECIMALS 10

FloatInput::FloatInput(QWidget *parent, QString ArgName, QString ArgType, float minvalue, float maxvalue) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::FloatInput)
{
    ui->setupUi(this);
    QDoubleValidator *validator = new QDoubleValidator(minvalue, maxvalue, DECIMALS, this);
    validator->setLocale(QLocale::c());
    ui->FloatEdit1->setValidator(validator);

    this->SetLabel(ui->Label);
    this->SetEditor(ui->FloatEdit1);
    this->SetText(QString::number(QLocale::c().toFloat(this->GetText())));
}
//---------------------------------------------------
FloatInput::~FloatInput()
{
    delete ui;
}
//------------------------------------------------------
float FloatInput::getValue()
{
    bool ok;
    float val = QLocale::c().toFloat(this->GetText(), &ok);
    if (!ok) {
        return 0.0f; 
    }
    return val;
}
