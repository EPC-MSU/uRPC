#ifndef CONTAINER_H
#define CONTAINER_H

#include <QWidget>
#include <QListWidgetItem>
#include <QMap>

namespace Ui {
class Container;
}

class Container : public QWidget
{
    Q_OBJECT

public:
    explicit Container(QWidget *parent = 0);
    ~Container();

    void addTab(QWidget* Tab, QString Name);
    int Count();

    void Search(QString Name);

private:
    Ui::Container *ui;
    QMap <QString, QWidget*> Widgets;


private slots:
    void ItemChanged(QListWidgetItem* Current, QListWidgetItem* Prev);
};

#endif // CONTAINER_H
