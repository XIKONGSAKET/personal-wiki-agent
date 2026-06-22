---
name: inspool
description: 将一次高价值回答或阶段性结论回填为 wiki 页面，通常优先沉淀到 inspool-wiki-zh/wiki/synthesis
---

# Skill 命令：inspool

你现在是这个 `inspool-wiki-zh/` 实验区的知识维护代理。请严格遵循 `Academic-wiki-agents-rules.md` 的规则。

本轮任务：把一次高价值回答沉淀回 wiki，而不是让它消失在聊天记录里。

适用场景：

- 一个跨多个来源的比较分析
- 一个阶段性研究结论
- 一个值得长期保存的问答总结

请按以下顺序执行：

1. 读取 `Academic-wiki-agents-rules.md`
2. 查看 `inspool-wiki-zh/wiki/index.md`
3. 判断这次内容最适合放入哪个目录，通常优先是 `inspool-wiki-zh/wiki/synthesis/`
4. 创建或更新对应页面
5. 为正文补充与现有页面的双链，关键结论优先链接到本地来源页
6. 补充或更新 frontmatter 中的 `supports`、`contradicts`、`related_*` 字段
7. 更新 `inspool-wiki-zh/wiki/index.md`
8. 在 `inspool-wiki-zh/wiki/log.md` 中追加一条 `query` 或 `refactor` 日志

写入页面时请明确区分：

- 事实依据
- 综合结论
- 推测或开放问题

如果当前内容仍然证据不足，请不要包装成“最终结论”。

不要在正文中大量堆放外部 URL；优先把证据关系落到本地 `sources` 页面。
