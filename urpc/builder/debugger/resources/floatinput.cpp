#include "floatinput.h"
#include "ui_floatinput.h"

#define DECIMALS 10

FloatInput::FloatInput(QWidget *parent, QString ArgName, QString ArgType, float minvalue, float maxvalue) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::FloatInput)
{
    ui->setupUi(this);
    ui->FloatEdit1->setValidator(new QDoubleValidator(minvalue, maxvalue, DECIMALS));

    this->SetLabel(ui->Label);
    this->SetEditor(ui->FloatEdit1);

}
//---------------------------------------------------
FloatInput::~FloatInput()
{
    delete ui;
}
//------------------------------------------------------
float FloatInput::getValue()
{
    return this->GetText().toFloat();
}
