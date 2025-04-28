# MRobot

更加高效快捷的 STM32 开发架构，诞生于 Robocon 和 Robomaster，但绝不仅限于此。

<div align="center">
  <img src="./image/MRobot.jpeg" height="100" alt="MRobot Logo">
  <p>是时候使用更简洁的方式开发单片机了</p>
  <p>
    <!-- <img src="https://img.shields.io/github/license/xrobot-org/XRobot.svg" alt="License">
    <img src="https://img.shields.io/github/repo-size/xrobot-org/XRobot.svg" alt="Repo Size">
    <img src="https://img.shields.io/github/last-commit/xrobot-org/XRobot.svg" alt="Last Commit">
    <img src="https://img.shields.io/badge/language-c/c++-F34B7D.svg" alt="Language"> -->
  </p>
</div>

---

## 引言

提起嵌入式开发，绝大多数人对每次繁琐的配置，以及查阅各种文档来写东西感到非常枯燥和浪费使时间，对于小形形目创建优雅的架构又比较费事，那么我们哟u没有办法快速完成基础环境的搭建后直接开始写逻辑代码呢？

这就是**MRobot**。



---

## 获取源代码

（此处可补充获取代码的具体方法）

---

## 主要特色

（此处可补充项目的主要特色）

---

## 组成

<div align="center">
  <img src="./image/嵌入式程序层次图.png" alt="嵌入式程序层次图">
</div>

- `src/bsp`
- `src/component`
- `src/device`
- `src/module`
- `src/task`

---

## 应用案例

> **Robomaster**

- 全向轮步兵
- 英雄
- 哨兵

---

## 机器人展示

`以上机器人均使用 MRobot 搭建`

---

## 硬件支持

（此处可补充支持的硬件列表）

---

## 图片展示


## 相关依赖

（此处可补充项目依赖的具体内容）

---

## 构建 exe

使用以下命令构建可执行文件：

```bash
pyinstaller --onefile --windowed 