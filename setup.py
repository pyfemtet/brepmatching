from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig
import os
import sys
import pathlib
import pybind11


## From https://stackoverflow.com/questions/42585210/extending-setuptools-extension-to-use-cmake-in-setup-py ##

class CMakeExtension(Extension):

    def __init__(self, name):
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])


class build_ext(build_ext_orig):

    def run(self):
        for ext in self.extensions:
            self.build_cmake(ext)
        super().run()

    def build_cmake(self, ext):
        cwd = pathlib.Path().absolute()

        # these dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        build_temp = pathlib.Path(self.build_temp)
        build_temp.mkdir(parents=True, exist_ok=True)
        extdir = pathlib.Path(self.get_ext_fullpath(ext.name))
        extdir.parent.mkdir(parents=True, exist_ok=True)

        # example of cmake args
        config = 'Debug' if self.debug else 'Release'
        pybind11_dir = str(pathlib.Path(pybind11.__file__).parent/'share'/'cmake'/'pybind11').replace('\\', '/')
        python_executable = sys.executable.replace('\\', '/')
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_%s=%s' % (config.upper(), str(extdir.parent.absolute())),
            '-DCMAKE_BUILD_TYPE=%s' % config,
            '-DCMAKE_BUILD_TYPE=%s' % config,
            f'-DPYTHON_EXECUTABLE={python_executable}',  # Python パスが空白を含んでも動作する
            f'-Dpybind11_DIR={pybind11_dir}',  # 隔離環境にあるので空白は入らなし、入っても動作する
        ]

        # example of build args
        build_args = [
            '--config', config
        ]

        os.chdir(str(build_temp))
        self.spawn(['cmake', str(cwd)] + cmake_args)
        if not self.dry_run:
            self.spawn(['cmake', '--build', '.'] + build_args)
        # Troubleshooting: if fail on line above then delete all possible 
        # temporary CMake files including "CMakeCache.txt" in top level dir.
        os.chdir(str(cwd))

## End from https://stackoverflow.com/questions/42585210/extending-setuptools-extension-to-use-cmake-in-setup-py ##


setup(
    ext_modules=[
        CMakeExtension('coincidence_matching'),
        CMakeExtension('set_attributes'),
        CMakeExtension('automate_cpp'),
    ],
    cmdclass={
        'build_ext': build_ext
    },
)
