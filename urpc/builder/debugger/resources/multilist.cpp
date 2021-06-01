
#include "multilist.h"

MultiListWidget::MultiListWidget() : QListWidget()
{

    QObject::connect(this,SIGNAL(itemChanged(QListWidgetItem*)),this,SLOT(ChangedSlot()));

    this->Changed();

    this->setMinimumHeight(60);
    this->setSizePolicy(QSizePolicy::Preferred,QSizePolicy::Expanding);
}
//----------------------------
MultiListWidget::~MultiListWidget()
{
}

//-------------------------------

void MultiListWidget::addItem(QString &label)
{

    QListWidget::addItem(label);
    this->item(this->count()-1)->setCheckState(Qt::Checked);
}

//----------
void MultiListWidget::ChangedSlot()
{
    Changed();
}

//-------------------------
QStringList MultiListWidget::checkedItems() const
{
    QStringList mCheckedItems;

    for(int i=0;i < this->count();i++)
    {
        if(this->item(i)->checkState() == Qt::Checked)
            mCheckedItems.push_back(this->item(i)->text());
    }

    return mCheckedItems;
}
