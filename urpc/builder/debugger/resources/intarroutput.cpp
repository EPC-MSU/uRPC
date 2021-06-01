#include "intarroutput.h"
#include "ui_intarroutput.h"

#include <QBoxLayout>

IntArrOutput::IntArrOutput(QWidget *parent, QString ArgName, QString ArgType) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::IntArrOutput)
{
    ui->setupUi(this);

    this->SetLabel(ui->Label);
    this->SetEditor(ui->IntEdit);

    this->GetEditor()->sizePolicy().setVerticalPolicy(QSizePolicy::Minimum);
}


IntArrOutput::~IntArrOutput()
{
    delete ui;
}
