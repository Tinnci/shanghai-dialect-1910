// preliminary.typ - 前言部分

#import "../metadata.typ": *

// ============================================================
// 封面
// ============================================================

#page(numbering: none)[
  #v(3cm)
  
  #align(center)[
    #text(size: 24pt, weight: "bold")[
      #book-title-zh
    ]
    
    #v(0.5em)
    
    #text(size: 14pt, style: "italic")[
      #book-title-en
    ]
    
    #v(0.3em)
    
    #text(size: 10pt)[
      #book-subtitle
    ]
    
    #v(3cm)
    
    #text(size: 12pt)[
      #author
    ]
    
    #v(1cm)
    
    #text(size: 10pt)[
      Originally published by #publisher, #original-year
    ]
    
    #v(2cm)
    
    #line(length: 50%, stroke: 0.5pt)
    
    #v(0.5em)
    
    #text(size: 9pt)[
      Digitized Edition / 数字化版本 (#digitized-year)
    ]
  ]
]

// ============================================================
// 版权页
// ============================================================

#page(numbering: none)[
  #v(1fr)
  
  #block(inset: 1em)[
    == Public Domain Notice / 公有版权声明
    
    #copyright-notice
    
    #v(1em)
    
    *Source / 来源:*
    
    Internet Archive
    
    #link(source-url)[#text(size: 8pt)[#source-url]]
  ]
  
  #v(1fr)
]

// ============================================================
// 序言 (可根据原书内容填充)
// ============================================================

= Preface / 序言

#lorem(100)

// TODO: 根据原书序言内容补充

#pagebreak()

// ============================================================
// 发音指南
// ============================================================

= Key to the Pronunciation / 发音说明

== Initials / 声母

本书采用上海罗马字系统 (Shanghai Romanised System)，以下为主要声母说明：

// TODO: 根据原书发音键内容补充

#pagebreak()
