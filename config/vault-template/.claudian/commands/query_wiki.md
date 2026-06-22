---
name: query_wiki
description: 基于 inspool-wiki-zh/wiki 现有页面回答问题，优先引用本地来源页，而不是直接回 raw 或外部链接做一次性总结
---

# Skill 命令：query_wiki

请严格遵循 `Academic-wiki-agents-rules.md` 的规则。

本轮任务：基于已有 wiki 回答问题，而不是直接跳过 wiki 去做一次性摘要。

请按以下顺序执行：

1. 读取 `Academic-wiki-agents-rules.md`
2. 优先查看 `inspool-wiki-zh/wiki/index.md`
3. 根据问题定位相关页面
4. 读取必要的来源页、实体页、概念页、综合页
5. 基于已有 wiki 做综合回答
6. 对关键判断优先给出本地来源页引用；如果可以，优先引用到具体小节，例如 `[[sources/某篇来源#关键观点]]`

如果本次回答产生了长期有价值的结论，例如：

- 一个明确的对比分析
- 一个稳定的主题综述
- 一个跨多个来源的综合判断

则请额外建议是否把结果沉淀到 `inspool-wiki-zh/wiki/synthesis/` 中。

回答时请区分：

- 已有事实
- 当前综合判断
- 仍待确认的问题

不要把没有来源支撑的内容说成确定事实。

不要优先引用外部 URL，除非当前 wiki 还没有对应的本地来源页。
