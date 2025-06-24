from urllib.parse import urlparse, urlencode
import ipaddress
import re
import os

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "./XGBoostClassifier.pickle.dat")


def havingIP(url):
    try:
        ipaddress.ip_address(url)
        ip = 1
    except:
        ip = 0
    return ip


def haveAtSign(url):
    if "@" in url:
        at = 1
    else:
        at = 0
    return at


def getLength(url):
    if len(url) < 54:
        length = 0
    else:
        length = 1
    return length


def getDepth(url):
    s = urlparse(url).path.split("/")
    depth = 0
    for j in range(len(s)):
        if len(s[j]) != 0:
            depth = depth + 1
    return depth


def redirection(url):
    pos = url.rfind("//")
    if pos > 6:
        if pos > 7:
            return 1
        else:
            return 0
    else:
        return 0


def httpDomain(url):
    domain = urlparse(url).netloc
    if "https" in domain:
        return 1
    else:
        return 0


shortening_services = (
    r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|"
    r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|"
    r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|"
    r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|"
    r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|"
    r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|"
    r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|"
    r"tr\.im|link\.zip\.net"
)


def tinyURL(url):
    match = re.search(shortening_services, url)
    if match:
        return 1
    else:
        return 0


def prefixSuffix(url):
    if "-" in urlparse(url).netloc:
        return 1  # phishing
    else:
        return 0  # legitimate


import re
from bs4 import BeautifulSoup
import whois
import urllib
import urllib.request
from datetime import datetime


def web_traffic(url):
    try:
        url = urllib.parse.quote(url)
        rank = BeautifulSoup(
            urllib.request.urlopen(
                "http://data.alexa.com/data?cli=10&dat=s&url=" + url
            ).read(),
            "xml",
        ).find("REACH")["RANK"]
        rank = int(rank)
    except TypeError:
        return 1
    if rank < 100000:
        return 1
    else:
        return 0


def domainAge(domain_name):
    creation_date = domain_name.creation_date
    expiration_date = domain_name.expiration_date

    if isinstance(creation_date, list):
        creation_date = creation_date[0]
    if isinstance(expiration_date, list):
        expiration_date = expiration_date[0]

    if hasattr(creation_date, "replace"):
        creation_date = creation_date.replace(tzinfo=None)
    if hasattr(expiration_date, "replace"):
        expiration_date = expiration_date.replace(tzinfo=None)

    if (expiration_date is None) or (creation_date is None):
        return 1

    ageofdomain = abs((expiration_date - creation_date).days)
    if (ageofdomain / 30) < 6:
        return 1
    else:
        return 0


def domainEnd(domain_name):
    expiration_date = domain_name.expiration_date
    if isinstance(expiration_date, str):
        try:
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        except:
            return 1
    if expiration_date is None:
        return 1
    elif type(expiration_date) is list:
        return 1
    else:
        today = datetime.now()
        end = abs((expiration_date - today).days)
        if (end / 30) < 6:
            end = 0
        else:
            end = 1
    return end


import requests


def iframe(response):
    if response == "":
        return 1
    else:
        if re.findall(r"[<iframe>|<frameBorder>]", response.text):
            return 0
        else:
            return 1


def mouseOver(response):
    if response == "":
        return 1
    else:
        if re.findall("<script>.+onmouseover.+</script>", response.text):
            return 1
        else:
            return 0


def rightClick(response):
    if response == "":
        return 1
    else:
        if re.findall(r"event.button ?== ?2", response.text):
            return 0
        else:
            return 1


def forwarding(response):
    if response == "":
        return 1
    else:
        if len(response.history) <= 2:
            return 0
        else:
            return 1


def featureExtraction(url):

    features = []
    features.append(havingIP(url))
    features.append(haveAtSign(url))
    features.append(getLength(url))
    features.append(getDepth(url))
    features.append(redirection(url))
    features.append(httpDomain(url))
    features.append(tinyURL(url))
    features.append(prefixSuffix(url))

    dns = 0
    try:
        domain_name = whois.whois(urlparse(url).netloc)
        print("ok")
    except:
        dns = 1
        print("sry")

    features.append(dns)
    features.append(1 if dns == 1 else domainAge(domain_name))
    features.append(1 if dns == 1 else domainEnd(domain_name))

    try:
        response = requests.get(url)
    except:
        response = ""

    features.append(iframe(response))
    features.append(mouseOver(response))
    features.append(rightClick(response))
    features.append(forwarding(response))

    return features


feature_names = [
    "Domain",
    "Have_IP",
    "Have_At",
    "URL_Length",
    "URL_Depth",
    "Redirection",
    "https_Domain",
    "TinyURL",
    "Prefix/Suffix",
    "DNS_Record",
    "Domain_Age",
    "Domain_End",
    "iFrame",
    "Mouse_Over",
    "Right_Click",
    "Web_Forwards",
    "Label",
]

import concurrent.futures
import pickle


def feature_extraction_with_timeout(url, timeout=30):
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(featureExtraction, url)
            return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        print(f"Feature extraction for URL '{url}' timed out.")
        return None


def detect_0(urls, timeout=30):
    features = []
    timeout_positions = []

    for idx, url in enumerate(urls):
        extracted_feature = feature_extraction_with_timeout(url, timeout=timeout)
        if extracted_feature is not None:
            features.append(extracted_feature)
        else:
            timeout_positions.append(idx)

    if features:
        loaded_model = pickle.load(open(_MODEL_PATH, "rb"))
        predictions = list(loaded_model.predict(features))
    else:
        predictions = []

    for pos in timeout_positions:
        predictions.insert(pos, -1)

    return predictions
