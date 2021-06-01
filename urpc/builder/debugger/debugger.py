from os.path import abspath, join, dirname
from zipfile import ZipFile, ZIP_DEFLATED
from textwrap import dedent

# TODO: don't use mako here; see clib generator for example
from mako.lookup import TemplateLookup

from urpc.builder.util import ClangView
from urpc.builder.util.resource import resources

_module_path = abspath(dirname(__file__))
_lookup = TemplateLookup((join(_module_path, "resources"),), input_encoding="utf-8", output_encoding="utf-8")


class DebuggerView(ClangView):

    def __init__(self, project):
        super().__init__(project)

        self._setters = []

        for acc in self._accessors:
            self._setters.append(acc[1])

    @property
    def argstructs(self):
        return self._argstructs

    def is_setter(self, cmd):
        return True if cmd in self._setters else False

    def build_cmake_lists(self) -> str:
        text = dedent(f"""
        cmake_minimum_required(VERSION 2.8)

        project(uRPC_debugger)

        # Tell CMake to run moc when necessary:
        set(CMAKE_AUTOMOC ON)
        set(CMAKE_AUTORCC ON)
        set(CMAKE_AUTOUIC ON)
        if(${{CMAKE_VERSION}} VERSION_GREATER_EQUAL "3.10.0")
            cmake_policy(SET CMP0071 OLD)
        endif()

        # Include current directory
        set (CMAKE_INCLUDE_CURRENT_DIR ON)

        # Search libraries in current directory
        link_directories(${{CMAKE_SOURCE_DIR}})

        set (USE_QT5 FALSE)

        if(${{FORCE_QT4}})
            set (USE_QT5 FALSE)
        elseif(${{FORCE_QT5}})
            set (USE_QT5 TRUE)
        else()
            # Detect QT version
            find_package(Qt4 QUIET)
            find_package(Qt5Widgets QUIET)
            if(${{Qt4_FOUND}})
                message("Qt4 will be used")
                set (USE_QT5 FALSE)
            elseif(${{Qt5Widgets_FOUND}})
                message("Qt5 will be used")
                set (USE_QT5 TRUE)
            else()
                message(FATAL_ERROR "No Qt4/Qt5 found")
            endif()
        endif()

        if(NOT ${{USE_QT5}})
            find_package(Qt4 REQUIRED QtCore QtGui QtMain)
            include(${{QT_USE_FILE}})
        endif()

        if(${{USE_QT5}})
            find_package(Qt5Widgets REQUIRED)
            include_directories(${{Qt5Widgets_INCLUDES}})
            add_definitions(${{QtWidgets_DEFINITIONS}})
            set(CMAKE_CXX_FLAGS "${{Qt5Widgets_EXECUTABLE_COMPILE_FLAGS}}")
        endif()

        set(SOURCES
            main.cpp
            floatinput.cpp
            mainwindow.cpp
            intinput.cpp
            iopanel.cpp
            floatarrinput.cpp
            intarrinput.cpp
            floatoutput.cpp
            intoutput.cpp
            floatarroutput.cpp
            intarroutput.cpp
            multilist.cpp
            validlineedit.cpp
            base_io_widget.cpp
            container.cpp)

        set(HEADERS
            floatinput.h
            mainwindow.h
            intinput.h
            iopanel.h
            floatarrinput.h
            intarrinput.h
            floatoutput.h
            intoutput.h
            floatarroutput.h
            intarroutput.h
            multilist.h
            validlineedit.h
            base_io_widget.h
            container.h
            {self.name}.h)

        set(UIS
            floatinput.ui
            mainwindow.ui
            intinput.ui
            iopanel.ui
            floatarrinput.ui
            intarrinput.ui
            floatoutput.ui
            intoutput.ui
            floatarroutput.ui
            intarroutput.ui
            container.ui)

        source_group("Generated Sources - Do Not Edit" FILES ${{GENERATED_SOURCES}})

        include_directories(${{CMAKE_BINARY_DIR}})

        add_executable(uRPC_debugger
             # source files that are actually built directLy
             ${{SOURCES}}
             ${{GENERATED_SOURCES}}

             # items included so they show up in your IDE
             ${{HEADERS}}
             ${{UIS}}
             ${{RESOURCES}})

        if(${{USE_QT5}})
            set(QT_LIBS Qt5::Widgets)
        else()
            set(QT_LIBS ${{QT_LIBRARIES}})
        endif()

        target_link_libraries(uRPC_debugger ${{QT_LIBS}} {self.name} ${{CMAKE_THREAD_LIBS_INIT}})

        if(WIN32)
            set_property(DIRECTORY ${{CMAKE_CURRENT_SOURCE_DIR}} PROPERTY VS_STARTUP_PROJECT uRPC_debugger)
            set_target_properties(uRPC_debugger PROPERTIES WIN32_EXECUTABLE YES)
        endif()

        if (WIN32)
        add_custom_command(TARGET uRPC_debugger POST_BUILD
            COMMAND ${{CMAKE_COMMAND}} -E copy_if_different
                    "${{PROJECT_SOURCE_DIR}}/{self.name}.dll"
                    $<TARGET_FILE_DIR:uRPC_debugger>)
        endif()
        """)

        return text


def build(project, output):
    view = DebuggerView(project)
    utils = {
        "argstructs": view.argstructs,
        "library_shared_file": view.library_shared_file,
        "library_header_file": view.library_header_file
    }

    subdir_path = join(_module_path, "resources")
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file in resources(subdir_path):
            archive_path = file[len(subdir_path) + 1:]
            if file.endswith(".mako"):
                # if "Project.cpp.mako" in file or "Project.h.mako" in file:
                archive.writestr(archive_path.replace(".mako", ""), _lookup.get_template(archive_path).render_unicode(
                    protocol=project,
                    is_namespaced=True,
                    view=view,
                    **utils
                ))
            else:
                archive.write(file, archive_path)
        archive.writestr("CMakeLists.txt", view.build_cmake_lists())
