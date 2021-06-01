#ifndef BASE_IO_WIDGET_H
#define BASE_IO_WIDGET_H

#include <QString>
#include <QWidget>
#include <QLabel>
#include <QLineEdit>

class base_io_widget : public QWidget
{
    Q_OBJECT

private:
    QString Name;
    QString Type;

    QLabel *Label;
    QLineEdit *Editor;

protected:
    void SetLabel(QLabel* ArgLabel);
    void SetEditor(QLineEdit *Editor);

    QLineEdit* GetEditor(void);
    QLabel*    GetLabel(void);

public:
    explicit base_io_widget(QString ArgName, QString ArgType, QWidget *parent = 0);

    virtual QString GetText(void);
    virtual QString GetType(void);
    virtual QString GetName(void);

    virtual void SetText(QString);

signals:

public slots:
};

#endif // BASE_IO_WIDGET_H
