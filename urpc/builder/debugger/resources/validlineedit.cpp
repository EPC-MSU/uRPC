#include "validlineedit.h"

//-----------------------------
ValidFloatLineEdit::ValidFloatLineEdit(QWidget *parent, float minvalue, float maxvalue, int sizevalue) : QLineEdit(parent)
{
    min = minvalue;
    max = maxvalue;
    size = sizevalue;

    QObject::connect(this,SIGNAL(textChanged(QString)), this, SLOT(Edited(QString)));
}
///-------------------------------------------------
//---------------------------------------
void ValidIntLineEdit::Edited(QString str)
{
    if(Valid(str))
        plt.setColor(QPalette::Base,Qt::white);
    else
        plt.setColor(QPalette::Base,Qt::red);


      setPalette(plt);
}


//----------------------------------------
void ValidFloatLineEdit::Edited(QString str)
{
    if(Valid(str))
        plt.setColor(QPalette::Base,Qt::white);
    else
        plt.setColor(QPalette::Base,Qt::red);


      setPalette(plt);
}



//---------------------------------------------validators:
bool ValidIntLineEdit::Valid(QString str)
{
     ///"2345 2345 345 356 456 6 35646 -14 23 -123 " format

     QString temp = str;
     QString sub_str = "";
     bool ok = 1;
     
     if (min >= 0)
     {
         // ulong
         unsigned long long int n = 0;

         int count = 0;

         while(temp.contains(" ") && ok)
         {
             n = temp.left(temp.indexOf(' ')).toULongLong(&ok);

             // Fix signed and unsigned compare. TODO: more nice solution
             if((n > max && n > 0) || n < min)
                 return 0;

             temp = temp.right(temp.length()-temp.indexOf(' ')-1);

             if(count++ >= (size-1))
                 return 0;
         }

         if(!ok) return 0;


         n = temp.toULongLong(&ok);
         // Fix signed and unsigned compare. TODO: more nice solution
         if((n > max & n > 0) || n < min)
                 return 0;

         return ok;
     }
     else
     {
        // long
         long long int n = 0;

         int count = 0;

         while(temp.contains(" ") && ok)
         {
             n = temp.left(temp.indexOf(' ')).toLongLong(&ok);

             // Fix signed and unsigned compare. TODO: more nice solution
             if((n > max && n > 0) || n < min)
                 return 0;

             temp = temp.right(temp.length()-temp.indexOf(' ')-1);

             if(count++ >= (size-1))
                 return 0;
         }

         if(!ok) return 0;


         n = temp.toLongLong(&ok);
         // Fix signed and unsigned compare. TODO: more nice solution
         if((n > max & n > 0) || n < min)
                 return 0;

         return ok;        
     }
}
//---------------------------------------------------
bool ValidFloatLineEdit::Valid(QString str)
{
    ///"2345.536 2345.345 345.2345 356.123 4561 6 35646 -14.12 23 -123 " format

    QString temp = str;
    QString sub_str = "";
    bool ok = 1;

    float n = 0;

    int count = 0;

    while(temp.contains(" ") && ok)
    {

        n = temp.left(temp.indexOf(' ')).toFloat(&ok);
        if(n>max || n<min)
            return 0;

        temp = temp.right(temp.length()-temp.indexOf(' ')-1);


        if(count++ >= (size-1))
            return 0;


    }

    if(!ok) return 0;

    n = temp.toFloat(&ok);
    if(n > max || n < min)
            return 0;

    return ok;

}
