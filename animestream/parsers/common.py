from selenium import webdriver

_driver = None


def driver():
    global _driver
    if _driver is not None:
        return _driver

    import chromedriver_autoinstaller

    chromedriver_autoinstaller.install()

    op = webdriver.ChromeOptions()
    op.headless = True
    _driver = webdriver.Chrome(options=op)
    return _driver
