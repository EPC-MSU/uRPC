#include "floatarrinput.h"
#include "ui_floatarrinput.h"

FloatArrInput::FloatArrInput(QWidget *parent, QString ArgName, QString ArgType, float minvalue, float maxvalue, int size) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::FloatArrInput)
{
    ui->setupUi(this);

    this->SetLabel(ui->Label);
    this->SetEditor(new ValidFloatLineEdit(this, minvalue, maxvalue, size));

    layout()->addWidget(this->GetEditor());
    setLayout(layout());

}
//-------------------------------------------------------------
FloatArrInput::~FloatArrInput()
{
    delete ui;
}
//-------------------------------------------------------
void FloatArrInput::getValue(float* res)
{
    QString str = this->GetEditor()->text();

    QStringList Floats = str.split(" ");

    for(int i = 0; i < Floats.size(); i++)
    {
        res[i] = Floats[i].toFloat();
    }
}
