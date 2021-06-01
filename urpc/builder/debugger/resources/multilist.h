#ifndef MULTILIST_H
#define MULTILIST_H

#include <QtGui>

#include <QListWidget>

class MultiListWidget
    : public QListWidget
{
    Q_OBJECT


public:
    MultiListWidget();
    virtual ~MultiListWidget();

    QStringList checkedItems() const;
    void addItem(QString &label);


signals:
    void Changed();


private slots:
    void ChangedSlot();

};

#endif // MULTILIST_H
