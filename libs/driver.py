import os
import selenium
import tempfile
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType


proxy = Proxy({'proxyType': ProxyType.AUTODETECT, 'autodetect': True})
hubUrl = "http://webdriver.qak:4444/wd/hub"

debugIds = ("__debug__", )
removeDebug = """var node = document.getElementById("%s");
if (node.parentNode) {
node.parentNode.removeChild(node);
}"""


def shot(cap, url, ads=None):
    webdriver = webdriver.Remote(hubUrl,
                            desired_capabilities=cap,
                            proxy=proxy)
    webdriver.set_window_size(1024, 800)
    webdriver.get(url)
    if ads:
        sizeJs = "elm=document.getElementById(\"%s\");\
                  elm.style.display=\"block\";elm.style.width=\"%s px\";\
                  elm.style.height=\"%s px\";elm.style.overflow=\"hidden\";"
        for ad in ads:
            elm = webdriver.find_element_by_id(ad["id"])
            if ad["size"] != (elm.size["width"], elm.size["height"]):
                webdriver.execute_script(sizeJs % (ad["id"], ad["size"][0],
                                         ad["size"][1]))

    try:
        ads = webdriver.execute_script("return pozice;")
    except selenium.common.exceptions.WebDriverException:
        ads = []
    for ad in ads:
        elm = webdriver.find_element_by_id(ad["id"])
        ad["size"] = elm.size["width"], elm.size["height"]
        ad["location"] = elm.location["x"], elm.location["y"]
    for dId in debugIds:
        webdriver.execute_script(removeDebug % dId)

    _, filename = tempfile.mkstemp()
    webdriver.save_screenshot(filename)
    data = open(filename).read()
    os.remove(filename)
    return data, ads
