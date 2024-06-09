find_package(Python COMPONENTS Interpreter Development)
find_package(Qt6 REQUIRED COMPONENTS Core Widgets)

qt_add_executable(${NAME} main.cpp)
