#ifndef IOPANEL_H
#define IOPANEL_H

#include <QWidget>
#include <QGroupBox>
#include <QPushButton>
#include <QVector>
#include <QTimer>

#include <QFile>

#include "base_io_widget.h"

namespace Ui {
class iopanel;
}

class iopanel : public QWidget
{
    Q_OBJECT

public:
    explicit iopanel(QWidget *parent = 0, QString ArgName = "");
    ~iopanel();

    QString GetName(void);

    // TODO: no public variables!

    QPushButton *PB;
    QPushButton *CallGetterBtn;

    void AddRequest(base_io_widget*);
    void AddResponse(base_io_widget*);

    void SetTypeSetter();

    base_io_widget* GetRequest(int Index);
    base_io_widget* GetResponse(int Index);

    int RequestsCount();
    int ResponsesLen();

   public slots:
    void PeriodicButtonClicked();
    void PeriodicUpdate();

private:
    QString Name;

    Ui::iopanel *ui;

    QTimer PeriodicSendTimer;

    QVector<base_io_widget*> Requests;
    QVector<base_io_widget*> Responses;

    QFile *PeriodicDataFile;
};

#endif // IOPANEL_H
