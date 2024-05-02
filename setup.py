import os
import sys
import logging
import subprocess
from multiprocessing import cpu_count
from pathlib import Path
from platform import system
import wheel.bdist_wheel as orig

from setuptools import setup, Extension
from setuptools.command.install import install
from setuptools.command.build_ext import build_ext


default_lib_dir = (
    "" if system() == "Windows" else os.path.join(os.getenv("HOME"), ".local")
)

# ---------- set environment variables for vcpkg on Windows ----------------------------


def set_vcpkg_environment_variables():
    if not os.getenv("VCPKG_ROOT_DIR"):
        raise OSError("Environment variable 'VCPKG_ROOT_DIR' is undefined.")
    if not os.getenv("VCPKG_DEFAULT_TRIPLET"):
        raise OSError("Environment variable 'VCPKG_DEFAULT_TRIPLET' is undefined.")
    if not os.getenv("VCPKG_FEATURE_FLAGS"):
        raise OSError("Environment variable 'VCPKG_FEATURE_FLAGS' is undefined.")
    return (
        os.getenv("VCPKG_ROOT_DIR"),
        os.getenv("VCPKG_DEFAULT_TRIPLET"),
        os.getenv("VCPKG_FEATURE_FLAGS"),
    )


# ---------- CMakeBuild class (custom build_ext for IDAKLU target) ---------------------


class CMakeBuild(build_ext):
    user_options = [
        *build_ext.user_options,
        ("suitesparse-root=", None, "suitesparse source location"),
        ("sundials-root=", None, "sundials source location"),
    ]

    def initialize_options(self):
        build_ext.initialize_options(self)
        self.suitesparse_root = None
        self.sundials_root = None

    def finalize_options(self):
        build_ext.finalize_options(self)
        # Determine the calling command to get the
        # undefined options from.
        # If build_ext was called directly then this
        # doesn't matter.
        try:
            self.get_finalized_command("install", create=0)
            calling_cmd = "install"
        except AttributeError:
            calling_cmd = "bdist_wheel"
        self.set_undefined_options(
            calling_cmd,
            ("suitesparse_root", "suitesparse_root"),
            ("sundials_root", "sundials_root"),
        )
        if not self.suitesparse_root:
            self.suitesparse_root = os.path.join(default_lib_dir)
        if not self.sundials_root:
            self.sundials_root = os.path.join(default_lib_dir)

    def get_build_directory(self):
        # setuptools outputs object files in directory self.build_temp
        # (typically build/temp.*). This is our CMake build directory.
        # On Windows, setuptools is too smart and appends "Release" or
        # "Debug" to self.build_temp. So in this case we want the
        # build directory to be the parent directory.
        if system() == "Windows":
            return Path(self.build_temp).parents[0]
        return self.build_temp

    def run(self):
        if not self.extensions:
            return

        # Build in parallel wherever possible
        os.environ["CMAKE_BUILD_PARALLEL_LEVEL"] = str(cpu_count())

        if system() == "Windows":
            use_python_casadi = False
        else:
            use_python_casadi = True

        build_type = os.getenv("PYBAMM_CPP_BUILD_TYPE", "RELEASE")
        cmake_args = [
            f"-DCMAKE_BUILD_TYPE={build_type}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            "-DUSE_PYTHON_CASADI={}".format("TRUE" if use_python_casadi else "FALSE"),
            "-DPYBAMM_IDAKLU_EXPR_IREE=ON",
            "-GNinja",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ]
        if self.suitesparse_root:
            cmake_args.append(
                f"-DSuiteSparse_ROOT={os.path.abspath(self.suitesparse_root)}"
            )
        if self.sundials_root:
            cmake_args.append(f"-DSUNDIALS_ROOT={os.path.abspath(self.sundials_root)}")

        build_dir = self.get_build_directory()
        if not os.path.exists(build_dir):
            os.makedirs(build_dir)

        # The CMakeError.log file is generated by cmake is the configure step
        # encounters error. In the following the existence of this file is used
        # to determine whether or not the cmake configure step went smoothly.
        # So must make sure this file does not remain from a previous failed build.
        if os.path.isfile(os.path.join(build_dir, "CMakeError.log")):
            os.remove(os.path.join(build_dir, "CMakeError.log"))

        # ---------- configuration for vcpkg on Windows ----------------------------------------

        build_env = os.environ
        if os.getenv("PYBAMM_USE_VCPKG"):
            (
                vcpkg_root_dir,
                vcpkg_default_triplet,
                vcpkg_feature_flags,
            ) = set_vcpkg_environment_variables()
            build_env["vcpkg_root_dir"] = vcpkg_root_dir
            build_env["vcpkg_default_triplet"] = vcpkg_default_triplet
            build_env["vcpkg_feature_flags"] = vcpkg_feature_flags

        # ---------- Run CMake and build IDAKLU module -----------------------------------------

        cmake_list_dir = os.path.abspath(os.path.dirname(__file__))
        print("-" * 10, "Running CMake for IDAKLU solver", "-" * 40)
        subprocess.run(
            ["cmake", cmake_list_dir, *cmake_args],
            cwd=build_dir,
            env=build_env,
            check=True,
        )

        if os.path.isfile(os.path.join(build_dir, "CMakeError.log")):
            msg = (
                "cmake configuration steps encountered errors, and the IDAKLU module"
                " could not be built. Make sure dependencies are correctly "
                "installed. See "
                "https://docs.pybamm.org/en/latest/source/user_guide/installation/install-from-source.html"
            )
            raise RuntimeError(msg)
        else:
            print("-" * 10, "Building IDAKLU module", "-" * 40)
            subprocess.run(
                ["cmake", "--build", ".", "--config", "Release"],
                cwd=build_dir,
                env=build_env,
                check=True,
            )

            # Move from build temp to final position
            for ext in self.extensions:
                self.move_output(ext)

    def move_output(self, ext):
        # Copy built module to dist/ directory
        build_temp = Path(self.build_temp).resolve()
        # Get destination location
        # self.get_ext_fullpath(ext.name) -->
        # build/lib.linux-x86_64-3.5/idaklu.cpython-37m-x86_64-linux-gnu.so
        # using resolve() with python < 3.6 will result in a FileNotFoundError
        # since the location does not yet exists.
        dest_path = Path(self.get_ext_fullpath(ext.name)).resolve()
        source_path = build_temp / os.path.basename(self.get_ext_filename(ext.name))
        dest_directory = dest_path.parents[0]
        dest_directory.mkdir(parents=True, exist_ok=True)
        self.copy_file(source_path, dest_path)


# ---------- end of CMake steps --------------------------------------------------------


# ---------- configure setup logger ----------------------------------------------------


log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger("PyBaMM setup")

# To override the default severity of logging
logger.setLevel("INFO")

# Use FileHandler() to log to a file
logfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup.log")
file_handler = logging.FileHandler(logfile)
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)

# Add the file handler
logger.addHandler(file_handler)
logger.info("Starting PyBaMM setup")


class CustomInstall(install):
    """A custom install command to add 2 build options"""

    user_options = [
        *install.user_options,
        ("suitesparse-root=", None, "suitesparse source location"),
        ("sundials-root=", None, "sundials source location"),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.suitesparse_root = None
        self.sundials_root = None

    def finalize_options(self):
        install.finalize_options(self)
        if not self.suitesparse_root:
            self.suitesparse_root = default_lib_dir
        if not self.sundials_root:
            self.sundials_root = default_lib_dir

    def run(self):
        install.run(self)


# ---------- Custom class for building wheels ------------------------------------------


class bdist_wheel(orig.bdist_wheel):
    """A custom install command to add 2 build options"""

    user_options = [
        *orig.bdist_wheel.user_options,
        ("suitesparse-root=", None, "suitesparse source location"),
        ("sundials-root=", None, "sundials source location"),
    ]

    def initialize_options(self):
        orig.bdist_wheel.initialize_options(self)
        self.suitesparse_root = None
        self.sundials_root = None

    def finalize_options(self):
        orig.bdist_wheel.finalize_options(self)
        if not self.suitesparse_root:
            self.suitesparse_root = default_lib_dir
        if not self.sundials_root:
            self.sundials_root = default_lib_dir

    def run(self):
        orig.bdist_wheel.run(self)


def compile_KLU():
    # Return whether or not the KLU extension should be compiled.
    # Return True if:
    # - Not running on Windows AND
    # - CMake is found AND
    # - The pybind11/ directory is found in the PyBaMM project directory
    CMakeFound = True
    PyBind11Found = True
    windows = (not system()) or system() == "Windows"

    msg = "Running on Windows" if windows else "Not running on windows"
    logger.info(msg)

    try:
        subprocess.run(["cmake", "--version"])
        logger.info("Found CMake.")
    except OSError:
        CMakeFound = False
        logger.info("Could not find CMake. Skipping compilation of KLU module.")

    pybamm_project_dir = os.path.dirname(os.path.abspath(__file__))
    pybind11_dir = os.path.join(pybamm_project_dir, "pybind11")
    try:
        open(os.path.join(pybind11_dir, "tools", "pybind11Tools.cmake"))
        logger.info(f"Found pybind11 directory ({pybind11_dir})")
    except FileNotFoundError:
        PyBind11Found = False
        msg = (
            f"Could not find PyBind11 directory ({pybind11_dir})."
            " Skipping compilation of KLU module."
        )
        logger.info(msg)

    return CMakeFound and PyBind11Found


idaklu_ext = Extension(
    name="pybamm.solvers.idaklu",
    # The sources list should mirror the list in CMakeLists.txt
    sources=[
        "pybamm/solvers/c_solvers/idaklu/Expressions/Expressions.hpp",
        "pybamm/solvers/c_solvers/idaklu/Expressions/Base/Expression.hpp",
        "pybamm/solvers/c_solvers/idaklu/Expressions/Base/ExpressionSet.hpp",
        "pybamm/solvers/c_solvers/idaklu/Expressions/Base/ExpressionTypes.hpp",
        "pybamm/solvers/c_solvers/idaklu/Expressions/Base/ExpressionSparsity.hpp",
        "pybamm/solvers/c_solvers/idaklu/Expressions/Casadi/CasadiFunctions.cpp",
        "pybamm/solvers/c_solvers/idaklu/Expressions/Casadi/CasadiFunctions.hpp",
        "pybamm/solvers/c_solvers/idaklu/idaklu_solver.hpp",
        "pybamm/solvers/c_solvers/idaklu/IDAKLUSolver.cpp",
        "pybamm/solvers/c_solvers/idaklu/IDAKLUSolver.hpp",
        "pybamm/solvers/c_solvers/idaklu/IDAKLUSolverOpenMP.inl",
        "pybamm/solvers/c_solvers/idaklu/IDAKLUSolverOpenMP.hpp",
        "pybamm/solvers/c_solvers/idaklu/IDAKLUSolverOpenMP_solvers.cpp",
        "pybamm/solvers/c_solvers/idaklu/IDAKLUSolverOpenMP_solvers.hpp",
        "pybamm/solvers/c_solvers/idaklu/sundials_functions.inl",
        "pybamm/solvers/c_solvers/idaklu/sundials_functions.hpp",
        "pybamm/solvers/c_solvers/idaklu/IdakluJax.cpp",
        "pybamm/solvers/c_solvers/idaklu/IdakluJax.hpp",
        "pybamm/solvers/c_solvers/idaklu/common.hpp",
        "pybamm/solvers/c_solvers/idaklu/python.hpp",
        "pybamm/solvers/c_solvers/idaklu/python.cpp",
        "pybamm/solvers/c_solvers/idaklu/Solution.cpp",
        "pybamm/solvers/c_solvers/idaklu/Solution.hpp",
        "pybamm/solvers/c_solvers/idaklu/Options.hpp",
        "pybamm/solvers/c_solvers/idaklu/Options.cpp",
        "pybamm/solvers/c_solvers/idaklu.cpp",
    ],
)
ext_modules = [idaklu_ext] if compile_KLU() else []

# Project metadata was moved to pyproject.toml (which is read by pip). However, custom
# build commands and setuptools extension modules are still defined here.
setup(
    # silence "Package would be ignored" warnings
    include_package_data=True,
    ext_modules=ext_modules,
    cmdclass={
        "build_ext": CMakeBuild,
        "bdist_wheel": bdist_wheel,
        "install": CustomInstall,
    },
)
