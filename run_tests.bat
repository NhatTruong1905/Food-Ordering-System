@echo off
chcp 65001 >nul
echo ===================================================
echo   CHƯƠNG TRÌNH CHẠY KIỂM THỬ TỰ ĐỘNG (UNIT TESTS)
echo ===================================================
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe run_tests.py
) else (
    python run_tests.py
)
pause
