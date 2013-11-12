import os
import re
import tempfile
import selenium
import libs.path
from selenium import webdriver
from cPickle import loads, dumps
from xmlrpclib import ServerProxy, Binary
from StringIO import StringIO
from PIL import Image, ImageDraw, ImageChops, ImageEnhance, ImageStat


debugIds = ("__debug__",)
removeDebug = """var node = document.getElementById("%s");
if (node.parentNode) {
node.parentNode.removeChild(node);
}"""
uploadUrl = "http://storage.qak:3642/RPC2"
test_id_regexp = re.compile(r"\w+")


def get_test_id(service, test_name, step):
    if test_id_regexp.match(service) and test_id_regexp.match(test_name) and \
            test_id_regexp.match(step):
        return os.path.join(service, test_name, step)
    else:
        raise ValueError("get_test_id has to be \w+")


def _load(self, testId, browser):
    ret = self.proxy.remoteFile.read(libs.path.uploadPath(testId, browser,
                                                          "original",
                                                          "original.png"))
    buff = StringIO(ret["data"])
    self.im1 = Image.open(buff)


def _erase(self):
    for ad in self.ads1:
        d = ImageDraw.Draw(self.im1)
        d.rectangle(ad["location"] + ad["size"], fill="lightgray")
    for ad in self.ads2:
        d = ImageDraw.Draw(self.im2)
        d.rectangle(ad["location"] + ad["size"], fill="lightgray")


def _diff(self):
    diff = ImageChops.difference(self.im1, self.im2)
    stat = ImageStat.Stat(diff)
    print "RMS: %s" % stat.rms
    if stat.rms[0] < self.rmsLimit:
        return 0
    else:
        return 1


def shot(webdriver, browser, testId, buildId):
    proxy = ServerProxy(uploadUrl)
    webdriver.set_window_size(1024, 800)

    ret = proxy.remoteFile.read(libs.path.uploadPath(testId, browser,
                                                     "original",
                                                     "ads.pickle"))
    if ret["status"] == 200:
        originExists = True
    else:
        originExists = False

    if not originExists:
        ads1 = loads(ret["data"].data)
        if ads1:
            sizeJs = "elm=document.getElementById(\"%s\");\
                      elm.style.display=\"block\";\
                      elm.style.width=\"%s px\";elm.style.height=\"%s px\";\
                      elm.style.overflow=\"hidden\";"
            for ad in ads1:
                elm = webdriver.find_element_by_id(ad["id"])
                if ad["size"] != (elm.size["width"], elm.size["height"]):
                    webdriver.execute_script(sizeJs % (ad["id"], ad["size"][0],
                                                       ad["size"][1]))

    try:
        ads2 = webdriver.execute_script("return pozice;")
    except selenium.common.exceptions.WebDriverException:
        ads2 = []
    for ad in ads2:
        elm = webdriver.find_element_by_id(ad["id"])
        ad["size"] = elm.size["width"], elm.size["height"]
        ad["location"] = elm.location["x"], elm.location["y"]
    for dId in debugIds:
        webdriver.execute_script(removeDebug % dId)

    _, filename = tempfile.mkstemp()
    webdriver.save_screenshot(filename)
    data = open(filename).read()
    os.remove(filename)
    adsPickled = dumps(ads2)
    if originExists:
        proxy.remoteFile.write(libs.path.uploadPath(testId, browser, buildId,
                                                    "build.png"),
                               Binary(data), False)
        proxy.remoteFile.write(libs.path.uploadPath(testId, browser, buildId,
                                                    "ads.pickle"),
                               Binary(adsPickled), False)
    else:
        proxy.remoteFile.write(libs.path.uploadPath(testId, browser,
                                                    "original",
                                                    "original.png"),
                               Binary(data), False)
        proxy.remoteFile.write(libs.path.uploadPath(testId, browser,
                                                    "original",
                                                    "ads.pickle"),
                               Binary(adsPickled), False)
