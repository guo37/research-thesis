import fs from 'node:fs/promises';
import path from 'node:path';
import { FileBlob, PresentationFile } from '@oai/artifact-tool';

const tmp = process.env.TMP_DIR;
const starter = path.join(tmp, 'template-starter.pptx');
const finalPptx = process.env.FINAL_PPTX;
const previewDir = path.join(tmp, 'preview');
const layoutDir = path.join(tmp, 'layout', 'final');
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(layoutDir, { recursive: true });

const BLUE = '#005EA8';
const LIGHT = '#EAF4FF';
const TEAL = '#00A6A6';
const ORANGE = '#F2994A';
const GRAY = '#4D4D4D';
const BORDER = '#A8B7C7';
const W = 960;

function addText(slide, text, x, y, w, h, opt = {}) {
  const s = slide.shapes.add({
    geometry: 'textbox',
    position: { left: x, top: y, width: w, height: h },
    fill: 'none',
    line: { style: 'solid', fill: 'none', width: 0 },
  });
  s.text = text;
  s.text.style = {
    fontSize: opt.size ?? 20,
    bold: opt.bold ?? false,
    color: opt.color ?? '#222222',
    alignment: opt.align ?? 'left',
    typeface: 'Microsoft YaHei',
  };
  return s;
}

function addBox(slide, text, x, y, w, h, opt = {}) {
  const s = slide.shapes.add({
    geometry: opt.geometry ?? 'roundRect',
    position: { left: x, top: y, width: w, height: h },
    fill: opt.fill ?? 'white',
    line: { style: 'solid', fill: opt.line ?? BORDER, width: opt.lineWidth ?? 1.1 },
    borderRadius: opt.radius ?? 10,
    shadow: 'shadow-none',
  });
  s.text = text;
  s.text.style = {
    fontSize: opt.size ?? 18,
    bold: opt.bold ?? false,
    color: opt.color ?? '#222222',
    alignment: opt.align ?? 'center',
    typeface: 'Microsoft YaHei',
  };
  return s;
}

function topOf(el) {
  return el.position?.top ?? el.frame?.top ?? 0;
}

function deleteIfPossible(el) {
  if (typeof el.delete === 'function') el.delete();
}

function clearBody(slide) {
  for (const shape of [...(slide.shapes.items ?? [])]) {
    const hasText = String(shape.text ?? '').trim().length > 0;
    const top = topOf(shape);
    if (hasText || (top >= 40 && top < 500)) deleteIfPossible(shape);
  }
  for (const image of [...(slide.images.items ?? [])]) {
    const top = topOf(image);
    if (top >= 40) deleteIfPossible(image);
  }
  for (const table of [...(slide.tables.items ?? [])]) {
    if (table.id && typeof slide.tables.deleteById === 'function') {
      slide.tables.deleteById(table.id);
    } else {
      deleteIfPossible(table);
    }
  }
}

function addHeader(slide, title) {
  slide.shapes.add({
    geometry: 'rect',
    position: { left: 55, top: 0, width: 710, height: 42 },
    fill: 'white',
    line: { style: 'solid', fill: 'white', width: 0 },
  });
  addText(slide, title, 68, 5, 710, 36, { size: 23, bold: true, color: BLUE });
}

function addLine(slide, x1, y1, x2, y2, opt = {}) {
  return slide.shapes.add({
    geometry: 'line',
    position: { left: x1, top: y1, width: x2 - x1, height: y2 - y1 },
    fill: 'none',
    line: { style: 'solid', fill: opt.color ?? BLUE, width: opt.width ?? 2 },
  });
}

function addPill(slide, text, x, y, w, color = BLUE) {
  return addBox(slide, text, x, y, w, 32, {
    fill: color,
    line: color,
    color: 'white',
    bold: true,
    size: 14,
    radius: 16,
  });
}

function addBulletList(slide, items, x, y, w, gap = 38, size = 19) {
  items.forEach((item, i) => {
    addBox(slide, String(i + 1), x, y + i * gap + 3, 22, 22, {
      fill: BLUE,
      line: BLUE,
      color: 'white',
      size: 13,
      bold: true,
      radius: 11,
    });
    addText(slide, item, x + 34, y + i * gap, w - 34, 32, { size });
  });
}

function updateShapeText(shape, text, style = {}) {
  shape.text = text;
  shape.text.style = { typeface: 'Microsoft YaHei', ...style };
  if (shape.bringToFront) shape.bringToFront();
  return shape;
}

function findTextShape(slide, needle) {
  const items = slide.shapes.items ?? [];
  const hit = items.find((s) => String(s.text ?? '').includes(needle));
  if (!hit) throw new Error(`Text shape not found: ${needle}`);
  return hit;
}

function updateTextOnSlide(slide, needle, text, style = {}) {
  return updateShapeText(findTextShape(slide, needle), text, style);
}

const presentation = await PresentationFile.importPptx(await FileBlob.load(starter));

const importedTables = await presentation.inspect({ kind: 'table', maxChars: 20000 });
for (const line of importedTables.ndjson.split(/\r?\n/).filter(Boolean)) {
  const record = JSON.parse(line);
  if (record.kind === 'table' && record.id && record.slide) {
    const slide = presentation.slides.getItem(record.slide - 1);
    if (typeof slide.tables.deleteById === 'function') slide.tables.deleteById(record.id);
    else deleteIfPossible(presentation.resolve(record.id));
  }
}

// 1. Title
{
  const slide = presentation.slides.getItem(0);
  updateTextOnSlide(slide, '研究进展', '研究进展汇报', {
    fontSize: 38,
    bold: true,
    color: 'white',
    alignment: 'center',
  });
  updateTextOnSlide(slide, '二零二六', '2026年06月17日', {
    fontSize: 20,
    bold: true,
    color: 'white',
    alignment: 'center',
  });
  addText(slide, '面向教育资源检索的可信多模态知识推理研究', 180, 248, 600, 45, {
    size: 24,
    bold: true,
    color: 'white',
    align: 'center',
  });
  addText(slide, 'Trustworthy Multimodal Knowledge Reasoning for Educational Resource Retrieval', 185, 292, 590, 26, {
    size: 13,
    color: '#DDEFFF',
    align: 'center',
  });
}

// 2. Route restructuring
{
  const slide = presentation.slides.getItem(1);
  clearBody(slide);
  addHeader(slide, '研究路线重构');
  addText(slide, '从“大而全模型堆叠”收敛到“可信教育资源检索”', 80, 56, 800, 34, {
    size: 25,
    bold: true,
    align: 'center',
  });
  addBox(slide, '旧路线\nGFM 预训练\nCausal-MMKG / do(C)\nCausal VAE + CosSim\nLLM prompt 解释', 76, 130, 260, 220, {
    fill: '#F7F7F7',
    line: '#BBBBBB',
    size: 19,
    color: '#444444',
    bold: true,
  });
  addBox(slide, '定位调整\n旧实验降级为\npreliminary / pilot\n用于说明探索过程', 350, 150, 240, 180, {
    fill: '#FFF4E8',
    line: ORANGE,
    size: 18,
    color: '#5A3B1E',
    bold: true,
  });
  addBox(slide, '新路线\n可信教育资源检索\n资源是否对齐\n缺失是否可信\n解释是否忠实', 624, 130, 260, 220, {
    fill: LIGHT,
    line: BLUE,
    size: 19,
    color: '#143A5A',
    bold: true,
  });
  addLine(slide, 336, 238, 350, 238, { color: ORANGE, width: 3 });
  addLine(slide, 590, 238, 624, 238, { color: ORANGE, width: 3 });
  addText(slide, '最终贡献不再以 GFM / Causal-MMKG / Causal VAE 为主，而围绕可信检索中的三个科学问题展开。', 92, 390, 776, 40, {
    size: 19,
    color: GRAY,
    align: 'center',
  });
}

// 3. Core questions
{
  const slide = presentation.slides.getItem(2);
  clearBody(slide);
  addHeader(slide, '核心研究问题');
  addText(slide, '教育资源检索需要回答三个可信问题', 140, 58, 680, 34, {
    size: 27,
    bold: true,
    align: 'center',
  });
  const xs = [70, 350, 630];
  const cards = [
    ['资源是否对齐？', 'RC1', '教育知识结构约束的\n跨模态资源对齐', 'alignment score'],
    ['缺失是否可信？', 'RC2', '面向非随机模态缺失的\n选择性补全', 'modality reliability'],
    ['解释是否忠实？', 'RC3', '融合路径、对齐与可靠性的\n图约束解释生成', 'faithful explanation'],
  ];
  cards.forEach((c, i) => {
    addBox(slide, c[1], xs[i] + 88, 120, 70, 36, {
      fill: BLUE,
      line: BLUE,
      color: 'white',
      size: 17,
      bold: true,
      radius: 18,
    });
    addBox(slide, `${c[0]}\n\n${c[2]}\n\n输出：${c[3]}`, xs[i], 172, 250, 210, {
      fill: i === 1 ? '#FFF7EA' : LIGHT,
      line: i === 1 ? ORANGE : BLUE,
      size: 18,
      bold: true,
    });
  });
}

// 4. Overall route
{
  const slide = presentation.slides.getItem(3);
  clearBody(slide);
  addHeader(slide, '总体技术路线图');
  const y = 86;
  const stages = [
    ['数据层', 'ScienceQA\nOpenStax / MOOC'],
    ['知识层', 'resource-concept mapping\nconcept graph'],
    ['RC1', 'alignment score'],
    ['RC2', 'modality status\nreliability score'],
    ['RC3', 'faithful explanation'],
  ];
  stages.forEach((s, i) => {
    const x = 56 + i * 174;
    addBox(slide, `${s[0]}\n\n${s[1]}`, x, y + (i % 2) * 34, 145, 130, {
      fill: i < 2 ? '#F7FBFF' : LIGHT,
      line: BLUE,
      size: 16,
      bold: true,
    });
    if (i < stages.length - 1) {
      addLine(slide, x + 145, y + 65 + (i % 2) * 34, x + 174, y + 65 + ((i + 1) % 2) * 34, {
        color: ORANGE,
        width: 3,
      });
    }
  });
  addText(slide, '统一数据底座支撑三章：资源-概念对齐、模态缺失可靠性、图约束解释生成。', 110, 330, 740, 34, {
    size: 20,
    bold: true,
    align: 'center',
  });
  addBox(slide, '共享 schema：resources.csv / concepts.csv / resource_concept_edges.csv / modality_status.csv', 150, 386, 660, 50, {
    fill: '#F8F8F8',
    line: '#D0D0D0',
    size: 16,
  });
}

// 5. RC1
{
  const slide = presentation.slides.getItem(4);
  clearBody(slide);
  addHeader(slide, 'RC1：教育知识结构约束的跨模态资源对齐');
  addText(slide, '问题：通用 CLIP 只学习开放域图文相似，不保证教学目标一致。', 70, 58, 820, 28, {
    size: 20,
    bold: true,
  });
  const xs = [80, 300, 520, 740];
  const boxes = ['ScienceQA resource\nquestion / image / lecture', 'Frozen CLIP / SigLIP\n+ adapter', 'concept-aware\nhard negatives', 'alignment score'];
  boxes.forEach((b, i) => {
    addBox(slide, b, xs[i], 150, 155, 105, {
      fill: i === 3 ? '#E8F7F3' : LIGHT,
      line: i === 3 ? TEAL : BLUE,
      size: 15,
      bold: true,
    });
    if (i < boxes.length - 1) addLine(slide, xs[i] + 155, 202, xs[i + 1], 202, { color: ORANGE, width: 3 });
  });
  addBulletList(slide, [
    'resource-concept alignment：资源与 topic / skill 对齐',
    'hierarchy regularization：约束概念层级一致性',
    'hard negative：同学科、同 topic 不同 skill 更难区分',
  ], 110, 310, 760, 42, 18);
}

// 6. RC2
{
  const slide = presentation.slides.getItem(5);
  clearBody(slide);
  addHeader(slide, 'RC2：面向非随机模态缺失的选择性补全');
  addText(slide, '核心判断：不是所有缺图都应该补；首先要诊断 missingness 是否依赖知识点。', 72, 58, 820, 28, {
    size: 20,
    bold: true,
  });
  const xs = [88, 346, 604];
  [
    ['missingness diagnosis', 'has_image ~ subject + topic + skill'],
    ['missing type classifier', 'observed / accidental / structural / ambiguous'],
    ['selective completion', '只对确有视觉需求的偶然缺失补全'],
  ].forEach((b, i) => {
    addBox(slide, `${b[0]}\n\n${b[1]}`, xs[i], 140, 210, 126, {
      fill: i === 1 ? '#FFF7EA' : LIGHT,
      line: i === 1 ? ORANGE : BLUE,
      size: 16,
      bold: true,
    });
    if (i < 2) addLine(slide, xs[i] + 210, 203, xs[i + 1], 203, { color: ORANGE, width: 3 });
  });
  addBox(slide, '当前重点：ScienceQA image missingness 数据诊断\n统计 subject/topic/skill 缺图率、MI、chi-square、logistic regression AUC', 116, 330, 728, 72, {
    fill: '#F8F8F8',
    line: '#D0D0D0',
    size: 18,
    bold: true,
  });
}

// 7. RC3
{
  const slide = presentation.slides.getItem(6);
  clearBody(slide);
  addHeader(slide, 'RC3：路径-对齐-可靠性约束解释生成');
  addText(slide, '目标：让教育资源推荐解释可验证、可追溯、忠实于证据。', 86, 58, 790, 30, {
    size: 21,
    bold: true,
    align: 'center',
  });
  ['graph path', 'alignment score', 'modality status', 'reliability score'].forEach((t, i) =>
    addBox(slide, t, 80, 120 + i * 58, 190, 38, { fill: LIGHT, line: BLUE, size: 16, bold: true }),
  );
  addBox(slide, 'Evidence Package', 360, 170, 220, 92, {
    fill: '#FFF7EA',
    line: ORANGE,
    size: 22,
    bold: true,
    color: '#5A3B1E',
  });
  addBox(slide, 'constrained LLM\nexplanation', 650, 120, 190, 70, { fill: LIGHT, line: BLUE, size: 17, bold: true });
  addBox(slide, 'verifier\nentity / relation / claim', 650, 245, 190, 82, { fill: '#E8F7F3', line: TEAL, size: 17, bold: true });
  addLine(slide, 270, 218, 360, 218, { color: ORANGE, width: 3 });
  addLine(slide, 580, 218, 650, 155, { color: ORANGE, width: 3 });
  addLine(slide, 745, 190, 745, 245, { color: ORANGE, width: 3 });
  addText(slide, '输出：faithful educational explanation', 230, 390, 500, 32, {
    size: 22,
    bold: true,
    color: BLUE,
    align: 'center',
  });
}

// 8. Schema
{
  const slide = presentation.slides.getItem(7);
  clearBody(slide);
  addHeader(slide, '数据集与统一 Schema');
  addText(slide, 'ScienceQA 可重构为教育资源检索数据底座，但不是现成知识图谱。', 76, 58, 820, 28, {
    size: 20,
    bold: true,
  });
  const headers = ['表', '核心字段', '用途'];
  const rows = [
    ['resources.csv', 'question, choices, image, lecture, solution', '资源基本单元'],
    ['concepts.csv', 'subject, topic, skill, grade', '概念节点'],
    ['resource_concept_edges.csv', 'resource_id, concept_id', '资源-概念映射'],
    ['concept_edges.csv', 'subject-topic-skill hierarchy', '弱知识结构'],
    ['modality_status.csv', 'has_image, status, reliability', 'RC2 输入输出'],
  ];
  const x = 70;
  const y = 116;
  const widths = [220, 410, 230];
  const rh = 54;
  headers.forEach((h, i) => addBox(slide, h, x + widths.slice(0, i).reduce((a, b) => a + b, 0), y, widths[i], 40, {
    fill: BLUE,
    line: BLUE,
    color: 'white',
    size: 15,
    bold: true,
    radius: 0,
  }));
  rows.forEach((r, ri) => r.forEach((c, ci) => addBox(slide, c, x + widths.slice(0, ci).reduce((a, b) => a + b, 0), y + 40 + ri * rh, widths[ci], rh, {
    fill: ri % 2 ? 'white' : '#F7FBFF',
    line: '#C8D4DF',
    size: 14,
    radius: 0,
  })));
}

// 9. Exp0
{
  const slide = presentation.slides.getItem(8);
  clearBody(slide);
  addHeader(slide, '当前最小可执行实验：ScienceQA 数据诊断');
  addText(slide, '已完成 Exp0：验证 image missingness 是否依赖 subject / topic / skill。', 70, 56, 820, 28, {
    size: 20,
    bold: true,
  });
  [
    ['样本数', '21,208'],
    ['缺图率', '51.28%'],
    ['topic MI', '0.3211'],
    ['skill MI', '0.6884'],
  ].forEach((m, i) => addBox(slide, `${m[1]}\n${m[0]}`, 70 + i * 215, 110, 170, 85, {
    fill: i === 3 ? '#E8F7F3' : LIGHT,
    line: i === 3 ? TEAL : BLUE,
    size: 20,
    bold: true,
    color: '#143A5A',
  }));
  const rows = [
    ['baseline', 'test AUC'],
    ['majority', '0.5000'],
    ['subject-only', '0.7985'],
    ['topic-only', '0.8833'],
    ['skill-only', '0.9997'],
    ['topic+skill', '0.9997'],
  ];
  rows.forEach((r, i) => {
    addBox(slide, r[0], 230, 230 + i * 35, 250, 35, {
      fill: i === 0 ? BLUE : (i % 2 ? 'white' : '#F7FBFF'),
      line: '#C8D4DF',
      color: i === 0 ? 'white' : '#222222',
      size: 15,
      bold: i === 0,
      radius: 0,
    });
    addBox(slide, r[1], 480, 230 + i * 35, 180, 35, {
      fill: i === 0 ? BLUE : (i % 2 ? 'white' : '#F7FBFF'),
      line: '#C8D4DF',
      color: i === 0 ? 'white' : '#222222',
      size: 15,
      bold: i === 0,
      radius: 0,
    });
  });
  addBox(slide, '结论：支持 structured missingness / MNAR 初步假设；skill 是最强信号。', 115, 448, 730, 36, {
    fill: '#FFF7EA',
    line: ORANGE,
    size: 17,
    bold: true,
    color: '#5A3B1E',
  });
}

// 10. Timeline
{
  const slide = presentation.slides.getItem(9);
  clearBody(slide);
  addHeader(slide, '近期执行计划');
  const weeks = [
    ['Week 1', 'ScienceQA schema\nimage missingness diagnosis'],
    ['Week 2', 'RC1 baseline\nCLIP / adapter / hard negatives'],
    ['Week 3', 'RC2 annotation\nmissing type classifier'],
    ['Week 4', 'RC3 evaluation\nfaithfulness metrics'],
  ];
  weeks.forEach((w, i) => {
    const x = 80 + i * 210;
    addPill(slide, w[0], x + 30, 110, 120, i === 0 ? TEAL : BLUE);
    addBox(slide, w[1], x, 172, 180, 150, {
      fill: i === 0 ? '#E8F7F3' : LIGHT,
      line: i === 0 ? TEAL : BLUE,
      size: 17,
      bold: true,
    });
    if (i < 3) addLine(slide, x + 180, 247, x + 210, 247, { color: ORANGE, width: 3 });
  });
  addText(slide, '当前状态：研究主线重构完成；Exp0 数据诊断已完成；Exp0.1 标注候选表已生成。', 96, 400, 768, 36, {
    size: 20,
    bold: true,
    align: 'center',
  });
}

// 11. Risks
{
  const slide = presentation.slides.getItem(10);
  clearBody(slide);
  addHeader(slide, '风险与应对');
  const rows = [
    ['topic 粒度粗', '引入 skill / OpenStax 章节结构'],
    ['prerequisite relation 缺失', '小规模人工图谱 + LLM 辅助生成后抽检'],
    ['缺失类型无标签', '300-500 条弱标注 + 人工校验'],
    ['图结构无增益', '图用于 hard negative / regularization，不盲目 message passing'],
  ];
  addBox(slide, '风险', 88, 90, 300, 45, { fill: BLUE, line: BLUE, color: 'white', size: 18, bold: true, radius: 0 });
  addBox(slide, '应对策略', 388, 90, 470, 45, { fill: BLUE, line: BLUE, color: 'white', size: 18, bold: true, radius: 0 });
  rows.forEach((r, i) => {
    const yy = 135 + i * 75;
    addBox(slide, r[0], 88, yy, 300, 75, {
      fill: i % 2 ? 'white' : '#F7FBFF',
      line: '#C8D4DF',
      size: 18,
      bold: true,
      radius: 0,
    });
    addBox(slide, r[1], 388, yy, 470, 75, {
      fill: i % 2 ? 'white' : '#F7FBFF',
      line: '#C8D4DF',
      size: 17,
      radius: 0,
    });
  });
}

// 12. Summary
{
  const slide = presentation.slides.getItem(11);
  updateTextOnSlide(slide, '谢谢', '总结与下一步', {
    fontSize: 36,
    bold: true,
    color: '#111111',
    alignment: 'center',
  });
  updateTextOnSlide(slide, 'THANK', '新版研究主线已经确定，旧实验降级为 pilot', {
    fontSize: 18,
    color: '#333333',
    alignment: 'center',
  });
  addBulletList(slide, [
    '围绕“对齐、缺失、解释”三个可信问题组织论文贡献',
    'ScienceQA 诊断支持 structured missingness / MNAR 初步假设',
    '下一步推进 missing type 标注、RC1 baseline 和 RC3 解释评测集',
  ], 210, 340, 560, 42, 18);
}

for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `final-slide-${String(index + 1).padStart(2, '0')}`;
  const png = await presentation.export({ slide, format: 'png', scale: 1 });
  await fs.writeFile(path.join(previewDir, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: 'layout' });
  await fs.writeFile(path.join(layoutDir, `${stem}.layout.json`), await layout.text());
}

const montage = await presentation.export({ format: 'webp', montage: true, scale: 1 });
await fs.writeFile(path.join(previewDir, 'final-montage.webp'), new Uint8Array(await montage.arrayBuffer()));
const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);
console.log(finalPptx);
