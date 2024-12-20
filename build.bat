rem 最初に setup.py の ver を更新しないとちゃんと動かないかも


del /Q brepmatching.egg-info\*
del /Q build\*
del /Q dist\*
rmdir /S /Q brepmatching.egg-info
rmdir /S /Q build
rmdir /S /Q dist


poetry install --no-root
poetry run python setup.py build
rem なぜか setup.py install すると既存の pip の環境を壊してまで関連ライブラリを入れようとするので
rem build してから build フォルダの中身をプロジェクトルートに移動すること
