import unittest

from pipeline.assess.scale import classify_volume


class TestVolumeScale(unittest.TestCase):

    def test_matai_an_estimate_and_official_same_scale(self):
        # 估 12,716、官方 9,100，誤差近 40%，但級距一樣
        self.assertEqual(classify_volume(12716).scale, "極大型")
        self.assertEqual(classify_volume(9100, rel_error=0.0).scale, "極大型")

    def test_range_crossing_boundary(self):
        c = classify_volume(4000)          # 2,400～5,600
        self.assertEqual(c.scale, "大型～極大型")

    def test_tiny_and_small_share_label(self):
        self.assertEqual(classify_volume(9, rel_error=0.5).scale, "小型")

    def test_confidence_follows_detection_grade(self):
        self.assertEqual(classify_volume(12716, detection_grade="A").confidence, "高")
        self.assertEqual(classify_volume(12716, detection_grade="B").confidence, "中")
        self.assertEqual(classify_volume(12716, detection_grade="C").confidence, "低")
        self.assertEqual(classify_volume(12716).confidence, "中")

    def test_crossing_lowers_confidence(self):
        self.assertEqual(classify_volume(4000, detection_grade="A").confidence, "中")
        self.assertEqual(classify_volume(4000, detection_grade="C").confidence, "低")

    def test_bad_curve_is_low(self):
        self.assertEqual(classify_volume(12716, detection_grade="A", curve_ok=False).confidence, "低")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            classify_volume(0)
        with self.assertRaises(ValueError):
            classify_volume(100, rel_error=1.5)

    def test_to_dict(self):
        d = classify_volume(12716).to_dict()
        self.assertEqual(d["rangeWanM3"], [7630, 17802])
        self.assertEqual(d["scale"], "極大型")
