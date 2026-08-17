import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = "C:\\Users\\miste\\OneDrive\\Documentos\\minecraft_IA_Algorithms";
const BUILD = path.join(ROOT, "work", "presentation-v2");
const OUT = path.join(ROOT, "outputs", "apresentacao_ia_q_learning_parkour.pptx");
const HERO = path.join(ROOT, "work", "presentation-build", "parkour-hero.png");

const W = 1280;
const H = 720;
const M = 56;
const COLORS = {
  canvas: "#FFFFFF",
  ink: "#000000",
  muted: "#5B6472",
  panel: "#EDEDED",
  panel2: "#F6F7F9",
  rule: "#B8BCC4",
  accent: "#6DCBF4",
  accentStrong: "#3D8DFF",
  accentPale: "#DFF4FD",
  dark: "#111827",
  white: "#FFFFFF",
};

const presentation = Presentation.create({ slideSize: { width: W, height: H } });

function addText(slide, name, text, box, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: box,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: 24,
    typeface: "Arial",
    color: COLORS.ink,
    verticalAlignment: "top",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
    ...style,
  };
  return shape;
}

function addBox(slide, name, box, fill = COLORS.panel, line = null, radius = 0) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    name,
    position: box,
    fill,
    line: line || { style: "solid", fill: "none", width: 0 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function addRule(slide, name, x, y, width, color = COLORS.rule, thickness = 1) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width, height: thickness },
    fill: color,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function addTitle(slide, title, number, section) {
  addText(slide, `section-${number}`, section.toUpperCase(),
    { left: M, top: 28, width: 360, height: 24 },
    { fontSize: 16, bold: true, color: COLORS.accentStrong });
  addText(slide, `title-${number}`, title,
    { left: M, top: 62, width: 1168, height: 76 },
    { fontSize: 46, bold: true, lineSpacing: 0.9, autoFit: "none" });
  addText(slide, `page-${number}`, String(number).padStart(2, "0"),
    { left: 1178, top: 674, width: 46, height: 20 },
    { fontSize: 14, color: COLORS.muted, alignment: "right" });
}

function addNotes(slide, speaker, timing, lines, sources) {
  const sourceLines = sources.map((source) => `- ${source}`).join("\n");
  const notes = [
    `Responsável sugerido: ${speaker}`,
    `Tempo: ${timing}`,
    "",
    ...lines,
    "",
    "[Sources]",
    sourceLines,
    "[/Sources]",
  ].join("\n");
  slide.speakerNotes.textFrame.setText(notes);
  slide.speakerNotes.setVisible(true);
}

function addBulletList(slide, name, items, box, style = {}) {
  const shape = addText(slide, name, "", box, {
    fontSize: 23,
    lineSpacing: 1.08,
    ...style,
  });
  shape.text = items.map((item) => ({
    bulletCharacter: "•",
    marginLeft: 24,
    indent: -14,
    spaceAfter: 900,
    runs: [item],
  }));
  return shape;
}

function addMetric(slide, x, stat, label, description, index) {
  addBox(slide, `metric-panel-${index}`, { left: x, top: 304, width: 354, height: 304 }, COLORS.panel2);
  addText(slide, `metric-stat-${index}`, stat,
    { left: x + 28, top: 342, width: 298, height: 92 },
    { fontSize: 64, bold: true, color: COLORS.accentStrong, autoFit: "none" });
  addText(slide, `metric-label-${index}`, label,
    { left: x + 28, top: 449, width: 298, height: 42 },
    { fontSize: 27, bold: true, autoFit: "none" });
  addText(slide, `metric-desc-${index}`, description,
    { left: x + 28, top: 507, width: 298, height: 72 },
    { fontSize: 19, color: COLORS.muted, lineSpacing: 1.08 });
}

// 1 — Capa: composição baseada no layout 08 (meio texto, meio imagem).
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  const heroBytes = await fs.readFile(HERO);
  addText(slide, "cover-eyebrow", "INTRODUÇÃO À INTELIGÊNCIA ARTIFICIAL",
    { left: M, top: 54, width: 540, height: 28 },
    { fontSize: 17, bold: true, color: COLORS.accentStrong });
  addText(slide, "cover-title", "Q-Learning para\ncontrole de\nparkour",
    { left: M, top: 130, width: 540, height: 250 },
    { fontSize: 64, bold: true, lineSpacing: 0.86, autoFit: "none" });
  addText(slide, "cover-subtitle", "Aprendizado por reforço tabular em um ambiente 3D, com estados, ações e recompensas.",
    { left: M, top: 418, width: 520, height: 112 },
    { fontSize: 25, color: COLORS.muted, lineSpacing: 1.08 });
  addRule(slide, "cover-accent", M, 574, 144, COLORS.accentStrong, 6);
  addText(slide, "cover-scope", "Minecraft é apenas o ambiente experimental; o foco é a IA.",
    { left: M, top: 598, width: 520, height: 54 },
    { fontSize: 18, color: COLORS.muted });
  slide.images.add({
    blob: heroBytes.buffer.slice(heroBytes.byteOffset, heroBytes.byteOffset + heroBytes.byteLength),
    contentType: "image/png",
    alt: "Bot voxel saltando entre plataformas de parkour com partículas azuis de aprendizado",
    fit: "cover",
    position: { left: 658, top: 42, width: 582, height: 588 },
    geometry: "roundRect",
    borderRadius: 18,
  });
  addNotes(slide, "Integrante 1", "0min30s", [
    "Abrir com a pergunta: como um agente aprende quando andar, correr ou pular sem receber uma regra pronta para cada obstáculo?",
    "Definir Minecraft em uma frase: é apenas o ambiente 3D que fornece física, observações e consequências das ações.",
    "Antecipar a ideia central: modelamos o problema como aprendizado por reforço tabular e atualizamos a tabela Q a cada experiência.",
  ], [
    "README.md",
    "config/cenarios/labirinto_parkours.json",
    "Imagem: OpenAI ImageGen; prompt registrado em work/presentation-build/source-notes.txt",
  ]);
}

// 2 — Formulação do problema de IA como decisão sequencial.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "O parkour é um problema de decisão sequencial", 2, "Problema de IA");
  addText(slide, "problem-claim", "Cada ação altera o próximo\nestado do agente.",
    { left: M, top: 190, width: 520, height: 120 },
    { fontSize: 39, bold: true, lineSpacing: 0.92, autoFit: "none" });
  addBulletList(slide, "problem-bullets", [
    "não há uma regra fixa para cada salto",
    "a decisão atual afeta as opções futuras",
    "o objetivo é maximizar a recompensa acumulada",
  ], { left: M, top: 344, width: 530, height: 235 });

  addText(slide, "agenda-title", "Elementos do aprendizado por reforço",
    { left: 666, top: 190, width: 500, height: 40 },
    { fontSize: 29, bold: true });
  const agenda = [
    ["Agente", "bot"],
    ["Ambiente", "mundo 3D"],
    ["Política", "ε-greedy"],
    ["Objetivo", "max Σr"],
  ];
  agenda.forEach(([label, time], i) => {
    const y = 252 + i * 78;
    addRule(slide, `agenda-rule-${i}`, 666, y + 54, 504, COLORS.rule, 1);
    addText(slide, `agenda-num-${i}`, `0${i + 1}`,
      { left: 666, top: y, width: 54, height: 34 },
      { fontSize: 20, bold: true, color: COLORS.accentStrong });
    addText(slide, `agenda-label-${i}`, label,
      { left: 732, top: y, width: 320, height: 36 },
      { fontSize: 24, bold: true });
    addText(slide, `agenda-time-${i}`, time,
      { left: 1070, top: y, width: 100, height: 36 },
      { fontSize: 21, color: COLORS.muted, alignment: "right" });
  });
  addNotes(slide, "Integrante 1", "1min10s", [
    "Definir o problema como controle sequencial: o agente observa, age, recebe uma consequência e chega a uma nova situação.",
    "Explicar os quatro elementos da direita. A política é epsilon-greedy e o objetivo é maximizar a soma de recompensas ao longo do episódio.",
    "Evitar explicar mecânicas do jogo. Para a disciplina, basta dizer que o ambiente aplica física e informa posição e velocidade.",
  ], [
    "docs/GUIA_Q_LEARNING.md",
    "docs/COMO_O_PROJETO_FUNCIONA.md",
  ]);
}

// 3 — Pipeline de conversão do percurso para uma representação compreensível pela IA.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "Como o percurso 3D vira entrada para o agente", 3, "Representação do ambiente");
  addText(slide, "tracks-intro", "A geometria é convertida uma vez; durante o treino, posição e velocidade continuam vindo do ambiente real.",
    { left: M, top: 146, width: 820, height: 38 },
    { fontSize: 23, color: COLORS.muted });
  addRule(slide, "track-line", 86, 342, 1045, COLORS.ink, 2);
  const tracks = [
    { x: 86, n: "01", title: "Ler o mundo", body: "Arquivos do mapa → blocos\ne caixas de colisão" },
    { x: 486, n: "02", title: "Normalizar", body: "Rotação + translação:\nmeta sempre em +progresso" },
    { x: 886, n: "03", title: "Discretizar", body: "4 células à frente →\níndice de 0 a 3.455" },
  ];
  tracks.forEach((t, i) => {
    addBox(slide, `track-dot-${i}`, { left: t.x - 8, top: 333, width: 18, height: 18 }, i === 2 ? COLORS.accentStrong : COLORS.ink, null, 9);
    addText(slide, `track-num-${i}`, t.n,
      { left: t.x, top: 260, width: 70, height: 34 },
      { fontSize: 19, bold: true, color: COLORS.accentStrong });
    addText(slide, `track-title-${i}`, t.title,
      { left: t.x, top: 386, width: 260, height: 44 },
      { fontSize: 30, bold: true });
    addText(slide, `track-body-${i}`, t.body,
      { left: t.x, top: 448, width: 270, height: 86 },
      { fontSize: 23, color: COLORS.muted, lineSpacing: 1.05 });
  });
  addText(slide, "track-takeaway", "O algoritmo não recebe “blocos”: recebe um estado compacto com significado físico.",
    { left: M, top: 600, width: 1040, height: 40 },
    { fontSize: 25, bold: true });
  addNotes(slide, "Integrante 2", "1min30s", [
    "Etapa 1: a ferramenta lê os arquivos regionais do mundo e traduz cada bloco para uma caixa de colisão com altura e largura.",
    "Etapa 2: início e fim definem uma transformação de coordenadas. Qualquer direção real vira lateral, altura e progresso crescente.",
    "Etapa 3: o estado consulta apoios nas quatro células seguintes e combina essa leitura com altura relativa, posição no bloco, fase vertical e velocidade.",
    "O JSON é um mapa estático da geometria; a dinâmica do movimento continua sendo observada diretamente no ambiente durante cada ação.",
  ], [
    "tools/mapear_percurso.py",
    "tools/nbt.py",
    "tools/blocos.py",
    "src/parkour/coordenadas.py",
    "src/parkour/estado.py",
  ]);
}

// 4 — Estado, ações e recompensa: três regiões conectadas.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "Estado, ações e recompensa definem o problema", 4, "Modelagem");
  // Conectores primeiro, atrás dos nós.
  addBox(slide, "model-arrow-1", { left: 383, top: 337, width: 80, height: 20 }, COLORS.accentStrong);
  addBox(slide, "model-arrowhead-1", { left: 451, top: 326, width: 34, height: 42 }, COLORS.accentStrong);
  addBox(slide, "model-arrow-2", { left: 794, top: 337, width: 80, height: 20 }, COLORS.accentStrong);
  addBox(slide, "model-arrowhead-2", { left: 862, top: 326, width: 34, height: 42 }, COLORS.accentStrong);
  const cols = [
    { x: 56, title: "Estado", big: "3.456", unit: "situações", body: "Piso nas 4 células seguintes\nAltura do apoio\nFase do salto e velocidade" },
    { x: 468, title: "Ações", big: "4", unit: "controles", body: "Andar\nCorrer\nCorrer + pular\nAndar + pular" },
    { x: 880, title: "Recompensa", big: "+20", unit: "ao chegar", body: "+1 × avanço\n−0,02 por decisão\n−10 por queda ou trava" },
  ];
  cols.forEach((c, i) => {
    addBox(slide, `model-panel-${i}`, { left: c.x, top: 202, width: 344, height: 390 }, i === 1 ? COLORS.accentPale : COLORS.panel2);
    addText(slide, `model-title-${i}`, c.title,
      { left: c.x + 28, top: 230, width: 288, height: 44 },
      { fontSize: 28, bold: true });
    addText(slide, `model-big-${i}`, c.big,
      { left: c.x + 28, top: 286, width: 288, height: 75 },
      { fontSize: 53, bold: true, color: COLORS.accentStrong, autoFit: "none" });
    addText(slide, `model-unit-${i}`, c.unit,
      { left: c.x + 28, top: 363, width: 288, height: 32 },
      { fontSize: 20, color: COLORS.muted });
    addText(slide, `model-body-${i}`, c.body,
      { left: c.x + 28, top: 424, width: 288, height: 138 },
      { fontSize: 21, lineSpacing: 1.12 });
  });
  addNotes(slide, "Integrante 2", "1min35s", [
    "Explicar que Q-Learning tabular exige um índice inteiro de estado.",
    "O modo piso combina quatro bits de apoio, seis classes de altura, posição no bloco, fase vertical e faixa de velocidade: 16 × 6 × 4 × 3 × 3 = 3.456.",
    "As quatro ações são suficientes para o corredor reto e duram quatro ticks, aproximadamente 200 ms.",
    "A recompensa usa progresso líquido para evitar ganhar pontos oscilando para frente e para trás; o detalhe completo aparece no slide 8.",
  ], [
    "src/parkour/estado.py",
    "src/parkour/acoes.py",
    "src/parkour/recompensa.py",
    "config/parkour.json",
  ]);
}

// 5 — Equação e exploração: composição em duas colunas baseada no layout 05.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "A tabela Q melhora a ação a cada experiência", 5, "Algoritmo e parâmetros");
  addBox(slide, "bellman-panel", { left: M, top: 194, width: 566, height: 374 }, COLORS.panel2);
  addText(slide, "bellman-label", "ATUALIZAÇÃO DE BELLMAN",
    { left: 86, top: 226, width: 460, height: 28 },
    { fontSize: 17, bold: true, color: COLORS.accentStrong });
  addText(slide, "bellman-equation", "Q(s,a) ← Q(s,a) + α ·\n[r + γ · max Q(s′,a′) − Q(s,a)]",
    { left: 86, top: 296, width: 500, height: 130 },
    { fontSize: 33, bold: true, typeface: "Arial", lineSpacing: 1.12, autoFit: "none" });
  addText(slide, "bellman-params", "α = 0,20     γ = 0,97",
    { left: 86, top: 472, width: 470, height: 42 },
    { fontSize: 25, color: COLORS.muted });

  addText(slide, "epsilon-title", "Parâmetros usados",
    { left: 676, top: 202, width: 500, height: 48 },
    { fontSize: 31, bold: true });
  addText(slide, "epsilon-big", "ε: 1,00 → 0,05",
    { left: 676, top: 282, width: 500, height: 74 },
    { fontSize: 48, bold: true, color: COLORS.accentStrong, autoFit: "none" });
  addBulletList(slide, "epsilon-bullets", [
    "α = 0,20  ·  taxa de aprendizado",
    "γ = 0,97  ·  desconto do futuro",
    "ε ← max(0,05; ε × 0,9995) após cada episódio",
    "ε = 0 durante a avaliação da política",
  ], { left: 676, top: 378, width: 500, height: 220 }, { fontSize: 21 });
  addNotes(slide, "Integrante 2", "1min35s", [
    "Ler a equação em linguagem simples: comparar o valor atual com a recompensa imediata mais o melhor futuro conhecido.",
    "Destacar que α controla quanto a experiência nova corrige a tabela e γ valoriza consequências futuras.",
    "Explicar epsilon-greedy: com probabilidade epsilon escolhemos uma ação aleatória; caso contrário usamos a melhor ação conhecida.",
    "Relacionar os valores: alfa 0,20 evita substituir completamente o passado; gama 0,97 valoriza chegar à meta; o decaimento reduz a exploração lentamente.",
  ], [
    "src/parkour/q_learning.py",
    "config/parkour.json",
    "docs/GUIA_Q_LEARNING.md",
  ]);
}

// 6 — Fluxo completo: diagrama nativo, conectores antes dos nós.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "Cada episódio repete o ciclo do Q-Learning", 6, "Fluxo de aprendizagem");
  const xs = [56, 292, 528, 764, 1000];
  for (let i = 0; i < 4; i += 1) {
    addBox(slide, `cycle-link-${i}`, { left: xs[i] + 180, top: 352, width: 46, height: 12 }, COLORS.accentStrong);
    addBox(slide, `cycle-head-${i}`, { left: xs[i] + 216, top: 342, width: 24, height: 32 }, COLORS.accentStrong);
  }
  const steps = [
    ["1", "Observar s", "posição, apoio e velocidade"],
    ["2", "Escolher a", "política epsilon-greedy"],
    ["3", "Executar", "ação por 4 ticks"],
    ["4", "Receber", "recompensa r e estado s′"],
    ["5", "Atualizar Q", "equação de Bellman"],
  ];
  steps.forEach(([n, title, body], i) => {
    addBox(slide, `cycle-node-${i}`, { left: xs[i], top: 260, width: 190, height: 206 }, i === 4 ? COLORS.accentPale : COLORS.panel2);
    addText(slide, `cycle-n-${i}`, n,
      { left: xs[i] + 20, top: 280, width: 40, height: 34 },
      { fontSize: 20, bold: true, color: COLORS.accentStrong });
    addText(slide, `cycle-title-${i}`, title,
      { left: xs[i] + 20, top: 332, width: 150, height: 40 },
      { fontSize: 25, bold: true });
    addText(slide, `cycle-body-${i}`, body,
      { left: xs[i] + 20, top: 390, width: 150, height: 58 },
      { fontSize: 18, color: COLORS.muted, lineSpacing: 1.05 });
  });
  addText(slide, "cycle-footer", "Meta, queda, travamento ou 80 decisões encerram o episódio; então ε diminui.",
    { left: 140, top: 550, width: 990, height: 48 },
    { fontSize: 25, bold: true, alignment: "center" });
  addNotes(slide, "Integrante 2", "1min15s", [
    "Percorrer o fluxo usando a notação padrão de aprendizado por reforço: estado s, ação a, recompensa r e próximo estado s linha.",
    "A ação dura quatro ticks, aproximadamente 200 ms. Isso reduz a frequência de decisão sem eliminar o controle do salto.",
    "Nos três percursos deste experimento, o limite é 80 decisões. Ao final, a tabela e o histórico podem ser salvos e epsilon diminui.",
  ], [
    "docs/COMO_O_PROJETO_FUNCIONA.md",
    "src/parkour/ambiente_mc.py",
    "src/parkour/treinar.py",
  ]);
}

// 7 — Código simples: composição em duas colunas baseada no layout 05.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "A implementação separa algoritmo e ambiente", 7, "Implementação");
  addText(slide, "impl-title", "Núcleo do aprendizado",
    { left: M, top: 182, width: 510, height: 44 },
    { fontSize: 29, bold: true });
  addBox(slide, "code-panel", { left: M, top: 244, width: 560, height: 326 }, COLORS.dark, null, 12);
  const code = [
    "alvo = recompensa",
    "if not terminou:",
    "    alvo += gama * melhor_futuro",
    "",
    "erro = alvo - valor_atual",
    "Q[estado][acao] += alfa * erro",
  ].join("\n");
  addText(slide, "code-text", code,
    { left: 84, top: 278, width: 500, height: 250 },
    { fontSize: 22, typeface: "Consolas", color: COLORS.white, lineSpacing: 1.2, autoFit: "none" });

  addText(slide, "layers-title", "Módulos ligados aos conceitos",
    { left: 674, top: 182, width: 500, height: 44 },
    { fontSize: 29, bold: true });
  addBulletList(slide, "layers-bullets", [
    "q_learning.py: política epsilon-greedy e Bellman",
    "estado.py: estado contínuo → índice discreto",
    "recompensa.py: objetivo e penalidades",
    "treinar.py: interação (s, a, r, s′) por episódio",
  ], { left: 674, top: 254, width: 500, height: 286 }, { fontSize: 22 });
  addNotes(slide, "Integrante 3", "1min15s", [
    "Mostrar que a equação cabe em poucas linhas; a maior dificuldade não é a fórmula, mas definir boas observações e recompensas.",
    "O desacoplamento permite testar Bellman, persistência, estado e recompensa sem abrir o ambiente 3D.",
    "O adaptador ambiente_mc.py faz a ponte com a física real, mas não altera a lógica do Q-Learning.",
  ], [
    "src/parkour/q_learning.py",
    "src/parkour/ambiente_mc.py",
    "src/parkour/estado.py",
    "src/parkour/treinar.py",
  ]);
}

// 8 — Projeto da função de recompensa.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "Recompensa define o comportamento desejado", 8, "Modelagem do objetivo");
  addText(slide, "parallel-equation", "r = Δprogresso − 0,02",
    { left: M, top: 188, width: 600, height: 74 },
    { fontSize: 46, bold: true, autoFit: "none" });
  addText(slide, "parallel-example", "+20 meta   ·   −10 queda/trava",
    { left: M, top: 278, width: 600, height: 48 },
    { fontSize: 28, color: COLORS.accentStrong, bold: true });
  addRule(slide, "parallel-divider", 642, 178, 2, COLORS.rule, 390);
  addText(slide, "shared-title", "O que o sinal ensina",
    { left: 688, top: 188, width: 480, height: 52 },
    { fontSize: 31, bold: true });
  addBulletList(slide, "parallel-bullets", [
    "avançar e pousar: reforço positivo",
    "demorar: custo em cada decisão",
    "ficar parado: penalidade extra de −0,05",
    "queda, travamento e meta: sinais terminais",
  ], { left: 688, top: 276, width: 486, height: 274 }, { fontSize: 22 });
  addBox(slide, "parallel-callout", { left: M, top: 390, width: 544, height: 160 }, COLORS.accentPale);
  addText(slide, "parallel-callout-text", "Progresso líquido impede acumular recompensa oscilando no mesmo lugar.",
    { left: 88, top: 426, width: 480, height: 88 },
    { fontSize: 27, bold: true, lineSpacing: 1.05 });
  addNotes(slide, "Integrante 3", "1min10s", [
    "Explicar que a recompensa é a especificação do objetivo: o agente não sabe o que é um salto bonito, apenas tenta maximizar retorno.",
    "O termo de progresso é deslocamento líquido. Se o agente avança e volta, o ganho é cancelado; isso reduz reward hacking.",
    "No cenário usado, progresso só é confirmado após pousar em um apoio mapeado, evitando premiar um salto que termina em queda.",
  ], [
    "src/parkour/recompensa.py",
    "src/parkour/ambiente_mc.py",
    "config/parkour.json",
    "config/cenarios/labirinto_parkours.json",
  ]);
}

// 9 — Resultados comprovados: composição métrica baseada no layout 19.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "O treino salvo mostra evolução", 9, "Resultados");
  addText(slide, "results-qualifier", "Execução no frente_1: 70 bots × 50 rodadas = 3.500 episódios, todos registrados com ε = 0,05.",
    { left: M, top: 146, width: 1120, height: 62 },
    { fontSize: 23, color: COLORS.muted });
  addMetric(slide, 56, "3.500", "episódios registrados", "O arquivo contém somente a execução mais recente.", 1);
  addMetric(slide, 463, "7,20%", "chegadas no treino", "252 episódios terminaram na meta, ainda sob exploração.", 2);
  addMetric(slide, 870, "10,4%", "nos últimos 1.000", "Nos primeiros 1.000 registros, a taxa era 6,00%.", 3);
  addNotes(slide, "Integrante 4", "1min20s", [
    "O treino mais recente do frente_1 usou 70 bots por 50 rodadas: 70 × 50 = 3.500 episódios, numerados de 1 a 3.500.",
    "Nesse arquivo, 252 episódios chegaram à meta: taxa de 7,20% durante o treino.",
    "Nos primeiros 1.000 registros foram 60 chegadas, ou 6,00%; nos últimos 1.000 foram 104, ou 10,40%.",
    "Essas taxas são do treino com epsilon-greedy. Elas evidenciam melhora, mas não substituem uma avaliação separada com epsilon zero.",
  ], [
    "Informação do grupo: execução com 70 bots × 50 rodadas",
    "resultados/modelos/q_learning_labirinto_parkours_frente_1_acoes_v2_estado_v2_recompensa_v2_resultado.csv",
  ]);
}

// 10 — Limitações e próximos experimentos: duas colunas baseada no layout 05.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addTitle(slide, "O modelo foi treinado; falta avaliar a política", 10, "Avaliação");
  addText(slide, "limits-left-title", "Evidências já salvas",
    { left: M, top: 190, width: 520, height: 44 },
    { fontSize: 30, bold: true });
  addBulletList(slide, "limits-left", [
    "ε permaneceu em 0,05 no histórico limpo",
    "retorno médio: 4,34 → 9,84",
    "progresso válido médio: 26,3% → 34,3%",
  ], { left: M, top: 260, width: 520, height: 250 }, { fontSize: 22 });
  addText(slide, "limits-right-title", "Avaliação necessária",
    { left: 674, top: 190, width: 520, height: 44 },
    { fontSize: 30, bold: true, color: COLORS.accentStrong });
  addBulletList(slide, "limits-right", [
    "executar o modelo salvo com ε = 0",
    "repetir várias tentativas sem atualizar Q",
    "medir chegada, retorno e passos até a meta",
  ], { left: 674, top: 260, width: 520, height: 250 }, { fontSize: 22 });
  addText(slide, "limits-bottom", "Taxa durante treino com exploração ≠ desempenho final da política.",
    { left: 150, top: 575, width: 980, height: 44 },
    { fontSize: 27, bold: true, alignment: "center" });
  addNotes(slide, "Integrante 4", "1min15s", [
    "Comparando os primeiros e os últimos 1.000 episódios, o retorno médio aumentou de 4,34 para 9,84 e o progresso válido de 26,3% para 34,3%.",
    "O CSV não possui linhas com fase de avaliação; todas as 3.500 linhas são de treino com epsilon 0,05.",
    "O protocolo agora é carregar a tabela, desligar exploração e aprendizado, repetir várias execuções e medir chegada, retorno e passos.",
  ], [
    "resultados/modelos/q_learning_labirinto_parkours_frente_1_acoes_v2_estado_v2_recompensa_v2_resultado.csv",
    "src/parkour/q_learning.py",
    "src/parkour/treinar.py",
  ]);
}

// 11 — Fechamento: composição esparsa baseada no layout 26.
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.canvas;
  addText(slide, "close-eyebrow", "CONCLUSÃO",
    { left: M, top: 52, width: 300, height: 28 },
    { fontSize: 17, bold: true, color: COLORS.accentStrong });
  addText(slide, "close-title", "A IA aprende uma política porque\ncada ação produz estado, recompensa\ne uma correção na tabela Q.",
    { left: M, top: 140, width: 1120, height: 230 },
    { fontSize: 55, bold: true, lineSpacing: 0.93, autoFit: "none" });
  addRule(slide, "close-rule", M, 426, 1168, COLORS.ink, 2);
  const closing = [
    ["Representação", "O mapa 3D é normalizado e codificado em 3.456 estados."],
    ["Aprendizado", "Bellman, ε-greedy e recompensa transformam experiência em política."],
    ["Avaliação", "Carregar o modelo salvo e medir a política com ε = 0."],
  ];
  closing.forEach(([label, body], i) => {
    const x = M + i * 397;
    addText(slide, `close-label-${i}`, label,
      { left: x, top: 474, width: 350, height: 34 },
      { fontSize: 20, bold: true, color: COLORS.accentStrong });
    addText(slide, `close-body-${i}`, body,
      { left: x, top: 524, width: 350, height: 88 },
      { fontSize: 21, color: COLORS.muted, lineSpacing: 1.08 });
  });
  addNotes(slide, "Integrante 4", "0min45s", [
    "Retomar a pergunta inicial e responder: o agente aprende porque cada transição atualiza o valor de uma ação naquele estado.",
    "Reforçar que a contribuição central é a modelagem: converter geometria e movimento contínuos em uma representação pequena o bastante para Q-Learning tabular.",
    "Encerrar com honestidade experimental: houve treino e evolução mensurável; a política ainda precisa de uma avaliação separada.",
  ], [
    "Síntese de README.md e dos módulos src/parkour/",
  ]);
}

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

await fs.mkdir(path.join(BUILD, "rendered"), { recursive: true });
await fs.mkdir(path.dirname(OUT), { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(BUILD, "rendered", `${stem}.png`),
    await presentation.export({ slide, format: "png", scale: 1 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(BUILD, "rendered", `${stem}.layout.json`), await layout.text());
}

await writeBlob(path.join(BUILD, "deck-montage.webp"),
  await presentation.export({ format: "webp", montage: true, scale: 1 }));

const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,image,notes",
  maxChars: 30000,
});
await fs.writeFile(path.join(BUILD, "inspection.ndjson"), inspection.ndjson);

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(OUT);
console.log(`Deck exported to ${OUT}`);
