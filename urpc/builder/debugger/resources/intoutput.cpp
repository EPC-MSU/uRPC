#include "intoutput.h"
#include "ui_intoutput.h"

#include "validlineedit.h"

IntOutput::IntOutput(QWidget *parent, QString ArgName, QString ArgType) :
    base_io_widget(ArgName, ArgType, parent),
    ui(new Ui::IntOutput)
{
    ui->setupUi(this);

    this->SetLabel(ui->Label);

    this->SetEditor(ui->IntEdit);
    this->GetEditor()->sizePolicy().setVerticalPolicy(QSizePolicy::Minimum);

    this->cbox = 0;
    this->cboxconsts = 0;
}

IntOutput::~IntOutput()
{
    delete ui;
}
//-----------------------------------------

void IntOutput::AddConst(QString ConstName, int ConstValue)
{
    if (this->cboxconsts == 0)
    {
        // first append

        cbox = new MultiListWidget();
        cbox->setEditTriggers(QAbstractItemView::NoEditTriggers);

        QObject::connect(ui->IntEdit,SIGNAL(textChanged(QString)),this,SLOT(EditChanged()));

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
    this->cbox->addItem(ConstName);

    sorted_consts->append(QPair<int64_t, QString>(ConstValue, ConstName));

    qSort(*sorted_consts);
	std::reverse(sorted_consts->begin(), sorted_consts->end());

    this->EditChanged();

    // disable checking
    Qt::ItemFlags flags;
    flags = this->cbox->item(this->cbox->count() - 1)->flags();
    flags &= ~ Qt::ItemIsUserCheckable;
    this->cbox->item(this->cbox->count() - 1)->setFlags(flags);
}

void IntOutput::EditChanged(void)
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
