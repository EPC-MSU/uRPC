cmake_minimum_required(VERSION 2.8)
project(${device_name(protocol)} CXX)

# Detect correct C++11 flag
if(NOT ${"$"}{CMAKE_SYSTEM_NAME} STREQUAL Windows)
    include(CheckCXXCompilerFlag)
endif()
CHECK_CXX_COMPILER_FLAG("-std=c++11" COMPILER_SUPPORTS_CXX11)
CHECK_CXX_COMPILER_FLAG("-std=c++0x" COMPILER_SUPPORTS_CXX0X)

if(COMPILER_SUPPORTS_CXX11)
    set(CMAKE_CXX_FLAGS "${"$"}{CMAKE_CXX_FLAGS} -std=c++11")
elseif(COMPILER_SUPPORTS_CXX0X)
    set(CMAKE_CXX_FLAGS "${"$"}{CMAKE_CXX_FLAGS} -std=c++0x")
else()
    message(STATUS "The compiler ${"$"}{CMAKE_CXX_COMPILER} has no C++11 support. Please use a different C++ compiler.")
endif()

find_package(Threads)

find_package(PkgConfig)
pkg_check_modules(TANGO REQUIRED tango)
include_directories(${"$"}{TANGO_INCLUDE_DIRS})

include_directories(.)

set(HEADERS
    ${device_name(protocol)}.h
    ${device_name(protocol)}Class.h
)

set(SOURCES
    ClassFactory.cpp
    ${device_name(protocol)}.cpp
    ${device_name(protocol)}ReactiveAttributesPoll.cpp
    ${device_name(protocol)}StateMachine.cpp
    ${device_name(protocol)}Class.cpp
    main.cpp
)

add_executable(${server_name(protocol)} ${"$"}{HEADERS} ${"$"}{SOURCES})
target_link_libraries(${server_name(protocol)} ${"$"}{CMAKE_THREAD_LIBS_INIT} ${"$"}{TANGO_LIBRARIES} ${library_shared_file(protocol)})
