import io
import sys
import time
import unittest

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass


def run_all_tests():
    print("=" * 65)
    print(" BAT DAU CHAY TOAN BO UNIT TESTS (FOOD ORDERING SYSTEM)")
    print("=" * 65)

    start_time = time.time()

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='test', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    duration = time.time() - start_time
    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total - failures - errors

    print("\n" + "=" * 65)
    print(" BÁO CÁO TỔNG KẾT KẾT QUẢ KIỂM THỬ")
    print("=" * 65)
    print(f" • Tổng số test case : {total}")
    print(f" • Thành công        : {passed} tests")
    print(f" • Thất bại          : {failures} tests")
    print(f" • Lỗi ngoại lệ      : {errors} tests")
    print(f" • Thời gian chạy    : {duration:.2f} giây")
    print("=" * 65)

    if result.wasSuccessful():
        print(" [PASSED] TẤT CẢ CÁC TEST CASES ĐÃ VƯỢT QUA THÀNH CÔNG (100%)!\n")
        return 0
    else:
        print(" [FAILED] CÓ TEST CASE BỊ THẤT BẠI HOẶC LỖI. VUI LÒNG KIỂM TRA LẠI!\n")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
