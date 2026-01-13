// template.typ - 核心模板

// 移除 import，我们使用自定义实现来彻底解决依赖问题
// #import "@preview/rubby:0.10.2": get-ruby

// ============================================================
// 1. 自定义 Ruby 实现 (Reflowable & Robust)
// ============================================================

#let r(roman, hanzi) = {
  // 测量内容宽度的辅助函数
  let measure-width(content) = style(styles => measure(content, styles).width)
  
  // 使用 layout 获取可用空间上下文（虽然这里主要是为了测量）
  layout(size => {
    // 构造最终要显示的元素
    let rt = text(size: 0.55em, bottom-edge: "baseline")[#roman]
    let rb = text(top-edge: "baseline")[#hanzi]
    
    // 我们使用 box + stack 来实现垂直堆叠
    // 关键在于：外层 box 的宽度由较宽者决定
    // 较窄者在其中居中
    
    // 下面这种实现方式依赖于 typst 的自然布局
    // stack 会自动取最宽子元素的宽度
    // align(center) 会让较窄的子元素居中
    // 这正是我们需要的 Ruby 效果
    
    box(baseline: 20%, stack(
      dir: ttb,
      spacing: 2pt, // 汉字和拼音的间距
      align(center, rb), // 汉字在上
      align(center, rt)  // 拼音在下
    ))
  })
}

// 紧凑模式
#let rc = r

// ============================================================
// 2. 课文标题宏
// ============================================================

#let exercise(num, zh_title, ro_title) = {
  // 1. 插入一个隐藏标题供目录抓取
  block(height: 0pt, heading(
    level: 2, 
    outlined: true,
    numbering: none
  )[Exercise #num: #zh_title (#ro_title)])

  // 2. 每课重置脚注计数器
  counter(footnote).update(0)
  
  // 3. 课与课之间的间距
  v(1.5em, weak: true)
  
  // 4. 标题可视区块
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

#let pron-entry(roman, description) = {
  grid(
    columns: (3cm, 1fr),
    gutter: 1em,
    text(weight: "bold", font: "Libertinus Serif")[#roman],
    text[#description]
  )
  v(0.3em)
}

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
  set page(
    paper: "a5",
    margin: (inside: 2.2cm, outside: 1.8cm, top: 2cm, bottom: 2cm),
    numbering: "1",
    number-align: center,
  )
  
  set text(
    font: ("Noto Serif CJK SC",  "Libertinus Serif"),
    size: 10.5pt,
    lang: "zh",
  )
  
  set par(
    leading: 1.3em,
    justify: true,
    first-line-indent: 0em,
  )
  
  set footnote(numbering: n => [(#n)])
  set footnote.entry(
    separator: line(length: 30%, stroke: 0.5pt),
    indent: 0em,
    gap: 0.5em,
  )
  
  set heading(numbering: none)
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(2em)
    align(center, text(size: 16pt, weight: "bold")[#it.body])
    v(1em)
  }
  
  show heading.where(level: 2): it => {
    // 隐藏的目录标题不显示
  }
  
  body
}
