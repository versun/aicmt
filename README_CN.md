[English](./README.md) | [中文](./README_CN.md)
# AI Commit (aicmt)

一个智能的Git提交助手，不仅能生成提交信息，还能自动分析并将您的代码变更按最佳实践拆分为多个结构良好的提交。

## 功能特点

- **智能变更拆分**：不同于传统的提交信息生成器，aicmt能分析您的代码变更，并按照Git最佳实践自动拆分为多个逻辑清晰的提交
- **灵活控制**：您可以让AI决定最佳的提交数量，也可以精确指定想要的提交数量
- **专注编码**：自由地进行所有代码修改，将提交组织工作交给AI处理 - 在编码时无需担心如何完美地进行原子提交

## 安装

要求Python 3.10或更高版本。

```bash
pip install aicmt
```

## 快速开始（命令行参数模式）

在git仓库目录下，执行：
```bash
aicmt --api-key <API_KEY> --model <MODEL> --base-url <OPENAI_BASE_URL>
```

指定生成的提交数量（默认AI决定）：
```bash
aicmt --api-key <API_KEY> --model <MODEL> -n 3  # 将变更拆分为3个提交
```

## 帮助：
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

## 配置文件模式

1. 创建配置文件`.aicmtrc`

参考模板文件[`.aicmtrc.template`](./.aicmtrc.template)，并在用户目录下创建`.aicmtrc`文件。
```bash
cp .aicmtrc.template ～/.aicmtrc
```
也可在当前目录下创建`.aicmtrc`文件，将会覆盖全局的配置文件(~/.aicmtrc)
```bash
cd /path/to/git/repo
touch .aicmtrc
```

2. 在配置文件中添加OpenAI API等信息：

3. 进入git仓库目录内，执行`aicmt`命令，即可自动分析变更并生成提交信息。


## 开发

1. 克隆仓库：
```bash
git clone https://github.com/versun/aicmt.git
```

2. 安装依赖：
```bash
cd aicmt
pip install ".[dev]"
```

## 遇到问题？
本项目代码均有AI生成，所以如果遇到问题请首先自行询问AI尝试解决(最好是claude-3.5-sonnet模型)，如果还是无法解决，请提交issue，由我来询问AI解决。

## 贡献

欢迎提交拉取请求！