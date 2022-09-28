cmake_minimum_required(VERSION 3.5)
project(ZED_Hub_Tutorial_1)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ZED 3 REQUIRED)
find_package(CUDA ${ZED_CUDA_VERSION} REQUIRED)
find_package(OpenSSL REQUIRED)

set(ZED_LIBS ${ZED_LIBRARIES} ${CUDA_CUDA_LIBRARY} ${CUDA_CUDART_LIBRARY})
set(SL_IOT_LIB_DIR /usr/local/sl_iot/lib/)
set(SL_IOT_INCLUDE_DIR /usr/local/sl_iot/include/)
set(UTILS_LIB pthread util dl)

include_directories(${ZED_INCLUDE_DIRS})
include_directories(${SL_IOT_INCLUDE_DIR})
include_directories(${CUDA_INCLUDE_DIRS})
include_directories(${OPENSSL_INCLUDE_DIR})

link_directories(${ZED_LIBRARY_DIR})
link_directories(${SL_IOT_LIB_DIR})
link_directories(${CUDA_LIBRARY_DIRS})
link_directories(${OPENSSL_SSL_LIBRARY})

add_executable(${PROJECT_NAME} main.cpp)

target_link_libraries(${PROJECT_NAME} ${ZED_LIBS} sl_iot ${OPENSSL_LIBRARIES} ${UTILS_LIB})
