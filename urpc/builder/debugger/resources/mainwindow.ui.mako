<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>945</width>
    <height>751</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>${protocol.name}_debugger</string>
  </property>
  <property name="windowIcon">
   <iconset>
    <normaloff>:/new/prefix1/urpc_logo.png</normaloff>:/new/prefix1/urpc_logo.png</iconset>
  </property>
  <widget class="QWidget" name="centralwidget">
   <layout class="QGridLayout" name="gridLayout_3">
    <item row="1" column="0" colspan="2">
     <widget class="QListWidget" name="LogWidget">
      <property name="sizePolicy">
       <sizepolicy hsizetype="Expanding" vsizetype="Maximum">
        <horstretch>2</horstretch>
        <verstretch>0</verstretch>
       </sizepolicy>
      </property>
      <property name="maximumSize">
       <size>
        <width>16777215</width>
        <height>16777215</height>
       </size>
      </property>
      <property name="palette">
       <palette>
        <active>
         <colorrole role="WindowText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>109</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Button">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Light">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Midlight">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Text">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>111</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="BrightText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Base">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Window">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Shadow">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="HighlightedText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="AlternateBase">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="ToolTipBase">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
        </active>
        <inactive>
         <colorrole role="WindowText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>109</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Button">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Light">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Midlight">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Text">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>111</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="BrightText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Base">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Window">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Shadow">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="HighlightedText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="AlternateBase">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="ToolTipBase">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
        </inactive>
        <disabled>
         <colorrole role="WindowText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>120</red>
            <green>120</green>
            <blue>120</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Button">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Light">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Midlight">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Text">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>120</red>
            <green>120</green>
            <blue>120</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="BrightText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Base">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Window">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="Shadow">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="HighlightedText">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="AlternateBase">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
         <colorrole role="ToolTipBase">
          <brush brushstyle="SolidPattern">
           <color alpha="255">
            <red>0</red>
            <green>0</green>
            <blue>0</blue>
           </color>
          </brush>
         </colorrole>
        </disabled>
       </palette>
      </property>
      <property name="font">
       <font>
        <family>Simplified Arabic Fixed</family>
        <pointsize>12</pointsize>
       </font>
      </property>
      <property name="selectionMode">
       <enum>QAbstractItemView::NoSelection</enum>
      </property>
      <property name="layoutMode">
       <enum>QListView::SinglePass</enum>
      </property>
     </widget>
    </item>
    <item row="0" column="0" colspan="2">
     <layout class="QHBoxLayout" name="horizontalLayout">
      <item>
       <layout class="QVBoxLayout" name="verticalLayout">
        <item>
         <layout class="QFormLayout" name="formLayout">
          <item row="1" column="0">
           <widget class="QLineEdit" name="SearchEdit">
            <property name="sizePolicy">
             <sizepolicy hsizetype="Expanding" vsizetype="Fixed">
              <horstretch>1</horstretch>
              <verstretch>0</verstretch>
             </sizepolicy>
            </property>
           </widget>
          </item>
          <item row="0" column="1">
           <widget class="QLabel" name="label_2">
            <property name="text">
             <string>URL</string>
            </property>
           </widget>
          </item>
          <item row="1" column="1">
           <layout class="QHBoxLayout" name="horizontalLayout_4">
            <item>
             <widget class="QLineEdit" name="comEdit">
              <property name="sizePolicy">
               <sizepolicy hsizetype="Expanding" vsizetype="Fixed">
                <horstretch>0</horstretch>
                <verstretch>0</verstretch>
               </sizepolicy>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QPushButton" name="cntButton">
              <property name="text">
               <string>Connect</string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QPushButton" name="dcntButton">
              <property name="text">
               <string>Disconnect</string>
              </property>
             </widget>
            </item>
            <item>
             <spacer name="horizontalSpacer">
              <property name="orientation">
               <enum>Qt::Horizontal</enum>
              </property>
              <property name="sizeHint" stdset="0">
               <size>
                <width>40</width>
                <height>20</height>
               </size>
              </property>
             </spacer>
            </item>
            <item>
             <widget class="QPushButton" name="GetProfileBtn">
              <property name="text">
               <string>Get profile</string>
              </property>
             </widget>
            </item>
            <item>
             <widget class="QPushButton" name="SetProfileBtn">
              <property name="text">
               <string>Set profile</string>
              </property>
             </widget>
            </item>
           </layout>
          </item>
          <item row="0" column="0">
           <widget class="QLabel" name="label">
            <property name="text">
             <string>Search command</string>
            </property>
           </widget>
          </item>
         </layout>
        </item>
       </layout>
      </item>
     </layout>
    </item>
    <item row="2" column="0">
     <spacer name="horizontalSpacer_2">
      <property name="orientation">
       <enum>Qt::Horizontal</enum>
      </property>
      <property name="sizeType">
       <enum>QSizePolicy::Minimum</enum>
      </property>
      <property name="sizeHint" stdset="0">
       <size>
        <width>80</width>
        <height>20</height>
       </size>
      </property>
     </spacer>
    </item>
    <item row="2" column="1">
     <widget class="QPushButton" name="ClearBtn">
      <property name="sizePolicy">
       <sizepolicy hsizetype="Fixed" vsizetype="Fixed">
        <horstretch>1</horstretch>
        <verstretch>0</verstretch>
       </sizepolicy>
      </property>
      <property name="text">
       <string>Clean</string>
      </property>
     </widget>
    </item>
   </layout>
  </widget>
  <action name="actionAq">
   <property name="text">
    <string>Aq</string>
   </property>
  </action>
  <action name="actionA2">
   <property name="text">
    <string>A2</string>
   </property>
  </action>
 </widget>
 <layoutdefault spacing="6" margin="11"/>
 <resources/>
 <connections/>
</ui>
