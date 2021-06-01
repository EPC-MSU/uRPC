#include "base_io_widget.h"


base_io_widget::base_io_widget(QString ArgName, QString ArgType, QWidget *parent) : QWidget(parent)
{
    this->Name = ArgName;
    this->Type = ArgType;
}

void base_io_widget::SetLabel(QLabel *ArgLabel)
{
    this->Label = ArgLabel;
    this->Label->setText(this->Name + " " + "type: " + this->Type);
}

void base_io_widget::SetEditor(QLineEdit *ArgEditor)
{
    this->Editor = ArgEditor;
}

QString base_io_widget::GetText(void)
{
    return this->Editor->text();
}

QString base_io_widget::GetName(void)
{
    return this->Name;
}

QString base_io_widget::GetType(void)
{
    return this->Type;
}

QLineEdit* base_io_widget::GetEditor(void)
{
    return this->Editor;
}

QLabel* base_io_widget::GetLabel(void)
{
    return this->Label;
}

void base_io_widget::SetText(QString Str)
{
    this->Editor->setText(Str);
}
