#include "intinput.h"
#include "validlineedit.h"
#include "ui_intinput.h"



//-------------------------------------------------------
//-----------------------------------------------------------
IntInput::~IntInput()
{
    delete ui;
}

//---------------------------------------------
void IntInput::cBoxChanged()
{
    int res = 0;

    QObject::disconnect(this->GetEditor(), SIGNAL(textChanged(QString)), this, SLOT(EditChanged()));

    QStringList stlist = this->cbox->checkedItems();

    while(!stlist.isEmpty())
    {
        QString str = stlist.back();
        stlist.pop_back();

        res |= (*this->cboxconsts)[str];
    }

    this->GetEditor()->setText(QString::number(res));

    QObject::connect(this->GetEditor(), SIGNAL(textChanged(QString)), this, SLOT(EditChanged()));
}
//--------------------------------------------
void IntInput::AddConst(QString ConstName, int ConstValue)
{
    if (this->cboxconsts == 0)
    {
        // first append

        cbox = new MultiListWidget();

        QObject::connect(cbox,SIGNAL(itemClicked(QListWidgetItem*)),this,SLOT(cBoxChanged()));
        QObject::connect(this->GetEditor(), SIGNAL(textChanged(QString)), this, SLOT(EditChanged()));

        this->layout()->addWidget(this->cbox);

        // replace editor
        this->layout()->removeWidget(this->GetEditor());
        this->layout()->addWidget(this->GetEditor());

        cboxconsts = new QMap<QString, int64_t>;
        sorted_consts = new QList<QPair<int64_t, QString> >();

        this->sizePolicy().setVerticalPolicy(QSizePolicy::Expanding);
        this->setMaximumHeight(1000);
    }

    cboxconsts->insert(ConstName, ConstValue);
    sorted_consts->append(QPair<int64_t, QString>(ConstValue, ConstName));

    qSort(*sorted_consts);
    std::reverse(sorted_consts->begin(), sorted_consts->end());

    this->cbox->addItem(ConstName);
}

void IntInput::EditChanged(void)
{
    if (cbox != 0)
    {
        int64_t Value = this->GetEditor()->text().toLongLong();

        for(int i = 0; i < this->cbox->count(); i++)
        {
            int64_t const_value = this->sorted_consts->at(i).first;
            QString const_name = this->sorted_consts->at(i).second;

            if ((Value & const_value) == const_value)
            {
                this->cbox->findItems(const_name, Qt::MatchExactly)[0]->setCheckState(Qt::Checked);
                Value -= const_value;
            }
            else
            {
                this->cbox->findItems(const_name, Qt::MatchExactly)[0]->setCheckState(Qt::Unchecked);
            }
        }
    }
}
