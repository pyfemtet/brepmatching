from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig
import os
import sys
import pathlib
from pathlib import Path
import pybind11
from femtetutils import util


def get_requirements(filename):
    """Load requirements from a requirements file."""
    ret = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.replace(' ', '').replace('\n', '')
            line = line.split('#')[0]
            if len(line) > 0:
                ret.append(line)
    return ret


def get_femtet_dir_path():
    # read .debug if exists
    debug_file_path = Path(__file__).parent / '.debug'
    if os.path.exists(debug_file_path):
        with open(debug_file_path, 'r') as f:
            femtet_dir_path = f.read()

    else:
        # get Femtet root dir
        femtet_exe_path = util.get_femtet_exe_path()
        femtet_dir_path = os.path.dirname(femtet_exe_path)

    # If lib is not built, cannot use brepmatching.
    if not os.path.exists(os.path.join(femtet_dir_path, 'lib')):
        raise FileNotFoundError('Femtet >= 2025.0.0 required. '
                                'Your Femtet (with macros enabled) '
                                'appears to be less than 2025.0.0.')

    return femtet_dir_path


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
        femtet_lib_dir = f'{get_femtet_dir_path()}/lib'.replace('\\', '/')
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_%s=%s' % (config.upper(), str(extdir.parent.absolute())),
            '-DCMAKE_BUILD_TYPE=%s' % config,
            '-DCMAKE_BUILD_TYPE=%s' % config,
            f'-DPYTHON_EXECUTABLE={python_executable}',  # Python パスが空白を含んでも動作する
            f'-Dpybind11_DIR={pybind11_dir}',  # 隔離環境にあるので空白は入らなし、入っても動作する
            f'-DFEMTET_LIB_DIR={femtet_lib_dir}',
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
    name='brepmatching',
    version='0.1.4',
    description='Learning to match BRep Topology',
    author='Kazuma NAITO',
    author_email='kazuma.naito@murata.com',
    license='MIT',
    ext_modules=[
        CMakeExtension('coincidence_matching'),
        CMakeExtension('set_attributes'),
        CMakeExtension('automate_cpp'),
    ],
    cmdclass={
        'build_ext': build_ext
    },
    packages=find_packages(),
    package_data={
        'brepmatching': [
            'pyfemtet_scripts/data/dataset_to_predict/dataset/data/VariationData/*.csv',
            'pyfemtet_scripts/*.ckpt',
        ],
        'automate': [
            'cpp/*.cpp',
            'cpp/*.h',
            'include/Eigen/**',
            'CMakeLists.txt',
        ],
    },
    include_package_data=True,  # python package である brepmatching, automate 以外のファイルを配布物に含めるために MANIFEST.in を使います。
    install_requires=get_requirements('requirements.txt'),
)
