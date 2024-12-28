[English](./README.md) | [中文](./README_CN.md)
# AI Commit (aicmt)

An AI-powered Git commit assistant that not only generates commit messages, but also automatically analyzes and splits your code changes into multiple well-organized commits following best practices.

[![aicmt](https://asciinema.org/a/695352.svg)](https://asciinema.org/a/695352/?autoplay=1)

## Features

- **Intelligent Change Splitting**: Unlike traditional commit message generators, aicmt analyzes your code changes and automatically splits them into logical, focused commits following Git best practices
- **Flexible Control**: You can let AI decide the optimal number of commits, or specify exactly how many commits you want
- **Focus on Coding**: Make all your changes freely, and let AI handle the commit organization - no need to worry about making perfect atomic commits while coding

## Installation

Use pip to install (Python >=3.10)

```bash
pip install aicmt
```
or use brew to install
```bash
brew install versun/tap/aicmt
```

## Quick Start 


1. Create configuration file `.aicmtrc`

Reference the template file [`.aicmtrc.template`](./.aicmtrc.template) and create `.aicmtrc` in your home directory.
```bash
cp .aicmtrc.template ~/.config/aicmt/.aicmtrc
```
You can also create `.aicmtrc` in the current directory, which will override the global configuration file (~/.config/aicmt/.aicmtrc)
```bash
cd /path/to/git/repo
touch .aicmtrc
```

2. Add OpenAI API and other information in the configuration file.

3. Enter your git repository directory and run the `aicmt` command to automatically analyze changes and generate commit messages.

## Help
```bash
$ aicmt -h
usage: aicmt [-h] [-v] [-n N]

<<< AICMT (AI Commit) - AI-powered Git commit assistant >>>

options:
  -h, --help           show this help message and exit
  -v, --version        show program's version number and exit
  -n, --num-commits N  Number of commits to generate (default: AI decides)
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/versun/aicmt.git
```

2. Install dependencies:
```bash
cd aicmt
pip install -e ".[dev]"
```

## Having Issues?
All code in this project is AI-generated, so if you encounter any problems, please first try asking AI for solutions (preferably using the claude-3.5-sonnet model). 
If the issue persists, please submit an issue, and I will consult AI to resolve it.

## Contributing

Pull requests are welcome!
Please submit an issue before submitting a pull request, to avoid duplicate submissions.

## A Big Thank You to My Sponsors
I am deeply grateful to my amazing supporters and sponsors who have made my open source journey possible.   
<p align="center">
  <a href="https://github.com/versun/sponsors/">
    <img src='https://raw.githubusercontent.com/versun/sponsors/main/sponsors.svg'/>
  </a>
</p>

Become a Sponser on [Github](https://github.com/sponsors/versun) / [爱发电](https://afdian.com/@versun) / [微信](https://github.com/versun/sponsors/blob/b11431cb1302a4605f8e92447aaa061cbe704b68/wechat.jpg)

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=versun/aicmt&type=Date)](https://star-history.com/#versun/aicmt&Date)