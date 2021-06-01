#include "floatoutput.h"
#include "ui_floatoutput.h"

FloatOutput::FloatOutput(QWidget *parent, QString ArgName, QString ArgType) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::FloatOutput)
{
    ui->setupUi(this);
    ui->FloatEdit->sizePolicy().setVerticalPolicy(QSizePolicy::Minimum);

    this->SetLabel(ui->Label);
    this->SetEditor(ui->FloatEdit);
}
//---------------------------------------------------------------
FloatOutput::~FloatOutput()
{
    delete ui;
}
//--------------------------------------------------------------

void FloatOutput::setValue(float v)
{
    this->GetEditor()->setText(QString::number(v));
}
