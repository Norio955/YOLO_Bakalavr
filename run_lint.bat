@echo off
echo --- Running Black (Formatting) ---
black .
echo.
echo --- Running Pylint (Quality) ---
pylint main.py
echo.
echo --- Running Mypy (Types) ---
mypy main.py
echo.
echo --- All checks finished! ---
pause