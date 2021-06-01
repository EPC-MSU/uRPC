<%
    from urpc import ast
    from urpc.util.cconv import ascii_to_hex, get_msg_len, type_to_cstr
%>\

<%namespace import="namespaced" module = "urpc.builder.device.utils.namespaced" inheritable="True"/>

#include "mainwindow.h"
#include "ui_mainwindow.h"

#include "intarroutput.h"
#include "intarrinput.h"

#include "intinput.h"
#include "intoutput.h"

#include "floatinput.h"
#include "floatoutput.h"

#include "floatarrinput.h"
#include "floatarroutput.h"

#include <QTime>
#include <QFileDialog>

// libs for type identification
#include <limits>
#include <stdint.h>

void MainWindow::AddIOPanel(iopanel* Panel)
{
    MainContainer->addTab(Panel, Panel->GetName());
}

MainWindow::MainWindow (QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    log = ui->LogWidget;
    QObject::connect(ui->ClearBtn, SIGNAL(clicked(bool)),log,SLOT(clear()));

    comedit = ui->comEdit;
    QObject::connect(ui->cntButton, SIGNAL(clicked(bool)),this,SLOT(connectButton()));
    QObject::connect(ui->dcntButton,SIGNAL(clicked(bool)),this,SLOT(dconnectButton()));

    // ToolTip
    #ifdef Q_OS_WIN32
    this->comedit->setToolTip("Example:\ncom:\\\\.\\COM12\nxi-net://192.168.0.1/00001234");
    #else
        #ifdef Q_OS_LINUX
    this->comedit->setToolTip("Example:\ncom:///dev/tty/ttyACM34\nxi-net://192.168.0.1/00001234");
        #else
    this->comedit->setToolTip("Example:\ncom:\\\\.\\COM12\ncom:///dev/tty/ttyACM34\nemu:///var/lib/ximc/virtual56.dat\nxi-net://192.168.0.1/00001234");
        #endif
    #endif

    // Main tab widget
    MainContainer = new Container();

    this->ui->verticalLayout->addWidget(MainContainer);

    // search panel
    QObject::connect(ui->SearchEdit, SIGNAL(textChanged(QString)), this, SLOT(SearchSlot(QString)));

    // profile get/set slots
    QObject::connect(ui->GetProfileBtn, SIGNAL(clicked(bool)), this, SLOT(GetProfileSlot()));
    QObject::connect(ui->SetProfileBtn, SIGNAL(clicked(bool)), this, SLOT(SetProfileSlot()));

    /* commands
     * THIS CODE IS AUTOGENERATED
     */

    <%def name = "create_input_widget(cmd,arg)">\
        % if isinstance(arg.type_, ast.ArrayType):
            % if isinstance(arg.type_.type_, ast.FloatType):
    ${cmd.name}${arg.name}inputwidget = new FloatArrInput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}",-std::numeric_limits<float>::max(),std::numeric_limits<float>::max(),${len(arg.type_)});
            %else:
    ${cmd.name}${arg.name}inputwidget = new IntArrInput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}",std::numeric_limits<${type_to_cstr(arg.type_)[0]}>::min(),std::numeric_limits<${type_to_cstr(arg.type_)[0]}>::max(),${len(arg.type_)});
            %endif
        % else:  # (it is not array)
            % if isinstance(arg.type_, ast.FloatType):
    ${cmd.name}${arg.name}inputwidget = new FloatInput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}",-std::numeric_limits<float>::max(),std::numeric_limits<float>::max());
            % else:
    ${cmd.name}${arg.name}inputwidget = new IntInput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}",std::numeric_limits<${type_to_cstr(arg.type_)[0]}>::min(),std::numeric_limits<${type_to_cstr(arg.type_)[0]}>::max());
            % endif
        % endif
    ${cmd.name}iop->AddRequest(${cmd.name}${arg.name}inputwidget);
    </%def>

    <%def name = "create_output_widget(cmd,arg)">\
        %if isinstance(arg.type_, ast.ArrayType):
            %if isinstance(arg.type_.type_, ast.FloatType):
    ${cmd.name}${arg.name}outputwidget = new FloatArrOutput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}");
            %else:
    ${cmd.name}${arg.name}outputwidget = new IntArrOutput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}");
            %endif
        %else:
            %if isinstance(arg.type_,ast.FloatType):
    ${cmd.name}${arg.name}outputwidget = new FloatOutput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}");
            %else:
    ${cmd.name}${arg.name}outputwidget = new IntOutput(NULL,"${arg.name}", "${type_to_cstr(arg.type_)[0]}${type_to_cstr(arg.type_)[1]}");
            %endif
        %endif
    ${cmd.name}iop->AddResponse(${cmd.name}${arg.name}outputwidget);
    </%def>

    % for cmd in protocol.commands:
    // command ${cmd.name}
    ${cmd.name}iop = new iopanel(NULL, "${cmd.name}");
    this->AddIOPanel(${cmd.name}iop);
        % for arg in cmd.request.args:
    ${create_input_widget(cmd,arg)}
            % if len(arg.consts) > 0:
                % for c in arg.consts:
    ${cmd.name}${arg.name}inputwidget->AddConst("${c.name}", ${namespaced(c.name)});
                % endfor
            % endif

        % endfor
        % for arg in cmd.response.args:
    ${create_output_widget(cmd,arg)}
            % if len(arg.consts) > 0:
                % for c in arg.consts:
    ${cmd.name}${arg.name}outputwidget->AddConst("${c.name}", ${namespaced(c.name)});
                % endfor
            % endif
        % endfor

    QObject::connect(${cmd.name}iop->PB, SIGNAL(clicked(bool)), this, SLOT(${cmd.name}PressSlot(bool)));

    % if view.is_setter(cmd):
        ${cmd.name}iop->SetTypeSetter();
        QObject::connect(${cmd.name}iop->CallGetterBtn, SIGNAL(clicked(bool)), this, SLOT(${cmd.name}CallGetterPressSlot(bool)));
    % endif

    % endfor

    QObject::connect(ui->ClearBtn, SIGNAL(clicked(bool)),log,SLOT(clear()));

}

MainWindow::~MainWindow()
{
    ${namespaced("close_device")}(&device);
    delete ui;
}


//--------------------------------------
void MainWindow::logAdd(QString str)
{
    log->addItem(QTime::currentTime().toString() + ": " +str);
    log->scrollToBottom();
}

//---------------------------------------
void MainWindow::logClear()
{
    log->clear();
}

//--------------------------connect\disconnect slots
void MainWindow::connectButton()
{
    ${namespaced("close_device")}(&device);
    device = ${namespaced("open_device")}(comedit->text().toStdString().c_str());

    if(device == device_undefined)
    {
        ${namespaced("close_device")}(&device);
        logAdd(comedit->text()+ " device undefined");
    }
    else
    {
        logAdd(comedit->text()+ " connect");
    }

}

//------------------------------------------
void MainWindow::dconnectButton()
{
    ${namespaced("close_device")}(&device);
    logAdd("Disconnect "+comedit->text());
}

/* slots for SEND buttons
 * THIS CODE IS AUTOGENERATED
 */

<%
# this function take output and command structure and put data in output fields
%>
<%def name="set_output_fields(output,cmd)">
    % for arg in cmd.response.args:
        %if  isinstance(arg.type_, ast.ArrayType):
        ${cmd.name}${arg.name}outputwidget->setValue(output.${arg.name}, ${len(arg.type_)});
        %else:
        ${cmd.name}${arg.name}outputwidget->setValue(output.${arg.name});
        %endif
    %endfor
</%def>
% for cmd in protocol.commands:
void MainWindow::${cmd.name}PressSlot(bool)
{
    int result = 0;
    %if len(cmd.request.args) == 0:
        %if len(cmd.response.args) == 0:
    result = ${namespaced(cmd.name)}(device);
        %else:
    ${namespaced(argstructs[cmd.response].name)} output;
    result = ${namespaced(cmd.name)}(device,&output);
    if (result == result_ok || result == result_value_error)
    {
        ${set_output_fields(output,cmd)}
    }
        %endif
    %else:
    ${namespaced(argstructs[cmd.request].name)} input;

        % for arg in cmd.request.args:
            %if isinstance(arg.type_,ast.ArrayType):
                %if isinstance(arg.type_.type_, ast.FloatType):
    ${cmd.name}${arg.name}inputwidget->getValue(input.${arg.name});
                %else:
    ${cmd.name}${arg.name}inputwidget->getValue<${type_to_cstr(arg.type_)[0]}>(input.${arg.name});
                %endif
            %else:
                %if isinstance(arg.type_, ast.FloatType):
    input.${arg.name} = ${cmd.name}${arg.name}inputwidget->getValue();
                %else:
    input.${arg.name} = ${cmd.name}${arg.name}inputwidget->getValue<${type_to_cstr(arg.type_)[0]}>();
                %endif
            %endif
        % endfor

        %if len(cmd.response.args) == 0:
    result = ${namespaced(cmd.name)}(device,&input);
        %else:
    ${namespaced(argstructs[cmd.response].name)} output;
    result = ${namespaced(cmd.name)}(device,&input,&output);
    if (result == result_ok || result == result_value_error)
    {
        ${set_output_fields(output,cmd)}
    }
        %endif
    %endif

    if (result == device_undefined)
    {
        ${namespaced("close_device")}(&device);
    }

    logAdd("${namespaced(cmd.name)} returned "+QString::number(result));
}

    % if view.is_setter(cmd):
void MainWindow::${cmd.name}CallGetterPressSlot(bool)
{
    ${cmd.name.replace("set_", "get_")}PressSlot(true);

    for (int i = 0; i < ${cmd.name}iop->RequestsCount(); i++)
    {
        ${cmd.name}iop->GetRequest(i)->SetText(${cmd.name.replace("set_", "get_")}iop->GetResponse(i)->GetText());
    }
}
    % endif
% endfor

void MainWindow::SearchSlot(QString str)
{
    MainContainer->Search(str);
}

void MainWindow::GetProfileSlot()
{
    QString FileName = QFileDialog::getSaveFileName(0, "Save profile...", "${protocol.name}.json", "JSON files (*.json);; All files (*)");

    if (FileName.isEmpty())
        return;

    QFile Profile(FileName);

    if (!Profile.open(QIODevice::WriteOnly))
    {
        this->logAdd("Error opening file");
        this->logAdd("Abort");
        return;
    }

    char *Buf = 0;

    int Result = ${namespaced("get_profile")}(this->device, &Buf, malloc);

    if (Result == device_undefined)
    {
        ${namespaced("close_device")}(&device);
    }

    logAdd("get_profile returned " + QString::number(Result));

    if ((Result != result_ok) && (Result != result_value_error))
    {
        logAdd("Abort");
        Profile.close();
        free(Buf);
        return;
    }

    Profile.write(Buf);

    if (Profile.error())
    {
        logAdd("File error:");
        logAdd(Profile.errorString());
        logAdd("Abort");
        free(Buf);
        return;
    }

    logAdd("Done");
    Profile.close();
    free(Buf);
}

void MainWindow::SetProfileSlot()
{
    QString FileName = QFileDialog::getOpenFileName(0, "Open profile...", ".json", "JSON files (*.json);; All files (*)");

    if (FileName.isEmpty())
        return;

    QFile Profile(FileName);

    if (!Profile.open(QIODevice::ReadOnly))
    {
        this->logAdd("Error opening file");
        this->logAdd("Abort");
        return;
    }
    static char *Buf;
    static unsigned int Size;

    Size = Profile.size();
    Buf = new char[Size]; // TODO: safe pointer?

    Profile.read(Buf, Size);
    Profile.close();

    if (Profile.error())
    {
        logAdd("File error:");
        logAdd(Profile.errorString());
        logAdd("Abort");
        delete[] Buf;
        return;
    }

    int Result = 0;
    // TODO: more safe try-catch block
    try
    {
        Result = ${namespaced("set_profile")}(this->device, Buf);
        if (Result == device_undefined)
        {
            ${namespaced("close_device")}(&device);
        }
    }
    catch(...)
    {
        logAdd("General error");
        logAdd("Abort");
        delete[] Buf;
        return;
    }
    logAdd("set_profile returned " + QString::number(Result));

    logAdd("Done");
    Profile.close();
}