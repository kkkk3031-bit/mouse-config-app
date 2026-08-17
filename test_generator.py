import unittest
from generator import generate_lua, validate


class TestGenerator(unittest.TestCase):
    def test_remap(self):
        cfg = [{"button": 4, "type": "remap", "keys": ["lctrl", "c"]}]
        lua = generate_lua(cfg)
        self.assertIn("arg == 4", lua)
        self.assertIn('PressKey("lctrl")', lua)
        self.assertIn('PressKey("c")', lua)
        self.assertIn('ReleaseKey("c")', lua)
        self.assertIn('ReleaseKey("lctrl")', lua)

    def test_text(self):
        cfg = [{"button": 5, "type": "text", "text": 'say "hi"'}]
        lua = generate_lua(cfg)
        self.assertIn('local text = "say \\"hi\\""', lua)
        self.assertIn("PressAndReleaseKey(c)", lua)

    def test_combo(self):
        cfg = [{"button": 6, "type": "combo", "steps": [{"key": "b"}, {"delay_ms": 150}, {"key": "1"}]}]
        lua = generate_lua(cfg)
        self.assertIn('PressAndReleaseKey("b")', lua)
        self.assertIn("Sleep(150)", lua)
        self.assertIn('PressAndReleaseKey("1")', lua)

    def test_toggle(self):
        cfg = [{"button": 7, "type": "toggle", "key": "f", "interval_ms": 500}]
        lua = generate_lua(cfg)
        self.assertIn("repeating[7]", lua)
        self.assertIn("Sleep(500)", lua)
        self.assertIn("IsMouseButtonPressed(7)", lua)

    def test_multiple_buttons_combined(self):
        cfg = [
            {"button": 4, "type": "remap", "keys": ["a"]},
            {"button": 5, "type": "text", "text": "hi"},
        ]
        lua = generate_lua(cfg)
        self.assertIn("arg == 4", lua)
        self.assertIn("arg == 5", lua)

    def test_invalid_button_number(self):
        with self.assertRaises(ValueError):
            validate({"button": "x", "type": "remap", "keys": ["a"]})

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            validate({"button": 4, "type": "bogus"})

    def test_remap_needs_keys(self):
        with self.assertRaises(ValueError):
            validate({"button": 4, "type": "remap", "keys": []})

    def test_text_needs_text(self):
        with self.assertRaises(ValueError):
            validate({"button": 4, "type": "text", "text": ""})

    def test_combo_needs_steps(self):
        with self.assertRaises(ValueError):
            validate({"button": 4, "type": "combo", "steps": []})

    def test_toggle_needs_key(self):
        with self.assertRaises(ValueError):
            validate({"button": 4, "type": "toggle", "key": "", "interval_ms": 500})

    def test_lua_syntax_balanced(self):
        cfg = [
            {"button": 4, "type": "remap", "keys": ["lctrl", "c"]},
            {"button": 5, "type": "text", "text": "hi"},
            {"button": 6, "type": "combo", "steps": [{"key": "b"}, {"delay_ms": 150}]},
            {"button": 7, "type": "toggle", "key": "f", "interval_ms": 500},
        ]
        lua = generate_lua(cfg)
        opens = lua.count("function") + lua.count(" if ") + lua.count(" while ") + lua.count(" for ")
        ends = lua.count(" end") + lua.count("\nend")
        self.assertEqual(opens, ends)


if __name__ == "__main__":
    unittest.main()
