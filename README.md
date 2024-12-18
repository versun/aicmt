[English](./README.md) | [中文](./README_CN.md)
# AI Commit (aicmt)

An intelligent Git commit assistant that not only generates commit messages, but also automatically analyzes and splits your code changes into multiple well-organized commits following best practices.

## Features

- **Intelligent Change Splitting**: Unlike traditional commit message generators, aicmt analyzes your code changes and automatically splits them into logical, focused commits following Git best practices
- **Flexible Control**: You can let AI decide the optimal number of commits, or specify exactly how many commits you want
- **Focus on Coding**: Make all your changes freely, and let AI handle the commit organization - no need to worry about making perfect atomic commits while coding

## Installation

Requires Python 3.10 or higher.

```bash
pip install aicmt
```

## Quick Start (Command Line Arguments Mode)

In your git repository directory, run:
```bash
aicmt --api-key <API_KEY> --model <MODEL> --base-url <OPENAI_BASE_URL>
```

To specify the number of commits to generate(default: AI decides):
```bash
aicmt --api-key <API_KEY> --model <MODEL> -n 3  # Split changes into 3 commits
```

## Help
```bash
$ aicmt -h
usage: aicmt [-h] [-v] [--api-key KEY] [--base-url URL] [--model MODEL] [-n N]

<<< AICMT (AI Commit) - AI-powered Git commit assistant >>>

options:
  -h, --help           show this help message and exit
  -v, --version        show program's version number and exit
  --api-key KEY        OpenAI API key for authentication
  --base-url URL       Custom API base URL (default: https://api.openai.com/v1)
  --model MODEL        AI model to use (default: gpt-4o-mini)
  -n, --num-commits N  Number of commits to generate (default: AI decides)
```

## Configuration File Mode

1. Create configuration file `.aicmtrc`

Reference the template file [`.aicmtrc.template`](./.aicmtrc.template)` and create `.aicmtrc` in your home directory.
```bash
cp .aicmtrc.template ~/.aicmtrc
```
You can also create `.aicmtrc` in the current directory, which will override the global configuration file (~/.aicmtrc)
```bash
cd /path/to/git/repo
touch .aicmtrc
```

2. Add OpenAI API and other information in the configuration file.

3. Enter your git repository directory and run the `aicmt` command to automatically analyze changes and generate commit messages.

## Development

1. Clone the repository:
```bash
git clone https://github.com/versun/aicmt.git
```

2. Install dependencies:
```bash
cd aicmt
pip install ".[dev]"
```

## Having Issues?
All code in this project is AI-generated, so if you encounter any problems, please first try asking AI for solutions (preferably using the claude-3.5-sonnet model). 
If the issue persists, please submit an issue, and I will consult AI to resolve it.

## Contributing

Pull requests are welcome!
