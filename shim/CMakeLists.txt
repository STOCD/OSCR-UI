find_package(Python COMPONENTS Interpreter Development)
find_package(Qt6 REQUIRED COMPONENTS Core Widgets)

qt_add_executable(${NAME} main.cpp)

target_link_libraries(${NAME} PUBLIC Python::Python)
target_link_libraries(${NAME} PUBLIC Qt6::Core)
target_link_libraries(${NAME} PUBLIC Qt6::Widgets)
