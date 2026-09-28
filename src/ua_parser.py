import re

HTTP_CLIENT_RE = re.compile(r'^(curl|python-requests|python-urllib3|Scrapy|node-fetch|Go-http-client)/', re.I)
APP_RE = re.compile(r'^Avito/(\d+)[\d.]* \((?:Android (\d+); ([^)]+)|iPhone; iOS (\d+)\.\d+;[^)]*)\)')
BROWSERS = [ 
    ('yabrowser',       r'YaBrowser/(\d+\.\d+)'),
    ('headless_chrome', r'HeadlessChrome/(\d+)'),
    ('firefox',         r'Firefox/(\d+)'),
    ('chrome',          r'Chrome/(\d+)'),
    ('safari',          r'Version/(\d+)'),
]

def parse_ua(ua: str) -> dict:
    r = dict(ua_kind='other', ua_os='other', ua_os_ver=None, ua_browser='other',
             ua_browser_ver=None, ua_engine_ver=None, ua_device='none')
    if m := HTTP_CLIENT_RE.match(ua):
        r.update(ua_kind='http_client', ua_browser=m.group(1).lower())
        return r
    if m := APP_RE.match(ua):
        r.update(ua_kind='app', ua_browser='avito_app', ua_browser_ver=m.group(1))
        if m.group(2):
            r.update(ua_os='android', ua_os_ver=float(m.group(2)), ua_device=m.group(3))
        else:
            r.update(ua_os='ios', ua_os_ver=float(m.group(4)), ua_device='iPhone')
        return r
    if m := re.search(r'Android (\d+); ([^)]+)\)', ua):
        r.update(ua_kind='mobile_browser', ua_os='android', ua_os_ver=float(m.group(1)), ua_device=m.group(2))
    elif m := re.search(r'iPhone OS (\d+)_', ua):
        r.update(ua_kind='mobile_browser', ua_os='ios', ua_os_ver=float(m.group(1)), ua_device='iPhone')
    else:
        r['ua_kind'] = 'desktop_browser'
        r['ua_os'] = ('windows' if 'Windows' in ua else 'mac' if 'Macintosh' in ua
                      else 'linux' if 'Linux' in ua else 'other')
    for name, pat in BROWSERS:
        if m := re.search(pat, ua):
            r.update(ua_browser=name, ua_browser_ver=m.group(1))
            break
    if m := re.search(r'(?:Chrome|Firefox)/(\d+)', ua):
        r['ua_engine_ver'] = int(m.group(1))
    return r