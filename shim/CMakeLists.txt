find_package(Python COMPONENTS Interpreter Development)

add_executable(${NAME} main.cpp)

target_link_libraries(${NAME} PUBLIC Python::Python)
