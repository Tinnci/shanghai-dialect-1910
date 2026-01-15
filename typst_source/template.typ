// template.typ - 核心模板

// 移除 import，我们使用自定义实现来彻底解决依赖问题
// #import "@preview/rubby:0.10.2": get-ruby

// ============================================================
// 1. 自定义 Ruby 实现 (Reflowable & Robust)
// ============================================================

#let r(roman, hanzi) = {
  // 简单的内联 Ruby 实现
  // box 确保是内联元素，stack 垂直堆叠
  box(baseline: 50%, stack(
    dir: ttb,
    spacing: 1pt,
    align(center, text[#hanzi]), // 汉字在上
    align(center, text(size: 0.55em)[#roman]), // 拼音在下
  ))
}

// 紧凑模式
#let rc = r

// ============================================================
// 2. 课文标题宏 (带自动编号和目录链接)
// ============================================================

#let exercise(num, zh_title, ro_title) = {
  // 1. 创建元数据标签供索引跳转使用
  [#metadata((type: "exercise", num: num, zh: zh_title, ro: ro_title)) <exercise>]

  // 2. 每课重置脚注计数器
  counter(footnote).update(0)

  // 3. 课与课之间的间距
  v(1.5em, weak: true)

  // 4. 标题可视区块（含字重与字距优化）
  block(breakable: false)[
    #align(center)[
      // 全大写 EXERCISE: 增加正追踪 (0.08em) 提升可读性
      #text(size: 10pt, weight: "semibold", tracking: 0.08em)[
        EXERCISE NO. #num
      ]
      #v(0.3em)
      // 中文标题: 使用 semibold + 微小负追踪
      #text(size: 14pt, weight: "semibold", tracking: -0.01em)[#zh_title] #label("ex-" + str(num))
      #v(0.2em)
      // 罗马字标题: 保持斜体 + 轻微正追踪
      #text(size: 9pt, style: "italic", tracking: 0.02em)[#ro_title]
    ]
  ]

  v(0.5em)
}

// ============================================================
// 3. 辅助组件
// ============================================================

#let pron-entry(roman, description) = {
  grid(
    columns: (3cm, 1fr),
    gutter: 1em,
    text(weight: "bold", font: "Libertinus Serif")[#roman], text[#description],
  )
  v(0.3em)
}

#let vocab(zh, ro, en) = {
  grid(
    columns: (2cm, 4cm, 1fr),
    gutter: 0.5em,
    text(weight: "bold")[#zh], text(style: "italic")[#ro], text[#en],
  )
}

// ============================================================
// 4. 自定义目录生成 (包含课文列表) - 使用新的 context API
// ============================================================

#let exercise-outline() = {
  // 使用新的 context 语法 (Typst 0.11+)
  context {
    let exercises = query(<exercise>)

    // 分组显示 (每10课一组)
    let groups = (
      (1, 10, "Lessons 1–10"),
      (11, 20, "Lessons 11–20"),
      (21, 30, "Lessons 21–30"),
      (31, 40, "Lessons 31–40"),
      (41, 50, "Lessons 41–50"),
      (51, 60, "Lessons 51–60"),
      (61, 70, "Lessons 61–70"),
      (71, 80, "Lessons 71–80"),
      (81, 90, "Lessons 81–90"),
      (91, 100, "Lessons 91–100"),
      (101, 110, "Lessons 101–110"),
      (111, 120, "Lessons 111–120"),
      (121, 130, "Lessons 121–130"),
      (131, 140, "Lessons 131–140"),
      (141, 150, "Lessons 141–150"),
      (151, 155, "Lessons 151–155"),
    )

    for (start, end, label) in groups {
      text(weight: "bold", size: 9pt)[#label]
      v(0.3em)

      for ex in exercises {
        let data = ex.value
        if data.num >= start and data.num <= end {
          let page-num = counter(page).at(ex.location()).first()
          grid(
            columns: (auto, 1fr, auto),
            gutter: 0.3em,
            link(ex.location())[#data.num. #data.zh], box(width: 1fr, repeat[.]), link(ex.location())[#page-num],
          )
          v(0.15em)
        }
      }
      v(0.5em)
    }
  }
}

// ============================================================
// 5. 全局页面配置
// ============================================================

#let project(body) = {
  set document(
    title: "Shanghai Dialect Exercises (1910) - 数字化版",
    author: "J. H. Pott / 数字化整理: Tinnci",
  )
  set page(
    paper: "a5",
    margin: (inside: 2.2cm, outside: 1.8cm, top: 2cm, bottom: 2cm),
    numbering: "1",
    number-align: center,
  )

  // ============================================================
  // 文本设置 (含微排版优化)
  // ============================================================

  set text(
    font: ("Noto Serif CJK SC", "Libertinus Serif"),
    size: 10.5pt,
    lang: "zh",
    // 微排版: 启用悬挂标点 (Typst 0.11+)
    overhang: true,
    // 微排版: 启用字距对 (Kerning)
    kerning: true,
    // 微排版: 轻微字距追踪增强可读性
    tracking: 0.02em,
  )

  // ============================================================
  // 段落设置 (含两端对齐优化)
  // ============================================================

  set par(
    leading: 1.3em,
    justify: true,
    first-line-indent: 0em,
    // 允许略微调整行间距以优化排版
    linebreaks: "optimized",
  )

  set footnote(
    numbering: n => [(#n)],
    // split: true // Typst 0.11+ 默认支持跨页，显式属性可能暂不支持或名称不同
  )
  set footnote.entry(
    // 最佳实践：使用全宽分割线以清晰区分跨页脚注 (Best Practice: Full-width separator)
    separator: line(length: 100%, stroke: 0.5pt + gray),
    indent: 0em,
    gap: 0.5em,
  )

  // ============================================================
  // 标题样式 (含字重与字距优化)
  // ============================================================

  set heading(numbering: none)

  // Level 1 章节标题:
  // - 使用 semibold(600) 代替 bold(700) 减少"黑块"感
  // - 负追踪 (-0.02em) 让大标题更紧凑有张力
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(2em)
    align(center, text(
      size: 16pt,
      weight: "semibold",
      tracking: -0.02em,
    )[#it.body])
    v(1em)
  }

  // Level 2 子章节标题:
  // - 使用 medium(500) 获得更平滑的灰度过渡
  show heading.where(level: 2): it => {
    v(1em)
    text(
      size: 12pt,
      weight: "medium",
      tracking: -0.01em,
    )[#it.body]
    v(0.5em)
  }

  // 强调文本优化: 降低加粗强度避免过重
  show strong: set text(weight: 600)

  body
}
