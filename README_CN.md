[English](./README.md) | [中文](./README_CN.md)
# AI Commit (aicmt)

一个AI驱动的Git提交助手，不仅能自动生成提交信息，还能自动分析代码变更，并根据最佳实践将其拆分为多个结构良好的提交。

[![aicmt](https://asciinema.org/a/695352.svg)](https://asciinema.org/a/695352/?autoplay=1)

## 功能特点

- **智能变更拆分**：不同于传统的提交信息生成器，aicmt能分析您的代码变更，并按照Git最佳实践自动拆分为多个逻辑清晰的提交
- **灵活控制**：您可以让AI决定最佳的提交数量，也可以精确指定想要的提交数量
- **专注编码**：自由地进行所有代码修改，将提交组织工作交给AI处理 - 在编码时无需担心如何完美地进行原子提交

## 安装

使用pip安装(Python >=3.10)

```bash
pip install aicmt
```
或者使用brew安装
```bash
brew install versun/tap/aicmt
```

## 快速开始

1. 创建配置文件`.aicmtrc`

参考模板文件[`.aicmtrc.template`](./.aicmtrc.template),并在用户目录下创建`.aicmtrc`文件。
```bash
cp .aicmtrc.template ~/.config/aicmt/.aicmtrc
```
也可在当前目录下创建`.aicmtrc`文件，将会覆盖全局的配置文件(~/.config/aicmt/.aicmtrc)
```bash
cd /path/to/git/repo
touch .aicmtrc
```

2. 在配置文件中添加OpenAI API等信息，并保存。

3. 进入git仓库目录内，执行`aicmt`命令，即可自动分析变更并生成提交信息。

## 帮助：
```bash
$ aicmt -h
usage: aicmt [-h] [-v] [-n N]

<<< AICMT (AI Commit) - AI-powered Git commit assistant >>>

options:
  -h, --help           show this help message and exit
  -v, --version        show program's version number and exit
  -n, --num-commits N  Number of commits to generate (default: AI decides)
```

## 开发

1. 克隆仓库：
```bash
git clone https://github.com/versun/aicmt.git
```

2. 安装依赖：
```bash
cd aicmt
pip install -e ".[dev]"
```

## 遇到问题？
本项目代码均有AI生成，所以如果遇到问题请首先自行询问AI尝试解决(最好是claude-3.5-sonnet模型)，如果还是无法解决，请提交issue，由我来询问AI解决。

## 贡献

欢迎提交拉取请求！
请在提交PR前先提交issue，避免重复提交。

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