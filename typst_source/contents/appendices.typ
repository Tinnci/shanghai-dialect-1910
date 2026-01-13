// appendices.typ - 附录部分

#import "../template.typ": vocab

// ============================================================
// 索引条目宏
// ============================================================

#let index-entry(topic, exercise-num) = {
  grid(
    columns: (1fr, auto),
    gutter: 0.3em,
    [#topic #box(width: 1fr, repeat[.])], [Exercise #exercise-num],
  )
}

// ============================================================
// 英文索引
// ============================================================

= English Index / 英文索引

#text(style: "italic", size: 9pt)[
  _Note: Numbers refer to page numbers in the original 1910 edition._ \
  注：索引中的数字为原书 (1910年版) 页码。
]

#v(0.5em)

#list(
  [Ancestry of the Chinese and Japanese the same... 132],
  [Anti foot binding Society... 175],
  [Apprentice learning a trade... 99],
  [Arabian horse. Faithfulness of.. 203],
  [Arsenal, foundery... 150],
  [Benefit of knowing Chinese characters... 94],
  [Benefit of reading the papers... 98],
  [Benefit of prohibiting night gardens... 214],
  [Betrothal customs... 185],
  [Bicycle... 90],
  [Blind and lame man... 47],
  [Buying a bird... 18],
  [Buying land... 250],
  [Buying land 2nd Part... 252],
  [Buying things for another... 199],
  [Camel, A... 248],
  [Carriages, Different kinds... 66],
  [Chinese students... 114],
  [City children, Two... 131],
  [Collecting bills at Festival times... 153],
  [Collecting Municipal Tax... 100],
  [Collision of two vehicles... 49],
  [Complaining of the weather... 26],
  [Conversation between a shop keeper and a customer... 265],
  [Curing a stubborn child... 177],
  [Dangerous things... 190],
  [Detective, A... 61],
  [Dialects, Different... 3],
  [Diligent in business and accumulating money... 40],
  [Dirty water... 7],
  [Diseases... 13],
  [Door of Hope... 35],
  [Dreaming... 170],
  [Earthquake in Italy... 47],
  [Edibles... 12],
  [Escaping the heat... 145],
  [Escaping the heat at Mokanshan... 147],
  [Escaping the heat at a summer resort... 27],
  [Excavation of canals... 120],
  [Exhorting the police to study... 2],
  [Explosion of a match factory... 65],
  [Fire Company's methods... 83],
  [First aid... 109],
  [Foolish student... 216],
  [Fox A, that borrows the dignity of a lion... 221],
  [French tram driver's wages... 64],
  [Funeral... 143],
  [Funeral in the Settlement... 144],
  [Gambling... 78],
  [Gate interpreter and a detective... 263],
  [Girls studying and learning house work... 56],
  [Good way of spending a summer vacation... 58],
  [Good man has a good reward... 141],
  [Goose that laid the golden egg... 207],
  [Great wall of China... 173],
  [Hail storm... 168],
  [Health matters... 67],
  [Health rules or measures... 96],
  [Horseback riding... 192],
  [Horses, the utility of... 147],
  [Hot weather... 257-258-260],
  [Household furniture... 29],
  [Hunting at Mokanshan... 4],
  [Idolatrous performances for the sick... 181],
  [Idolatrous ceremonies for the dead... 183],
  [Ignorance of Chinese women... 110],
  [Illumination in the French Settlement... 34],
  [Illumination and Decoration in the French Concession... 112],
  [Infectious diseases... 22],
  [Injuring others and receiving self injury... 161],
  [International Opium Commission... 104],
  [Lark, A... 200],
  [Meeting pirates... 6],
  [Merciful man, A... 242],
  [Micellaneous sentences... 1],
  [Milk business... 157],
  [Monkey show... 125],
  [Motor men. The recruiting of... 75],
  [Nanking Road... 77],
  [Native, A, who wished to be a policeman... 51],
  [Opium... 101],
  [Opium shop closing... 121],
  [Opium meeting in the Y.M.C.A... 85],
  [Opium Commission... 104],
  [Ordinary occurences... 15],
  [Patience. Exhorting to... 213],
  [Perseverence... 155],
  [Pirate, named "Van Kau-deu... 129],
  [Play... 1],
  [Pleasure seeking man... 66],
  [Police drill quarters... 124],
  [Polite greetings... 268],
  [Poppy. Exhorting the people not to cultivate... 212],
  [Proclamation... 70],
  [Prohibiting the racing of dragon boats... 139],
  [Rain too abundant... 60],
  [Rape... 166],
  [Rats... 48],
  [Rebelling against parents... 91],
  [Refugees, Good way of helping... 220],
  [Repairing graves... 31],
  [Rescuing from fire... 32],
  [Riding in a carriage, in great haste... 24],
  [Riding in the rain... 45],
  [Ricsha... 195],
  [Ricsha and wheel-barrow... 119],
  [Rowdy, A... 88],
  [Satisfied child... 218],
  [Seasons, The four... 80],
  [Shanghai... 42],
  [Shanghai... 116],
  [Shanghai gardens... 44],
  [Sharper, A... 52],
  [Shop keeper and customer... 262],
  [Sicawei and Jessfield... 162],
  [Sickness... 16],
  [Silk culture... 254],
  [Soochow and Hangchow... 82],
  [Spring scenery... 11],
  [Study... 37],
  [Studying... 21],
  [Swindling... 87],
  [Tailor, A... 159],
  [Tall men for soldiers... 137],
  [Tartar general A... 107],
  [Theatrical performance... 152],
  [Thief A... 17],
  [Thief stealing. A... 193],
  [Tips, cumshas... 159],
  [Training a dog... 54],
  [Trams... 196],
  [Value of time... 8],
  [Virtuous dog... 38],
  [Weather... 58],
  [Weather that causes sickness... 62],
  [Weather that the people like... 73],
  [Wheel-barrow man... 164],
  [Wedding ceremonies... 187],
  [William Tell. The Swiss... 209],
  [Wolf. The boy who cried "wolf"... 205],
)

#pagebreak()

// ============================================================
// 勘误表
// ============================================================

= Errata / 勘误

本节列出原书中的印刷错误及更正。

== ERRATA (勘误表)

#table(
  columns: (auto, auto, auto, auto, auto),
  inset: 10pt,
  align: horizon,
  table.header([*Exercise*], [*Page*], [*Line*], [*Error*], [*Correction*]),
  [No 2], [2], [8], [yi], [i],
  [No 5], [5], [9], [nyuug], [nyung],
  [No 5], [5], [17], [kyau], [kau],
  [No 7], [7], [Title], [Tsauh], [tshauh],
  [No 8], [8], [9], [ngen], [nge],
  [No 10], [11], [4], [hwang], [hwaung],
  [No 10], [11], [5], [綠], [绿],
  [No 10], [12], [8], [ben], [be],
  [No 12], [13], [6], [kyah], [kyak],
  [No 13], [14], [2], [乾], [干],
  [No 14], [16], [2], [tsauh], [tshauh],
  [No 15], [16], [1], [kyau], [jau],
  [No 17], [18], [1], [dzen], [dze],
  [No 18], [19], [3], [juk], [juh],
  [No 18], [19], [6], [mian], [miau],
  [No 19], [21], [9], [kwhe], [kwe],
  [No 19], [21], [13], [we], [wen],
  [No 20], [23], [7], [ke], [ken],
  [No 20], [23], [10], [kwe], [kwhe],
  [No 20], [24], [3], [yau], [iao],
  [No 21], [25], [6], [we], [wen],
  [No 21], [25], [10], [ben], [be],
  [No 21], [25], [11], [we], [wen],
  [No 25], [31], [4], [tsauh], [tshauh],
  [No 27], [34], [2], [kwen], [kwe],
  [No 28], [36], [4], [nyien], [nyi],
  [No 28], [36], [10], [ji], [jien],
  [No 28], [37], [1], [we], [wen],
  [No 29], [38], [12], [kwen], [kwe],
  [No 31], [40], [1], [牌], [牌],
  [No 31], [41], [15], [戮], [戲],
  [No 32], [43], [18], [we], [wen],
  [No 34], [46], [2], [we], [wen],
  [No 34], [46], [4], [tse], [tsen],
  [No 34], [46], [10], [yau], [iao],
  [No 35], [47], [Title], [kyahi], [kyak],
  [No 37], [49], [6], [khwe], [khwen],
  [No 38], [50], [11], [me], [men],
  [No 38], [50], [15], [tsing], [tshing],
  [No 40], [53], [5], [tshan], [tsan],
  [No 40], [54], [2], [zoo], [dzoo],
  [No 41], [55], [11], [tse], [tsen],
  [No 41], [55], [16], [ke], [ken],
  [No 43], [58], [4], [dazk], [dzak],
  [No 43], [58], [10], [水], [海],
  [No 44], [59], [2], [ke], [ken],
  [No 44], [59], [13], [ban], [pan],
  [No 45], [61], [1], [ze], [zen],
  [No 47], [63], [1], [vaung], [vung],
  [No 47], [63], [3], [kwe], [kwen],
  [No 59], [80], [3], [tsau], [tshau],
  [No 61], [85], [10], [位], [会],
  [No 62], [86], [3], [boo], [poo],
  [No 64], [88], [11], [zing], [dzing],
  [No 64], [89], [3], [触], [戮],
  [No 65], [90], [8], [tshai], [tshia],
  [No 65], [91], [7], [軋], [扎],
  [No 67], [94], [6], [ngen], [nge],
  [No 67], [96], [5], [zauh], [dzauh],
  [No 68], [97], [14], [zing], [dzing],
  [No 80], [119], [7], [yen], [yien],
  [No 80], [120], [3], [dzu], [dzui],
  [No 81], [121], [1], [霸], [墦],
  [No 81], [121], [12], [ioe], [yoen],
  [No 82], [122], [2], [nien], [nyien],
  [No 107], [169], [2], [en], [sen],
  [No 110], [176], [4], [凂], [避],
  [No 111], [178], [17], [i], [yi],
  [No 115], [186], [5], [pan], [pah],
  [No 118], [192], [10], [yui], [iui],
  [No 121], [197], [11], [銅], [个],
  [No 127], [211], [4], [joch], [kyoeh],
  [No 127], [211], [7], [kien], [kyien],
  [No 130], [216], [3], [tsuh], [tshuh],
  [No 133], [220], [4], [whaung], [hwaung],
  [No 134], [222], [5], [kyiun], [kyuin],
  [No 153], [265], [3], [戮], [戳],
)

== ERRATA TO NOTES (注释部分勘误)

#table(
  columns: (auto, auto, auto, auto),
  inset: 10pt,
  align: horizon,
  table.header([*Page*], [*No. of note*], [*Error*], [*Correction*]),
  [19], [(4)], [nead], [road],
  [19], [(6)], [cach], [each],
  [26], [(6)], [lrrot], [Rot],
  [27], [(14)], [Chinkian8], [Chinkiang],
  [29], [(3)], [Lenley], [Lonely],
  [30], [(11)], [buchet], [bucket],
  [66], [(4)], [Ningpo], [Nanking],
  [86], [(4)], [uarity], [Variety],
)

#pagebreak()

// ============================================================
// 词汇表 (可选扩展)
// ============================================================

= Vocabulary / 词汇表

以下为本书常见方言词汇对照：

#vocab[巡捕][dzing-boo][Police]
#vocab[包打听][pau-tang-thing][Detective]
#vocab[电车][dien-tsho][Tram]
#vocab[东洋车][toong-yang-tsho][Rickshaw]
#vocab[钱庄][dzien-tsaung][Native Bank]
