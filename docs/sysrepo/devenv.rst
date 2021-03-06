Setting up a development environment
====================================

All the instructions are `on the sysrepo github <https://github.com/sysrepo/sysrepo/blob/master/INSTALL.md>`__.
Then try to get as many of the dependencies from your package manager.

.. note::
   The YANG file we've create crashes the released version of libyang, so for both libyang and sysrepo, the "devel" branches should be built.

Installing libredblack on Arch
------------------------------
To install libredblack on Arch Linux, download the tarball and configure it::

   USE_RBGEN=false ./configure --prefix=$HOME/.local/opt/sysrepo && make install

Installing libyang
------------------
Clone the `repo <https://github.com/CESNET/libyang>`__ and::

  git checkout devel
  mkdir build
  cd build
  cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX:PATH=$HOME/.local/opt/sysrepo ..
  make install


Installing sysrepo
------------------
Clone the repo, then::

  git checkout devel

To make sure the python bindings are not installed to `/usr/lib`, apply this patch:

.. code-block:: diff

   diff --git a/swig/python/CMakeLists.txt b/swig/python/CMakeLists.txt
   index 89197711..a4f306bd 100644
   --- a/swig/python/CMakeLists.txt
   +++ b/swig/python/CMakeLists.txt
   @@ -23,10 +23,10 @@ swig_link_libraries(${PYTHON_SWIG_BINDING} ${PYTHON_LIBRARIES} Sysrepo-cpp)
    
    file(COPY "examples" DESTINATION "${CMAKE_CURRENT_BINARY_DIR}")
    
   -execute_process(COMMAND
   -    ${PYTHON_EXECUTABLE} -c
   -    "from distutils.sysconfig import get_python_lib; print(get_python_lib())"
   -OUTPUT_VARIABLE PYTHON_MODULE_PATH OUTPUT_STRIP_TRAILING_WHITESPACE)
   +#execute_process(COMMAND
   +#    ${PYTHON_EXECUTABLE} -c
   +#    "from distutils.sysconfig import get_python_lib; print(get_python_lib())"
   +#OUTPUT_VARIABLE PYTHON_MODULE_PATH OUTPUT_STRIP_TRAILING_WHITESPACE)
    
    install( FILES "${CMAKE_CURRENT_BINARY_DIR}/_${PYTHON_SWIG_BINDING}.so" DESTINATION ${PYTHON_MODULE_PATH} )
    install( FILES "${CMAKE_CURRENT_BINARY_DIR}/${PYTHON_SWIG_BINDING}.py" DESTINATION ${PYTHON_MODULE_PATH} )

Then configure and install::

  mkdir build; cd build
  cmake -DIS_DEVELOPER_CONFIGURATION=1 -DCMAKE_INSTALL_PREFIX:PATH=$HOME/.local/opt/sysrepo -DGEN_LUA_BINDINGS=0 -DGEN_PYTHON_VERSION=3 -DPYTHON_MODULE_PATH=$HOME/.local/opt/sysrepo/lib/python3.7/site-packages ..
  make install

Using sysrepo
-------------

After installing sysrepo, amend the ``PATH``, ``LD_LIBRARY_PATH`` and ``PYTHONPATH`` environment variables::

  export PATH=$HOME/.local/opt/sysrepo/bin:$PATH
  export LD_LIBRARY_PATH=$HOME/.local/opt/sysrepo/lib:$LD_LIBRARY_PATH
  export PYTHONPATH=$HOME/.local/opt/sysrepo/lib/python3.6/site-packages:$PYTHONPATH

Now you can use the sysrepo python library and tools like ``sysrepoctl`` and ``sysrepocfg``.
