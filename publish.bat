del /Q brepmatching.egg-info\*
del /Q build\*
del /Q dist\*
rmdir /S /Q brepmatching.egg-info
rmdir /S /Q build
rmdir /S /Q dist

rem python setup.py bdist_wheel
python setup.py sdist
twine upload --repository pypi dist/* --username __token__ --password %PYPI_API_KEY_SECRET%

rem Build using poetry is NOT IMPLEMENTED
rem poetry build --format=sdist
rem poetry publish --username __token__ --password %PYPI_API_KEY_SECRET%
