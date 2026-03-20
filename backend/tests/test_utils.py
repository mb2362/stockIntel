"""
test_utils.py – Pure helper function tests for stocks.py.
_safe_float · _safe_int · _compute_rsi · _compute_macd
TIME_RANGE_TO_PERIOD · TIME_RANGE_TO_V8 · QuoteParts
"""
import sys, os, importlib, unittest, math
sys.path.insert(0, os.path.dirname(__file__))
import conftest  # noqa
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pandas as pd

stocks = importlib.import_module("app.api.endpoints.stocks")
_safe_float  = stocks._safe_float
_safe_int    = stocks._safe_int
_compute_rsi = stocks._compute_rsi
_compute_macd = stocks._compute_macd
QuoteParts   = stocks.QuoteParts
TIME_RANGE   = stocks.TIME_RANGE_TO_PERIOD
TIME_RANGE_V8 = stocks.TIME_RANGE_TO_V8


class TestSafeFloat(unittest.TestCase):
    def test_normal_int(self):          self.assertEqual(_safe_float(42), 42.0)
    def test_normal_float(self):        self.assertAlmostEqual(_safe_float(3.14), 3.14)
    def test_string_number(self):       self.assertAlmostEqual(_safe_float("2.71"), 2.71)
    def test_none_default(self):        self.assertEqual(_safe_float(None), 0.0)
    def test_none_custom_default(self): self.assertEqual(_safe_float(None, default=99.9), 99.9)
    def test_nan_default(self):         self.assertEqual(_safe_float(float("nan")), 0.0)
    def test_invalid_str(self):         self.assertEqual(_safe_float("bad"), 0.0)
    def test_zero(self):                self.assertEqual(_safe_float(0), 0.0)
    def test_negative(self):            self.assertEqual(_safe_float(-5.5), -5.5)
    def test_large_number(self):        self.assertEqual(_safe_float(1_000_000_000), 1_000_000_000.0)
    def test_boolean_true(self):        self.assertEqual(_safe_float(True), 1.0)


class TestSafeInt(unittest.TestCase):
    def test_normal_int(self):          self.assertEqual(_safe_int(7), 7)
    def test_float_truncates(self):     self.assertEqual(_safe_int(3.9), 3)
    def test_string_number(self):       self.assertEqual(_safe_int("5"), 5)
    def test_none_default(self):        self.assertEqual(_safe_int(None), 0)
    def test_none_custom_default(self): self.assertEqual(_safe_int(None, default=-1), -1)
    def test_nan_default(self):         self.assertEqual(_safe_int(float("nan")), 0)
    def test_invalid_str(self):         self.assertEqual(_safe_int("abc"), 0)
    def test_zero(self):                self.assertEqual(_safe_int(0), 0)
    def test_negative(self):            self.assertEqual(_safe_int(-3), -3)
    def test_large(self):               self.assertEqual(_safe_int(10_000_000), 10_000_000)


class TestComputeRSI(unittest.TestCase):
    def _s(self, v): return pd.Series(v, dtype=float)

    def test_returns_float(self):
        self.assertIsInstance(_compute_rsi(self._s(range(50, 80))), float)

    def test_in_range_0_100(self):
        import random; random.seed(42)
        data = [100 + random.uniform(-5, 5) for _ in range(60)]
        r = _compute_rsi(self._s(data))
        self.assertGreaterEqual(r, 0.0); self.assertLessEqual(r, 100.0)

    def test_always_rising_returns_float(self):
        # avg_loss=0 → NA replacement → defaults to 0.0
        r = _compute_rsi(self._s(range(100, 160)))
        self.assertIsInstance(r, float); self.assertGreaterEqual(r, 0.0)

    def test_always_falling_low_rsi(self):
        r = _compute_rsi(self._s(range(160, 100, -1)))
        self.assertLess(r, 30.0)

    def test_short_series_returns_zero(self):
        self.assertEqual(_compute_rsi(self._s([100.0, 101.0, 99.0])), 0.0)

    def test_flat_series_returns_zero(self):
        self.assertEqual(_compute_rsi(self._s([100.0] * 30)), 0.0)

    def test_oscillating_series_in_range(self):
        data = [100 + math.sin(i * 0.4) * 8 for i in range(60)]
        r = _compute_rsi(self._s(data))
        self.assertGreaterEqual(r, 0.0); self.assertLessEqual(r, 100.0)

    def test_custom_period(self):
        data = [100 + math.sin(i * 0.4) * 8 for i in range(40)]
        r = _compute_rsi(self._s(data), period=7)
        self.assertIsInstance(r, float); self.assertGreaterEqual(r, 0.0)


class TestComputeMACD(unittest.TestCase):
    def _s(self, v): return pd.Series(v, dtype=float)

    def test_keys_present(self):
        r = _compute_macd(self._s([100 + i * 0.5 for i in range(50)]))
        for k in ("value", "signal", "histogram"): self.assertIn(k, r)

    def test_values_are_floats(self):
        r = _compute_macd(self._s([100 + i * 0.5 for i in range(50)]))
        for k, v in r.items(): self.assertIsInstance(v, float)

    def test_histogram_equals_value_minus_signal(self):
        r = _compute_macd(self._s([100 + i * 0.5 for i in range(50)]))
        self.assertAlmostEqual(r["histogram"], r["value"] - r["signal"], places=8)

    def test_short_series(self):
        r = _compute_macd(self._s([100.0, 101.0, 99.0]))
        self.assertIn("value", r)

    def test_oscillating(self):
        data = [100 + math.sin(i * 0.3) * 5 for i in range(60)]
        r = _compute_macd(self._s(data))
        self.assertIsInstance(r["value"], float)


class TestTimeRanges(unittest.TestCase):
    def test_all_keys_period(self):
        for k in ("1D", "1W", "1M", "3M", "1Y", "5Y"):
            self.assertIn(k, TIME_RANGE)

    def test_all_keys_v8(self):
        for k in ("1D", "1W", "1M", "3M", "1Y", "5Y"):
            self.assertIn(k, TIME_RANGE_V8)

    def test_period_two_tuple(self):
        for k, v in TIME_RANGE.items(): self.assertEqual(len(v), 2)

    def test_v8_two_tuple(self):
        for k, v in TIME_RANGE_V8.items(): self.assertEqual(len(v), 2)

    def test_1d_period_five_min(self):
        _, interval = TIME_RANGE["1D"]; self.assertEqual(interval, "5m")

    def test_1d_v8_five_min(self):
        interval, _ = TIME_RANGE_V8["1D"]; self.assertEqual(interval, "5m")

    def test_5y_weekly(self):
        _, interval = TIME_RANGE["5Y"]; self.assertEqual(interval, "1wk")


class TestQuoteParts(unittest.TestCase):
    def test_instantiate(self):
        qp = QuoteParts(price=100.0, prev_close=99.0, open=98.0, high=101.0, low=97.0, volume=500_000)
        self.assertEqual(qp.price, 100.0); self.assertEqual(qp.volume, 500_000)

    def test_change_calc(self):
        qp = QuoteParts(price=110.0, prev_close=100.0, open=100.0, high=115.0, low=99.0, volume=500_000)
        self.assertAlmostEqual(qp.price - qp.prev_close, 10.0)

    def test_all_fields(self):
        qp = QuoteParts(price=1.0, prev_close=1.0, open=1.0, high=1.0, low=1.0, volume=0)
        for f in ("price", "prev_close", "open", "high", "low", "volume"):
            self.assertIsNotNone(getattr(qp, f))


if __name__ == "__main__":
    unittest.main(verbosity=2)
