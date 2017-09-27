from nh.core import module_loader

def test_loading():
    mod = module_loader.load_module("logging.config")
    mod = module_loader.load_module("time")
    obj = module_loader.load_object("curses.textpad.Textbox")
    assert obj.__name__ == "Textbox"
