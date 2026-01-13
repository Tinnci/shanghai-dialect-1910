// template.typ - 核心模板

#import "@preview/rubby:0.10.2": get-ruby

// ============================================================
// 1. 上海话 Ruby 注音函数
// ============================================================

// 标准模式：单字 + 罗马字
#let r = get-ruby(
  size: 0.55em,
  pos: bottom,
  dy: 0pt,
  delimiter: "|",
  alignment: "center",
)

// 紧凑模式：适合长罗马字的词组
#let rc = get-ruby(
  size: 0.5em,
  pos: bottom,
  dy: 0pt,
  delimiter: "|",
  alignment: "center",
)

// ============================================================
// 2. 课文标题宏
// ============================================================

#let exercise(num, zh_title, ro_title) = {
  // 每课重置脚注计数器
  counter(footnote).update(0)
  
  // 课与课之间的间距
  v(1.5em, weak: true)
  
  // 标题区块
  align(center, block(
    width: 100%,
    inset: (y: 0.8em),
    stroke: none,
  )[
    #text(size: 10pt, weight: "bold", tracking: 0.5pt)[
      EXERCISE NO. #num
    ]
    #v(0.3em)
    #text(size: 14pt, weight: "bold")[#zh_title]
    #v(0.2em)
    #text(size: 9pt, style: "italic", tracking: 0.3pt)[#ro_title]
  ])
  
  v(0.5em)
}

// ============================================================
// 3. 辅助组件
// ============================================================

// 发音说明条目
#let pron-entry(roman, description) = {
  grid(
    columns: (3cm, 1fr),
    gutter: 1em,
    text(weight: "bold", font: "Libertinus Serif")[#roman],
    text[#description]
  )
  v(0.3em)
}

// 词汇表条目
#let vocab(zh, ro, en) = {
  grid(
    columns: (2cm, 4cm, 1fr),
    gutter: 0.5em,
    text(weight: "bold")[#zh],
    text(style: "italic")[#ro],
    text[#en]
  )
}

// ============================================================
// 4. 全局页面配置
// ============================================================

#let project(body) = {
  // 页面设置
  set page(
    paper: "a5",
    margin: (inside: 2.2cm, outside: 1.8cm, top: 2cm, bottom: 2cm),
    numbering: "1",
    number-align: center,
  )
  
  // 字体设置
  set text(
    font: ("Source Han Serif SC", "Noto Serif CJK SC", "Libertinus Serif"),
    size: 10.5pt,
    lang: "zh",
  )
  
  // 段落设置
  set par(
    leading: 1.3em,  // 行间距（给 Ruby 留空间）
    justify: true,
    first-line-indent: 0em,
  )
  
  // 脚注样式：复刻原书 (1) 格式
  set footnote(numbering: n => [(#n)])
  set footnote.entry(
    separator: line(length: 30%, stroke: 0.5pt),
    indent: 0em,
    gap: 0.5em,
  )
  
  // 标题样式
  set heading(numbering: none)
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(2em)
    align(center, text(size: 16pt, weight: "bold")[#it.body])
    v(1em)
  }
  
  show heading.where(level: 2): it => {
    v(1em)
    text(size: 12pt, weight: "bold")[#it.body]
    v(0.5em)
  }
  
  body
}
