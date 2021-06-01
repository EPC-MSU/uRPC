#include "iopanel.h"
#include "ui_iopanel.h"
#include <QFile>

#define FILE_FORMAT ".log"
#define FILE_SPLIT  " "

iopanel::iopanel(QWidget *parent, QString ArgName) :
    QWidget(parent),
    ui(new Ui::iopanel)
{
    ui->setupUi(this);

    this->Name = ArgName;

    PB = ui->PushButton;
    CallGetterBtn = ui->GetterBtn;

    // unvisible if there no requests \ responses

    ui->scrollArea->setVisible(false);
    ui->scrollArea_2->setVisible(false);

    // not use getter button on default
    ui->GetterBtn->setVisible(false);

    QObject::connect(&(this->PeriodicSendTimer), SIGNAL(timeout()), this, SLOT(PeriodicUpdate()));
    QObject::connect(ui->PeriodicButton, SIGNAL(clicked(bool)), this, SLOT(PeriodicButtonClicked()));

    //file is not necessary while Periodic button not clicked
    PeriodicDataFile = NULL;
}

iopanel::~iopanel()
{
    this->PeriodicSendTimer.stop();

    if (this->PeriodicDataFile != NULL)
    {
        if (this->PeriodicDataFile->isOpen())
        {
            this->PeriodicDataFile->close();
        }

        delete PeriodicDataFile;
    }

    for (int i = 0; i < this->Requests.size(); i++)
    {
        delete this->Requests[i];
    }

    for (int i = 0; i < this->Responses.size(); i++)
    {
        delete this->Responses[i];
    }

    delete ui;
}

void iopanel::AddRequest(base_io_widget* Widget)
{
    this->ui->GBox1->layout()->addWidget(Widget);
    this->Requests.append(Widget);

    // visible if requests is not empty
    ui->scrollArea->setVisible(true);
}

void iopanel::AddResponse(base_io_widget* Widget)
{
    this->ui->GBox2->layout()->addWidget(Widget);
    this->Responses.append(Widget);

    // visible if responses is not empty
    ui->scrollArea_2->setVisible(true);
}

void iopanel::PeriodicButtonClicked(void)
{
    if (this->PeriodicDataFile == NULL)
    {
        this->PeriodicDataFile = new QFile(this->Name + ".log");
    }

    if (this->PeriodicSendTimer.isActive())
    {
        this->PeriodicSendTimer.stop();
        this->PeriodicDataFile->close();
        ui->PeriodicButton->setText("Periodic");
    }
    else
    {
        ui->PeriodicButton->setText("Stop");
        if (this->PeriodicDataFile->open(QIODevice::WriteOnly | QIODevice::Text | QIODevice::Truncate))
        {

            // write first line
            for (int i = 0; i < this->Responses.size(); i++)
            {
                QString str = (this->Responses[i]->GetName() + "(" + this->Responses[i]->GetType() + ")" + FILE_SPLIT);
                this->PeriodicDataFile->write(str.toLatin1(), str.size());
            }
            this->PeriodicDataFile->write("\n");
        }

        this->PeriodicSendTimer.start(this->ui->FreqBox->value());
    }


}

void iopanel::PeriodicUpdate(void)
{
    this->PB->click();

    if (this->PeriodicDataFile->isOpen())
    {
        for (int i = 0; i < this->Responses.count(); i++)
        {
            QString str = (this->Responses[i]->GetText() + FILE_SPLIT);
            this->PeriodicDataFile->write(str.toLatin1(), str.size());
        }
        this->PeriodicDataFile->write("\n");
    }
}

QString iopanel::GetName(void)
{
    return this->Name;
}

void iopanel::SetTypeSetter()
{
    ui->GetterBtn->setVisible(true);
}


base_io_widget* iopanel::GetRequest(int Index)
{
    return this->Requests[Index];
}

base_io_widget* iopanel::GetResponse(int Index)
{
    return this->Responses[Index];
}

int iopanel::RequestsCount()
{
    return this->Requests.size();
}

int iopanel::ResponsesLen()
{
    return this->Responses.size();
}
