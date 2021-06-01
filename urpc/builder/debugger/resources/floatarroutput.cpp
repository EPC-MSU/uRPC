#include "floatarroutput.h"
#include "ui_floatarroutput.h"

FloatArrOutput::FloatArrOutput(QWidget *parent, QString ArgName, QString ArgType) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::FloatArrOutput)
{
    ui->setupUi(this);

    this->SetLabel(ui->Label);

    ui->FloatEdit->sizePolicy().setVerticalPolicy(QSizePolicy::Minimum);

    this->SetEditor(ui->FloatEdit);
}

FloatArrOutput::~FloatArrOutput()
{
    delete ui;
}

//---------------------------------
void FloatArrOutput::setValue(float* f, int size)
{
    QString str = "";
    for(int i = 0; i < size - 1; i++)
        str += QString::number(f[i]) + " ";

    str+=QString::number(f[size-1]);

    this->GetEditor()->setText(str);
}
