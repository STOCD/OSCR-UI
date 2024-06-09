#include <exception>
#include <iostream>

#include <Python.h>

// nix-shell -p cmake gdb qt6.full

static int init_python(int argc, char **argv) {
  const char *executable = "venv/bin/python";
  const char *home = "venv";
  size_t size;
  PyConfig config;
  PyStatus status;

  PyConfig_InitIsolatedConfig(&config);

  status = PyConfig_SetBytesString(&config, &config.executable, executable);
  if (PyStatus_Exception(status)) {
    throw std::runtime_error("Failed to set executable venv");
  }

  status = PyConfig_SetBytesString(&config, &config.home, home);
  if (PyStatus_Exception(status)) {
    throw std::runtime_error("Failed to set executable venv");
  }

  Py_InitializeFromConfig(&config);
  PyConfig_Clear(&config);
  return 0;
}

static int init_main(int argc, char **argv) {
  const char *fname = "main.py";
  PyObject *obj = Py_BuildValue("s", fname);
  FILE *fp = _Py_fopen_obj(obj, "rb");
  if (NULL == fp) {
    throw std::runtime_error("Failed to open main.py");
  }

  int ret = PyRun_SimpleFile(fp, fname);
  fclose(fp);
  Py_Finalize();
  if (ret) {
    PyErr_Print();
    throw std::runtime_error("Failed to run main.py");
  }
  return 0;
}

static int run(int argc, char **argv) {
  int ret = 0;

  ret = init_python(argc, argv);
  if (ret) {
    throw std::runtime_error("Failed to initialize python");
  }

  ret = init_main(argc, argv);
  if (ret) {
    throw std::runtime_error("Failed to initialize qt");
  }

  return 0;
}

int main(int argc, char **argv) {
  int ret = 0;
  try {
    ret = run(argc, argv);
  } catch (std::exception &e) {
    std::cout << e.what() << std::endl;
  } catch (...) {
    std::cout << "Failed to parse exception" << std::endl;
  }
  return ret;
}
