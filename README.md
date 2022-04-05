```
 .S_sSSs      sSSs_sSSs     .S_SsS_S.     sSSs   .S_sSSs     .S_sSSs     .S_SSSs     .S S.     sSSs   .S_sSSs
.SS~YS%%b    d%%SP~YS%%b   .SS~S*S~SS.   d%%SP  .SS~YS%%b   .SS~YS%%b   .SS~SSSSS   .SS SS.   d%%SP  .SS~YS%%b
S%S   `S%b  d%S'     `S%b  S%S `Y' S%S  d%S'    S%S   `S%b  S%S   `S%b  S%S   SSSS  S%S S%S  d%S'    S%S   `S%b
S%S    S%S  S%S       S%S  S%S     S%S  S%|     S%S    S%S  S%S    S%S  S%S    S%S  S%S S%S  S%S     S%S    S%S
S%S    S&S  S&S       S&S  S%S     S%S  S&S     S%S    d*S  S%S    d*S  S%S SSSS%S  S%S S%S  S&S     S%S    d*S
S&S    S&S  S&S       S&S  S&S     S&S  Y&Ss    S&S   .S*S  S&S   .S*S  S&S  SSS%S   SS SS   S&S_Ss  S&S   .S*S
S&S    S&S  S&S       S&S  S&S     S&S  `S&&S   S&S_sdSSS   S&S_sdSSS   S&S    S&S    S S    S&S~SP  S&S_sdSSS
S&S    S&S  S&S       S&S  S&S     S&S    `S*S  S&S~YSSY    S&S~YSY%b   S&S    S&S    SSS    S&S     S&S~YSY%b
S*S    d*S  S*b       d*S  S*S     S*S     l*S  S*S         S*S   `S%b  S*S    S&S    S*S    S*b     S*S   `S%b
S*S   .S*S  S*S.     .S*S  S*S     S*S    .S*P  S*S         S*S    S%S  S*S    S*S    S*S    S*S.    S*S    S%S
S*S_sdSSS    SSSbs_sdSSS   S*S     S*S  sSS*S   S*S         S*S    S&S  S*S    S*S    S*S     SSSbs  S*S    S&S
SSS~YSSY      YSSP~YSSY    SSS     S*S  YSS'    S*S         S*S    SSS  SSS    S*S    S*S      YSSP  S*S    SSS
                                   SP           SP          SP                 SP     SP             SP
                                   Y            Y           Y                  Y      Y              Y
```

A generic DOM-based password sprayer

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.


### Installing

First, clone the repository

```
git clone https://github.com/yok4i/domsprayer.git
```

Once inside it, run `poetry` to install the dependencies

```
poetry install
```

Alternatively, you can install them with `pip`

```
pip install -r requirements.txt
```

### Help

Use `-h` to show the help menu

```
poetry run ./domprayer.py -h

usage: domsprayer.py [-h] -t TARGET [-d {chrome,firefox}] (-u USERNAME | -U FILE) (-p PASSWORD | -P FILE)
                     [-o OUTPUT] [-r N] [-x PROXY] [--sleep SLEEP] [--wait WAIT] [--jitter JITTER]
                     --lockout LOCKOUT [--frame TYPE:VALUE] [--uf TYPE:VALUE] [--pf TYPE:VALUE]
                     [--bt TYPE:VALUE] [--slack SLACK] [-H] [-s] [--rua] [-v]

Generic DOM-based Password Sprayer.

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        Target URL (required)
  -d {chrome,firefox}, --driver {chrome,firefox}
                        Webdriver to be used (default: firefox)
  -u USERNAME, --username USERNAME
                        Single username
  -U FILE, --usernames FILE
                        File containing usernames
  -p PASSWORD, --password PASSWORD
                        Single password
  -P FILE, --passwords FILE
                        File containing passwords
  -o OUTPUT, --output OUTPUT
                        Output file (default: valid_creds.txt)
  -r N, --reset-after N
                        Reset browser after N attempts (default: 1)
  -x PROXY, --proxy PROXY
                        Proxy to pass traffic through: <scheme://ip:port>
  --sleep SLEEP         Sleep time (in seconds) between each iteration (default: 0)
  --wait WAIT           Time to wait (in seconds) when looking for DOM elements (default: 3)
  --jitter JITTER       Max jitter (in seconds) to be added to wait time (default: 0)
  --lockout LOCKOUT     Lockout policy reset time (in minutes) (required)
  --frame TYPE:VALUE    Frame containing login form in the form of TYPE:VALUE (default: None)
  --uf TYPE:VALUE       Username field in the form of TYPE:VALUE (default: ID:user_email)
  --pf TYPE:VALUE       Password field in the form of TYPE:VALUE (default: ID:user_password)
  --bt TYPE:VALUE       Submit button in the form of TYPE:VALUE (default: ID:submit-button)
  --slack SLACK         Slack webhook for sending notifications (default: None)
  -H, --headless        Run in headless mode
  -s, --shuffle         Shuffle user list
  --rua                 Use random user-agent
  -v, --verbose         Verbose output
```


## Examples

Perform password spraying using a proxy and waiting 30 minutes between each password iteration

```
poetry run ./domprayer.py -r 1 -U emails.txt -P passwords.txt --proxy 127.0.0.1:9050 --lockout 30
```

### Note

If you are using a proxy with a protocol other than HTTP, you should specify the schema like `socks5://127.0.0.1:9050`.

The options `--uf`, `--pf`, `--bt` and `--frame` must use a `TYPE` supported by Selenium.
These are attributes available for `By` class, as decribed [here](https://selenium-python.readthedocs.io/locating-elements.html).


## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/yok4i/domsprayer/tags). 


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details


## Acknowledgments

* This project was heavily inspired by [0xZDH/msspray](https://github.com/0xZDH/msspray)


## Disclaimer

This tool is intended for educational purpose or for use in environments where you have been given explicit/legal authorization to do so.
