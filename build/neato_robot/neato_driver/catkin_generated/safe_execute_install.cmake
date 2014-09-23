execute_process(COMMAND "/home/shane/catkin_ws/src/comprobo2014/build/neato_robot/neato_driver/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/shane/catkin_ws/src/comprobo2014/build/neato_robot/neato_driver/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
