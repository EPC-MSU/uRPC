#include "container.h"
#include "ui_container.h"

#include "qdebug.h"

Container::Container(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Container)
{
    ui->setupUi(this);
    QObject::connect(ui->listWidget, SIGNAL(currentItemChanged(QListWidgetItem*,QListWidgetItem*)), this, SLOT(ItemChanged(QListWidgetItem*,QListWidgetItem*)));
}

Container::~Container()
{
    delete ui;
}

void Container::addTab(QWidget* Tab, QString Name)
{
    ui->listWidget->addItem(Name);
    ui->stackedWidget->addWidget(Tab);
    Widgets.insert(Name, Tab);

    ui->listWidget->setCurrentItem(ui->listWidget->item(0));
}

void Container::ItemChanged(QListWidgetItem *Current, QListWidgetItem *Prev)
{
    ui->stackedWidget->setCurrentWidget(Widgets[Current->text()]);
}

int Container::Count()
{
    return this->ui->listWidget->count();
}

void Container::Search(QString Name)
{
    int WidgetIndex = -1;

    for (int i=0; i < ui->listWidget->count(); i++)
    {
        if (ui->listWidget->item(i)->text().contains(Name))
        {
            ui->listWidget->item(i)->setHidden(false);
            WidgetIndex = i;
        }
        else
        {
            ui->listWidget->item(i)->setHidden(true);
        }
    }

    if (WidgetIndex >= 0)
    {
        ui->stackedWidget->setEnabled(true);
        ui->listWidget->setCurrentItem(ui->listWidget->item(WidgetIndex));

    }
    else
    {
        ui->stackedWidget->setEnabled(false);
    }
}
