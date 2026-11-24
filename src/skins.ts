/**
 * 皮肤配置（唯一入口）
 * ------------------------------------------------------------
 * 以后加一套皮肤，只改这个文件 + 丢素材，不用动 crab.ts：
 *
 *   1. 立绘：sprites/{动作}.webp（基础款）与 sprites/{皮肤}_{动作}.webp（皮肤款）
 *   2. 语音：voice/line_{皮肤}_pat_1.mp3 …（缺失自动回退基础款 line_pat_1）
 *   3. 缩略图：sprites/skinprev_{皮肤}.webp（设置面板里的预览小图）
 *   4. 本文件里加一条 SKINS 记录即可
 *
 * 台词优先级：自定义 txt > 该皮肤台词 > 基础台词
 * 音色（voiceId）只影响日后批量生成 TTS，运行时不需要它。
 */

export type LineSet = Array<[string, number]>;
export type ActionLine = [string, string];

export type SkinMeta = {
  /** 皮肤 id，需与 state.json 里 skin 字段、素材文件名一致 */
  id: string;
  label: string;
  /** 设置面板缩略图用的立绘 key（sprites/ 下的文件名） */
  thumb: string;
  /** 日后生成语音用的音色 id（不影响运行） */
  voiceId: string;
  /** 待机台词（文本 + 权重） */
  idle: LineSet;
  /** 互动台词覆盖（按动作名）；缺省动作自动回退基础台词 */
  actions?: Record<string, ActionLine[]>;
};

/** 基础套装——同时是所有皮肤的兜底 */
const BASE: SkinMeta = {
  id: "none",
  label: "默认",
  thumb: "skinprev_none",
  voiceId: "female-shaonv",
  idle: [
    ["主人～要看看钱包吗？", 3],
    ["我在看书，顺便帮你盯余额～", 3],
    ["点我就能看到明细啦！", 2],
    ["这本书讲到二进制，好有趣～", 2],
    ["海水有点凉，余额也有点凉…", 1],
    ["今天也省着点花哦～", 2],
    ["我夹！把花掉的钱夹回来！", 1],
    ["写代码辛苦了，记得喝水～", 2],
    ["右键可以设置我哦～", 1],
  ],
  actions: {
    pat: [
      ["好舒服～", "line_pat_1"],
      ["再摸摸嘛～", "line_pat_2"],
      ["嗯…这样很安心", "line_pat_3"],
      ["嘿嘿，被摸头了", "line_pat_4"],
    ],
    angry: [
      ["想…想对本小姐做什么…", "line_angry_1"],
      ["别乱点啦！", "line_angry_2"],
      ["哼，生气了哦", "line_angry_3"],
      ["你、你干嘛呀", "line_angry_4"],
    ],
    shy: [
      ["嗯……别、别这样…", "line_shy_1"],
      ["有点不好意思…", "line_shy_2"],
      ["那个…可以放开吗", "line_shy_3"],
    ],
    dizzy: [
      ["头好晕……", "line_dizzy_1"],
      ["别、别晃了啦…", "line_dizzy_2"],
      ["呃呃…转圈圈了", "line_dizzy_3"],
    ],
    legs: [
      ["别碰腿啦…", "line_legs_1"],
      ["痒痒的…", "line_legs_2"],
      ["那里不行啦", "line_legs_3"],
    ],
  },
};

/** 圣诞装：说雪、礼物、冷，不说书 */
const CHRISTMAS: SkinMeta = {
  id: "christmas",
  label: "圣诞",
  thumb: "skinprev_christmas",
  voiceId: "female-shaonv",
  idle: [
    ["下雪了诶，要一起看吗～", 3],
    ["礼物盒里会不会是余额呀…", 2],
    ["袜子里塞满了代码…", 2],
    ["外面好冷，我就在屏幕角落陪你", 3],
    ["铃铛响了，是充值的声音吗？", 2],
    ["圣诞树我够不到顶，你帮我挂星星", 1],
    ["今天可以多花一点点吧？就一点点", 2],
    ["麋鹿今天不上班，我来巡逻～", 1],
    ["记得喝热可可，别冻着手", 2],
  ],
};

/** 鲸鱼装：海边来客，懒散，怕热 */
const WHALE: SkinMeta = {
  id: "whale",
  label: "鲸鱼",
  thumb: "skinprev_whale",
  voiceId: "ICL_uranus_zh_female_qinglenggaoya_tob",
  idle: [
    ["海里好舒服，要不要一起潜下去～", 3],
    ["帽子戴好了，尾巴不许拉", 2],
    ["我今天有点懒，就趴在这儿了", 3],
    ["陆地上好热啊…想回水里", 2],
    ["用鳃呼吸的话，是不是就不用喘了", 1],
    ["拖鞋是防水的，踩水也不怕", 2],
    ["你敲键盘的声音像气泡，咕噜咕噜", 2],
    ["余额像潮水，涨了又退…", 2],
    ["别捏我帽子，会进水的", 1],
  ],
};

/** 和服装：夏日祭、花火、木屐 */
const YUKATA: SkinMeta = {
  id: "yukata",
  label: "和服",
  thumb: "skinprev_yukata",
  voiceId: "female-shaonv",
  idle: [
    ["穿木屐走路要小心，会踩空的…", 2],
    ["今晚有花火大会，去吗？", 3],
    ["团扇扇一扇，把热都扇走～", 2],
    ["腰封有点紧，但好看就值得", 2],
    ["这颗糖是刚才祭典上买的，分你一半", 2],
    ["风铃响了，是夏天的声音", 2],
    ["浴衣的袖子好大，能装下好多东西", 1],
    ["走慢一点啦，木屐跟不上你", 2],
    ["夜深了，花火也快结束了", 1],
  ],
};

export const SKINS: SkinMeta[] = [BASE, CHRISTMAS, WHALE, YUKATA];

export function getSkin(id: string): SkinMeta {
  for (const s of SKINS) if (s.id === id) return s;
  return BASE;
}

/** 皮肤 id → 素材前缀；基础套装不加前缀 */
export function skinPrefix(id: string): string {
  return id && id !== "none" ? id + "_" : "";
}
