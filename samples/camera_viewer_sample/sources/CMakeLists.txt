SET(execName app_executable)
cmake_minimum_required(VERSION 2.4)
PROJECT(${execName})

if(COMMAND cmake_policy)
	cmake_policy(SET CMP0003 OLD)
	cmake_policy(SET CMP0004 OLD)
	cmake_policy(SET CMP0015 OLD)
endif(COMMAND cmake_policy)

SET(EXECUTABLE_OUTPUT_PATH ".")
SET(SPECIAL_OS_LIBS "")

find_package(ZED 3 REQUIRED)
find_package(CUDA REQUIRED)
find_package(OpenSSL REQUIRED)

if(WIN32)
    SET(SL_IOT_BIN_DIR "$ENV{ZED_SDK_ROOT_DIR}/bin")
    SET(SL_IOT_LIB_DIR "$ENV{ZED_SDK_ROOT_DIR}/lib")
    SET(SL_IOT_INCLUDE_DIR "$ENV{ZED_SDK_ROOT_DIR}/include")
else(WIN32)
    SET(SPECIAL_OS_LIBS "pthread" "X11")
    add_definitions(-Wno-write-strings)
    SET(SL_IOT_LIB_DIR /usr/local/sl_iot/lib/)
    SET(SL_IOT_INCLUDE_DIR /usr/local/sl_iot/include/)
    SET(UTILS_LIB pthread util curl dl)
endif(WIN32)

include_directories(${ZED_INCLUDE_DIRS})
include_directories(${CUDA_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)
include_directories(${OPENSSL_INCLUDE_DIR})
include_directories(${SL_IOT_INCLUDE_DIR})

find_package(OpenSSL REQUIRED)
include_directories(${OPENSSL_INCLUDE_DIR})
link_directories(${OPENSSL_SSL_LIBRARY})

link_directories(${ZED_LIBRARY_DIR})
link_directories(${CUDA_LIBRARY_DIRS})
link_directories(${OPENSSL_SSL_LIBRARY})
link_directories(${SL_IOT_LIB_DIR})

FILE(GLOB_RECURSE SRC_FILES src/*.cpp)
FILE(GLOB_RECURSE HDR_FILES include/*.hpp)

add_definitions(-DOBFUSCATION)

ADD_EXECUTABLE(${PROJECT_NAME} ${HDR_FILES} ${SRC_FILES})
add_definitions(-std=c++14 -g -O3)
add_definitions(-DSL_IOT_WITH_ZED_SDK -DSL_CAPTURE)


SET(ZED_LIBS_EXT sl_iot ${ZED_LIBRARIES} ${CUDA_CUDA_LIBRARY} ${CUDA_CUDART_LIBRARY})

target_link_libraries(${PROJECT_NAME}
                        ${SPECIAL_OS_LIBS}
                        ${ZED_LIBS_EXT}
                        ${OPENSSL_LIBRARIES} ${UTILS_LIB})
