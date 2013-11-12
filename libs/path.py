import base64
import os.path


def uploadPath(service, url, browser, build, filename):
    encUrl = base64.b64encode(url)
    return os.path.join(service, encUrl, browser, build, filename)
