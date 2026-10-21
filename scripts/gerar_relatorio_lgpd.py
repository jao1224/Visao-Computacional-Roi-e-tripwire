#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do Relatório de Conformidade LGPD — Visão Computacional para Hotelaria.

Ferramenta de DOCUMENTACAO (fora do pipeline de producao): le o estado auditavel
do projeto (roadmap, requisitos, parecer legal, suite de testes) e gera um PDF
pronto para apresentacao a gestao de projeto / encarregado (DPO).

Nao faz parte do runtime do produto:
  - nao importa nenhum modulo do pipeline (main.py, zona.py, overlay.py, ...);
  - nao le nem grava frames, imagens ou videos (apenas texto do repositorio);
  - nao altera requirements.txt (reportlab e uma dependencia OPCIONAL de geracao).

Uso (ambiente com reportlab instalado):
    python3 -m venv .venv-relatorio
    ./.venv-relatorio/bin/pip install reportlab
    ./.venv-relatorio/bin/python scripts/gerar_relatorio_lgpd.py

Saida: docs/relatorios/RELATORIO-CONFORMIDADE-LGPD-v1.0-<AAAA-MM-DD>.pdf
"""
import os
import sys
from datetime import date

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------- paleta
PRIMARY = HexColor('#15304F')
ACCENT = HexColor('#0E7C7B')
OK = HexColor('#2D6A4F')
WARN = HexColor('#A85B13')
DANGER = HexColor('#9B2226')
LIGHT = HexColor('#EEF3F8')
LIGHT2 = HexColor('#F7F9FB')
BORDER = HexColor('#C3D0DC')
GREY = HexColor('#55636F')

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME = 'RELATORIO-CONFORMIDADE-LGPD-v1.0-%s.pdf' % date.today().strftime('%Y-%m-%d')
OUT = os.path.join(RAIZ, 'docs', 'relatorios', NOME)

# ---------------------------------------------------------------- estilos
ss = getSampleStyleSheet()

H1 = ParagraphStyle('H1', parent=ss['Heading1'], fontName='Helvetica-Bold',
                    fontSize=15, leading=19, textColor=PRIMARY, spaceBefore=14,
                    spaceAfter=8, alignment=TA_LEFT)
H2 = ParagraphStyle('H2', parent=ss['Heading2'], fontName='Helvetica-Bold',
                    fontSize=11.2, leading=14, textColor=ACCENT, spaceBefore=11,
                    spaceAfter=5)
H3 = ParagraphStyle('H3', parent=ss['Heading3'], fontName='Helvetica-Bold',
                    fontSize=9.6, leading=12.5, textColor=PRIMARY, spaceBefore=8,
                    spaceAfter=3)
P = ParagraphStyle('P', parent=ss['BodyText'], fontName='Helvetica', fontSize=9.2,
                   leading=13.2, textColor=HexColor('#1B2733'), alignment=TA_JUSTIFY,
                   spaceAfter=6)
PSM = ParagraphStyle('PSM', parent=P, fontSize=8.4, leading=11.6)
BULLET = ParagraphStyle('BULLET', parent=P, leftIndent=13, bulletIndent=3,
                        spaceAfter=3, alignment=TA_LEFT)
CELL = ParagraphStyle('CELL', parent=PSM, alignment=TA_LEFT, spaceAfter=0)
CELLB = ParagraphStyle('CELLB', parent=CELL, fontName='Helvetica-Bold')
CELLH = ParagraphStyle('CELLH', parent=CELL, fontName='Helvetica-Bold',
                       textColor=colors.white)
SMALLC = ParagraphStyle('SMALLC', parent=PSM, fontSize=7.5, leading=9.8,
                        textColor=GREY)
MONO = ParagraphStyle('MONO', parent=PSM, fontName='Courier', fontSize=8,
                      textColor=HexColor('#1B2733'))
CAPTION = ParagraphStyle('CAPTION', parent=SMALLC, spaceBefore=3, spaceAfter=9)

styles = {'H1': H1, 'H2': H2, 'H3': H3}

# ---------------------------------------------------------------- helpers
def h1(t):
    return Paragraph(t, H1)

def h2(t):
    return Paragraph(t, H2)

def h3(t):
    return Paragraph(t, H3)

def p(t, style=P):
    return Paragraph(t, style)

def bullet(t, style=BULLET):
    return Paragraph(t, style, bulletText='•')

def num(n, t, style=BULLET):
    return Paragraph(t, style, bulletText='%s.' % n)

def spacer(h=5):
    return Spacer(1, h)

def hr(color=BORDER, width=0.7):
    t = Table([['']], colWidths=[0], rowHeights=[0.6])
    t.setStyle(TableStyle([('LINEABOVE', (0, 0), (-1, 0), width, color)]))
    return t

def callout(title, body, accent=ACCENT, bg=LIGHT):
    inner = []
    if title:
        inner.append(Paragraph('<b>%s</b>' % title,
                               ParagraphStyle('ct', parent=P, fontSize=9.4,
                                              textColor=accent, alignment=TA_LEFT,
                                              spaceAfter=3)))
    inner.append(Paragraph(body, ParagraphStyle('cb', parent=P, fontSize=9.2,
                                                leading=13.2, spaceAfter=0)))
    t = Table([[inner]], colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('LINEBEFORE', (0, 0), (0, -1), 2.6, accent),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return t

def _cell(v, style=CELL):
    if isinstance(v, Paragraph):
        return v
    return Paragraph(str(v), style)

def mk_table(header, rows, widths, align=None, fs=8.4, head_bg=PRIMARY,
             zebra=True, repeat=1, valign='TOP'):
    data = []
    if header:
        data.append([_cell(h, CELLH) for h in header])
    for r in rows:
        data.append([_cell(v) for v in r])
    t = Table(data, colWidths=widths, repeatRows=repeat, hAlign='LEFT')
    cmds = [
        ('FONTSIZE', (0, 0), (-1, -1), fs),
        ('LEADING', (0, 0), (-1, -1), fs + 3.2),
        ('VALIGN', (0, -1), (-1, -1), valign),
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
        ('BOX', (0, 0), (-1, -1), 0.9, PRIMARY),
        ('LEFTPADDING', (0, 0), (-1, -1), 4.5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4.5),
        ('TOPPADDING', (0, 0), (-1, -1), 3.4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.4),
    ]
    if header:
        cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), head_bg),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('LINEBELOW', (0, 0), (-1, 0), 0.9, PRIMARY),
        ]
    if zebra:
        base = 1 if header else 0
        for i in range(base, len(data)):
            if (i - base) % 2 == 1:
                cmds.append(('BACKGROUND', (0, i), (-1, i), LIGHT2))
    if align:
        for col, a in align.items():
            cmds.append(('ALIGN', (col, 0), (col, -1), a))
    t.setStyle(TableStyle(cmds))
    return t

def caption(txt):
    return Paragraph(txt, CAPTION)

def code_block(lines):
    inner = [[Paragraph(l if l else '&nbsp;', MONO)] for l in lines]
    t = Table(inner, colWidths=[170 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#F4F6F8')),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 1.6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.6),
    ]))
    return t

# ---------------------------------------------------------------- documento
class RelatorioDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        BaseDocTemplate.__init__(self, filename, **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      id='corpo')
        self.addPageTemplates([
            PageTemplate(id='capa', frames=[frame], onPage=self._capa_decor),
            PageTemplate(id='corpo', frames=[frame], onPage=self._corpo_decor),
        ])

    def _capa_decor(self, canv, doc):
        canv.saveState()
        canv.setFillColor(PRIMARY)
        canv.rect(0, A4[1] - 18 * mm, A4[0], 18 * mm, stroke=0, fill=1)
        canv.setFillColor(ACCENT)
        canv.rect(0, A4[1] - 19.6 * mm, A4[0], 1.6 * mm, stroke=0, fill=1)
        canv.setFillColor(PRIMARY)
        canv.rect(0, 0, A4[0], 12 * mm, stroke=0, fill=1)
        canv.restoreState()

    def _corpo_decor(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(BORDER)
        canv.setLineWidth(0.5)
        y = A4[1] - 15 * mm
        canv.line(20 * mm, y, A4[0] - 20 * mm, y)
        canv.setFont('Helvetica', 7.6)
        canv.setFillColor(GREY)
        canv.drawString(20 * mm, y + 2.2 * mm,
                        'Relatório de Conformidade LGPD — Visão Computacional para Hotelaria (Analytics de Fluxo)')
        canv.drawRightString(A4[0] - 20 * mm, y + 2.2 * mm, 'Documento interno — Controller')
        # rodapé
        canv.setStrokeColor(BORDER)
        yf = 13 * mm
        canv.line(20 * mm, yf + 4.2 * mm, A4[0] - 20 * mm, yf + 4.2 * mm)
        canv.setFont('Helvetica', 7.6)
        canv.setFillColor(GREY)
        canv.drawString(20 * mm, yf,
                        'LTD-Parangaba · Projeto Visão Computacional Hotel · LGPD/MCI — %s'
                        % date.today().strftime('%d/%m/%Y'))
        canv.setFont('Helvetica-Bold', 8.4)
        canv.setFillColor(PRIMARY)
        canv.drawRightString(A4[0] - 20 * mm, yf, 'Página %d' % doc.page)
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            name = flowable.style.name
            text = flowable.getPlainText()
            if name == 'H1' and text != 'Índice':
                self.notify('TOCEntry', (0, text, self.page))
            elif name == 'H2':
                self.notify('TOCEntry', (1, text, self.page))


# ---------------------------------------------------------------- conteúdo
F = []          # flowables
A = F.append

DATA = date.today().strftime('%d/%m/%Y')

# =========================================================== CAPA
A(Spacer(1, 30 * mm))
A(Paragraph('RELATÓRIO TÉCNICO-JURÍDICO DE CONFORMIDADE',
            ParagraphStyle('eyebrow', fontName='Helvetica-Bold', fontSize=9.4,
                           textColor=ACCENT, spaceAfter=6)))
A(Paragraph('LGPD e Marco Civil da Internet',
            ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=26,
                           leading=29, textColor=PRIMARY, spaceAfter=4)))
A(Paragraph('Visão Computacional para Hotelaria — Analytics de Fluxo',
            ParagraphStyle('subtitle', fontName='Helvetica', fontSize=13,
                           leading=16, textColor=GREY, spaceAfter=14)))
A(hr(ACCENT, 1.6))
A(Spacer(1, 5 * mm))

ident = [
    ['Objeto do relatório',
     'Verificação da conformidade do sistema de visão computacional (contagem e ocupação '
     'por zona/ROI) com a Lei nº 13.709/2018 (LGPD) e a Lei nº 12.965/2014 (Marco Civil da Internet).'],
    ['Destinatário', 'Gestão de Projeto / Encarregado (DPO) — LTD-Parangaba'],
    ['Emitido por', 'Equipe de Engenharia de Visão Computacional (autor do sistema)'],
    ['Data de emissão', DATA],
    ['Versão', '1.0 — snapshot de progresso (Fases 1 e 2 concluídas)'],
    ['Base normativa', 'Lei nº 13.709/2018 (LGPD); Lei nº 12.965/2014 (Marco Civil); '
                       'Res. CD/ANPD nº 18/2024; Guia orientativo ANPD de 19/12/2024'],
    ['Base de evidências', 'Repositório Git, 81 commits; suíte automatizada com 33 testes '
                           'verdes; roadmap GSD de 9 fases; parecer interno de compliance'],
    ['Classificação', 'Uso interno do controlador. Não contém dado pessoal de hóspedes.'],
]
A(mk_table(None, ident, [38 * mm, 132 * mm], fs=8.6, zebra=True,
           head_bg=PRIMARY, repeat=0))
A(Spacer(1, 7 * mm))
A(callout('Como este documento foi produzido',
          'O relatório foi gerado com apoio do framework de planejamento <b>GSD</b> (Get Shit Done), '
          'que mantém o rastro entre <b>requisitos → roadmap → planos → implementação → testes → '
          'verificação legal</b>. Cada afirmação técnica deste relatório aponta para um arquivo, '
          'um teste ou um commit verificável no repositório. A auditoria legal que sustenta as '
          'conclusões está versionada em <i>.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md</i>.',
          accent=ACCENT, bg=LIGHT))
A(NextPageTemplate('corpo'))
A(PageBreak())

# =========================================================== ÍNDICE
A(h1('Índice'))
toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle('TOC0', fontName='Helvetica-Bold', fontSize=9.4, leading=15,
                   textColor=PRIMARY, spaceBefore=5),
    ParagraphStyle('TOC1', fontName='Helvetica', fontSize=8.8, leading=12.6,
                   textColor=GREY, leftIndent=10),
]
A(toc)
A(PageBreak())

# =========================================================== 1. SUMÁRIO EXECUTIVO
A(h1('1. Sumário Executivo'))

A(h2('1.1 Finalidade deste documento'))
A(p('Este relatório tem um único objetivo: permitir que a gestão de projeto avalie, com base em '
    'evidências verificáveis, se o sistema de visão computacional em desenvolvimento está em '
    'conformidade com a legislação brasileira de proteção de dados e de guarda de registros de '
    'aplicações, e o que ainda falta para que a operação com hóspedes reais possa ser iniciada.'))
A(p('O relatório cobre três dimensões: <b>(a) o que já existe e está testado</b>; <b>(b) o que está '
    'planejado para as fases seguintes</b>, com o respectivo marco de conformidade; e <b>(c) as '
    'lacunas e riscos residuais</b> que precisam ser fechados antes da entrada em produção.'))

A(h2('1.2 O que é o sistema'))
A(p('O sistema transforma câmeras de segurança convencionais de um hotel em sensores de negócio. '
    'Ele detecta <b>corpos</b> (não rostos) por visão computacional, contabiliza quantas pessoas '
    'ocupam cada zona demarcada (ROI) e, no futuro, calculará tempo de permanência e mapa de '
    'ocupação agregada. O resultado é <i>business intelligence</i> operacional — quantas pessoas estão '
    'no hall, no restaurante ou na recepção, agora e ao longo do dia — sem jamais identificar quem '
    'é quem.'))
A(callout('Regra de ouro do projeto (invariante em todas as 9 fases)',
          '<b>Saída exclusivamente agregada.</b> Nenhum dado por pessoa é gravado em nenhuma '
          'hipótese: nem imagem, nem ID de rastreamento, nem trajeto, nem perfil. Essa é a razão de '
          'o projeto ser defensável juridicamente (LGPD, art. 5º, XI e art. 12, caput) — e também '
          'a razão de ele ser tecnicamente mais simples de operar.',
          accent=OK, bg=HexColor('#EDF5F0')))

A(h2('1.3 Conclusão principal'))
A(callout('Parecer',
          '<b>SIM — o que está implementado está em conformidade com a LGPD e com o Marco Civil da '
          'Internet, e o desenho técnico das fases restantes foi construído para manter essa '
          'conformidade.</b><br/><br/>'
          'Não existe, no código atual, nenhum mecanismo capaz de identificar pessoas, guardar '
          'imagem de hóspede, reconstruir trajetórias ou associar pessoas entre câmeras. Essa '
          'afirmação não é uma declaração de boa-fé: ela é <b>verificada automaticamente por testes</b> '
          'que rodam em cada commit (seção 3.6) e por auditoria documental contra a Lei nº 13.709/2018 '
          '(seção 6).<br/><br/>'
          '<b>Porém, o sistema ainda NÃO pode ir para produção com hóspedes reais.</b> Faltam '
          'documentos e controles que são, por lei, responsabilidade do controlador (o hotel): '
          'RIPD, LIA, registro de operações (ROPA), encarregado publicado, aviso de monitoramento '
          'nas áreas, TTL de retenção, logs de acesso e plano de resposta a incidente. Todos estão '
          'previstos no roadmap (Fase 9, que funciona como <i>gate</i> formal) e detalhados na '
          'seção 7 deste relatório.',
          accent=OK, bg=HexColor('#EDF5F0')))

A(h2('1.4 Situação atual em números'))
A(mk_table(
    ['Indicador', 'Valor', 'Observação'],
    [['Fases do roadmap concluídas', '2 de 9 (22%)',
      'Fase 1 (pipeline single-câmera) e Fase 2 (contagem e ocupação por zona) concluídas e auditadas'],
     ['Requisitos v1 concluídos', '6 de 27 (22%)',
      'ING-01, ING-03, CNT-01, CNT-02, CNT-03 e CNT-04 — todos os requisitos de privacidade e de núcleo já entregues'],
     ['Testes automatizados', '33 testes, 100% verdes',
      'Suíte executada em ~10 s via <font face="Courier">./.venv/bin/python -m pytest</font>'],
     ['Linhas de código do produto', '608 linhas',
      'main.py (124), zona.py (313), overlay.py (129), rastreio.py (23), captura.py (19)'],
     ['Linhas de teste', '846 linhas', '7 arquivos de teste + conftest.py'],
     ['Commits no repositório', '81 commits', 'Commits atômicos, com documentação antes da implementação'],
     ['Documentos técnicos e legais', '10 documentos + 1 plano maestro',
      '<i>docs/DOCUMENTACAO_PROJETO_E_LGPD/</i> (docs 01 a 09 + README) e <i>docs/PLANO_V1_COMPLETO.md</i>'],
     ['Módulos de face / biometria / escrita de mídia', '<b>0</b>',
      'Verificado por varredura de tokens proibidos em todo o código de produto (teste automatizado)'],
     ['Arquivos de imagem/vídeo gerados pelo pipeline', '<b>0</b>',
      'Verificado por auditoria de disco antes/depois de executar o pipeline real (teste automatizado)'],
     ['Ocorrências de hóspede real tratadas', '<b>0</b>',
      'Invariante do roadmap: nenhum stream real antes do gate da Fase 9']],
    [58 * mm, 30 * mm, 82 * mm], fs=8.4))
A(caption('Tabela 1 — Indicadores de estado do projeto e de conformidade (fonte: repositório Git, '
          'suíte de testes e .planning/STATE.md).'))

A(h2('1.5 Os quatro vetores de risco e como foram neutralizados'))
A(mk_table(
    ['#', 'Vetor de risco (o que daria problema)', 'Base legal do risco', 'Tratamento implementado'],
    [['1', 'Identificar pessoas pelo rosto (facial recognition, embeddings)',
      'Art. 11 (dado sensível) — sem base legal para analytics; art. 52, II (multa de até 2% do '
      'faturamento, teto de R$ 50 milhões)',
      'Arquitetura sem qualquer módulo de face. Dependência <font face="Courier">opencv-python</font> '
      '(não <font face="Courier">opencv-contrib-python</font>) para não puxar <font face="Courier">cv2.face</font>. '
      'Teste automatizado varre o código de produto e falha se aparecer qualquer token de face/biometria.'],
     ['2', 'Guardar imagem, vídeo ou crop de hóspede em disco, log ou backup',
      'Art. 6º, II e III (necessidade e minimização); art. 48 (incidente)',
      'Frames existem apenas na RAM do processo e são descartados após a inferência. Não há '
      '<font face="Courier">imwrite</font>, <font face="Courier">VideoWriter</font> nem '
      '<font face="Courier">tofile</font> no código de produto. Teste executa o pipeline real e '
      'compara o inventário de arquivos de mídia antes e depois: zero arquivos novos.'],
     ['3', 'Reconstruir a rota ou o perfil de comportamento de alguém (rastreio entre câmeras, '
      'persistência de trail, Re-ID por silhueta)',
      'Art. 12, §2º (perfil comportamental de pessoa identificável é dado pessoal, ainda que "anônimo")',
      'Veto explícito e permanente a MTMCT, Re-ID e associação entre câmeras. O único rastreamento '
      'permitido é intra-câmera, efêmero, em RAM (ByteTrack, segundos), necessário à não-dupla-contagem. '
      'Teste de integração verifica que IDs não são persistidos.'],
     ['4', 'Deixar de ser anônimo por erro de configuração ou de schema (ex.: criar tabela '
      '<font face="Courier">sessoes</font>, gravar <font face="Courier">track_id</font>)',
      'Art. 12, caput (anonimização irreversível) e art. 5º, XI',
      'Schema do banco previsto apenas para configuração e métricas agregadas; auditoria de código '
      'automatizada (PRV-01) prevista como requisito da Fase 9; revisão documental contra as '
      'tabelas proibidas (doc 06) já realizada.']],
    [8 * mm, 44 * mm, 46 * mm, 72 * mm], fs=8.0))
A(caption('Tabela 2 — Os quatro vetores de risco do projeto e o tratamento dado a cada um. '
          'Os itens 1 e 2 são verificados por testes automatizados que rodam em toda entrega.'))

A(PageBreak())

# =========================================================== 2. ENQUADRAMENTO
A(h1('2. Enquadramento Legal'))
A(p('Esta seção estabelece o enquadramento do sistema perante a legislação. É a base sobre a qual '
    'se apoia a matriz de conformidade da seção 6. A verificação completa, artigo por artigo, está '
    'versionada em <i>.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md</i>.'))

A(h2('2.1 Papéis: quem é controlador e quem é operador'))
A(mk_table(
    ['Pergunta', 'Resposta adotada', 'Consequência prática'],
    [['O hotel é controlador dos dados? (art. 5º, VI)',
      '<b>Sim.</b> O hotel decide a finalidade (analytics de fluxo) e os meios (câmeras e sistema).',
      'O hotel responde perante os titulares e perante a ANPD.'],
     ['O sistema é controlador próprio?',
      '<b>Não.</b> Opera como <b>operador</b> em nome do hotel (art. 5º, VII). Se o produto for '
      'vendido a terceiros, quem compra é o controlador.',
      'As obrigações documentais (RIPD, ROPA, encarregado) são do hotel; o fornecedor entrega '
      'a evidência técnica.'],
     ['A saída do sistema é dado pessoal?',
      '<b>Não</b>, desde que as condições da seção 2.2 sejam respeitadas. É dado <b>anonimizado '
      'irreversível</b> (art. 5º, XI): contagens, ocupação, permanência e mapa de calor agregado.',
      'A saída pode ser usada em BI, relatório operacional e integração com PMS sem tratamento '
      'adicional de dados pessoais.'],
     ['Existe risco de a saída deixar de ser anônima?',
      '<b>Sim</b> — e é o risco central do projeto. Se o heatmap ou o dwell forem individualizados, '
      'passam a ser perfil comportamental (art. 12, §2º).',
      'Daí os vetos absolutos da seção 4 e a regra de persistir apenas agregados.']],
    [50 * mm, 66 * mm, 54 * mm], fs=8.2))
A(caption('Tabela 3 — Enquadramento do sistema (fonte: COMPLIANCE-LGPD-MARCO-CIVIL.md, seção 1).'))

A(h2('2.2 Natureza da saída: por que a saída é anônima e irreversível'))
A(p('A LGPD, no art. 12, caput, afasta do regime os dados anonimizados — <b>desde que a anonimização '
    'seja irreversível</b>. O projeto garante essa irreversibilidade por construção, e não por '
    'política de uso: o dado que sai do sistema é um <b>contador</b>, não uma <b>coordenada</b>. '
    'Nenhuma entidade individual (pessoa, sessão, ID de rastreamento, vetor de aparência) atravessa '
    'a fronteira de saída. O §2º do mesmo artigo é tratado como a fronteira mais dura: mesmo '
    'partindo de dados sem nome ou CPF, dados usados para formar perfil comportamental de pessoa '
    'identificável continuam sendo dados pessoais — e por isso são vedados no projeto.'))
A(mk_table(
    ['Camada', 'O que existe', 'Onde vive', 'Quanto tempo'],
    [['1. Imagem', 'Frame bruto da câmera', 'RAM do processo, variável local', 'Descartado no fim do frame'],
     ['2. Detecção', 'Bounding box + confiança (sem nome, sem ID persistente)', 'RAM', 'Descartado após o cálculo da zona'],
     ['3. Associação efêmera', 'ID numérico do ByteTrack, intra-câmera', 'RAM (dicionário <font face="Courier">track_states</font>)',
      'Morre quando a pessoa sai do quadro (poda a cada 60 frames)'],
     ['4. Agregação', 'Contagem de ocupação e % de área ocupada por zona', 'RAM (estado do processo)',
      'Zerada na virada do dia ou após 10 min de zona vazia'],
     ['5. Saída (futura, Fase 3+)', 'Métrica agregada por zona × janela de tempo',
      'PostgreSQL', 'Conforme TTL a definir por tipo de métrica (art. 16)']],
    [30 * mm, 56 * mm, 48 * mm, 36 * mm], fs=8.2))
A(caption('Tabela 4 — Inventário de dados por camada (ver seção 3.7 para as evidências em código). '
          'Observe que nenhuma camada contém identidade, e que a camada 3 é a única que usa '
          'identificadores temporários — sempre em RAM e por poucos segundos.'))

A(h2('2.3 Base legal do tratamento'))
A(mk_table(
    ['Base legal (art. 7º)', 'Aplicabilidade', 'Situação'],
    [['<b>VII</b> — proteção da vida e da incolumidade física',
      'Câmeras de segurança de hotel têm função de proteção.',
      'Aplicable à segurança já existente; o sistema é <b>complementar</b> (analytics), sem '
      'ampliar a captura de imagem.'],
     ['<b>IX</b> — interesse legítimo do controlador',
      'Operação do hotel: occupancy, fluxo, dimensionamento de equipe.',
      '<b>Base principal do sistema de analytics.</b> Exige <b>LIA</b> (Relatório de Impacto à '
      'Proteção de Dados Pessoais) nos termos do art. 10, §3º, e RIPD (art. 38). Ambos são '
      'requisito PRV-04, previsto para a Fase 9.'],
     ['<b>I</b> — consentimento',
      'Impraticável em monitoramento contínuo: não é livre, pode ser viciado e seria revogável '
      'a todo momento.',
      '<b>Não utilizada</b> — decisão deliberada e documentada.']],
    [46 * mm, 52 * mm, 72 * mm], fs=8.2))
A(caption('Tabela 5 — Bases legais avaliadas. A base de interesse legítimo é a que o hotel '
          'precisa documentar formalmente antes de operar (seção 7, lacunas L-01 e L-02).'))

A(h2('2.4 Marco Civil da Internet (Lei nº 12.965/2014)'))
A(mk_table(
    ['Artigo', 'Regra', 'Aplicação ao sistema'],
    [['Art. 2º, II e art. 7º, II', 'Privacidade como princípio e como direito',
      'Orienta todo o projeto; veda desvio de finalidade das câmeras de segurança para vigilância individual ou RH.'],
     ['Art. 10', 'Guarda de registros preservando a intimidade e a vida privada',
      'Logs mínimos, sem conteúdo de imagem e sem identificadores de pessoas.'],
     ['Art. 13', 'Registros de conexão guardados por 1 ano (provedor de conexão)',
      '<b>Não se aplica</b> — o sistema não é provedor de conexão.'],
     ['Art. 14', 'Vedado a provedor de conexão guardar registros de acesso a aplicações',
      '<b>Não se aplica</b> — mesma razão.'],
     ['<b>Art. 15</b>', 'Provedor de aplicação guarda registros de acesso à aplicação por '
      '<b>6 meses</b>, sob sigilo, em ambiente controlado',
      '<b>Aplica-se se a API/dashboard forem expostos pela internet.</b> Requisito API-04 (Fase 4): '
      'log de acesso = data/hora, IP, usuário e ação; retenção de exatamente 6 meses (não mais); '
      'prazo maior somente com requisição de autoridade competente e autorização judicial nos 60 dias '
      '(art. 15, §2º), procedimento a constar do runbook.'],
     ['Art. 22', 'Disponibilização de registros por ordem judicial',
      'Não há trilha individual para entregar; a resposta é a de dados agregados.'],
     ['Art. 11, III', 'Vedação a coletar/armazenar dados de conexão além do necessário',
      'Log de acesso mínimo, sem cookies de rastreamento de hóspede.']],
    [34 * mm, 58 * mm, 78 * mm], fs=8.2))
A(caption('Tabela 6 — Marco Civil da Internet: aplicação artigo a artigo (fonte: '
          'COMPLIANCE-LGPD-MARCO-CIVIL.md, seção 3).'))

A(h2('2.5 Regime sancionatório e exposição residual'))
A(p('A LGPD prevê, no art. 52, sanções graduadas. O quadro abaixo é reproduzido para dimensionar '
    'a exposição que a arquitetura do projeto elimina — e para deixar claro que o risco restante '
    'está concentrado em ações <b>organizacionais</b>, não técnicas.'))
A(mk_table(
    ['Sanção (art. 52)', 'Limite', 'Exposição do projeto'],
    [['I — Advertência com prazo para correção', '—', 'Não aplicável: não há infração técnica'],
     ['<b>II — Multa simples</b>', '<b>Até 2% do faturamento no Brasil (excluídos tributos), '
      'teto de R$ 50.000.000 por infração</b>',
      '<b>Eliminada por arquitetura</b> — sem face, sem imagem em disco, sem trilha persistida, '
      'sem associação entre câmeras'],
     ['III — Multa diária', 'Mesmo teto total',
      'Não aplicável: nada se repete automaticamente'],
     ['IV a VII — Publicação/registro da infração', 'Dano reputacional',
      'Não aplicável; a documentação de compliance publicada é, ela própria, mitigação de reputação'],
     ['VIII a X — Bloqueio, eliminação, suspensão ou vedação do tratamento', 'Pode parar o sistema',
      'Mitigação por arquitetura: o botão de eliminação é a eliminação da camada de identidade — '
      'que nunca é gravada'],
     ['Critérios do §1º', 'Gravidade, vantagem obtida, reincidência, cooperação, adoção de medidas, '
      'dano', 'A adoção do relatório de impacto e do plano de incidente conta como atenuante '
      '(cooperação e medidas)']],
    [46 * mm, 50 * mm, 74 * mm], fs=8.2))
A(caption('Tabela 7 — Sanções do art. 52 da LGPD (Lei nº 13.709/2018) e exposição residual. '
          'A maior multa do regime é de R$ 50 milhões ou 2% do faturamento, por infração.'))

A(PageBreak())

# =========================================================== 3. IMPLEMENTADO
A(h1('3. O que já foi implementado'))
A(p('Esta seção descreve o software efetivamente entregue e verificável hoje nas fases 1 e 2, com '
    'indicação de arquivo e de teste para cada afirmação.'))

A(h2('3.1 Panorama das fases concluídas'))
A(mk_table(
    ['Fase', 'Entregue', 'Evidência'],
    [['<b>Fase 1</b> — Fatia vertical single-câmera<br/>(concluída em 08/10/2026)',
      'Pipeline mínimo completo: captura de webcam/vídeo → detecção de corpo YOLO CrowdHuman → '
      'rastreio efêmero ByteTrack em RAM → overlay em tela. Nada em disco. Auditoria automatizada '
      'de privacidade desde o primeiro dia.',
      'Planos 01-01 a 01-04 (4/4); <i>captura.py</i>, <i>rastreio.py</i>, <i>overlay.py</i>, '
      '<i>main.py</i>; <i>tests/test_privacidade.py</i>'],
     ['<b>Fase 2</b> — Contagem e ocupação por zona em tempo real<br/>(concluída em 12/10/2026)',
      'Zonas ROI poligonais configuráveis por YAML; contagem e ocupação instantânea por zona '
      'recalculada a cada frame; interseção de área (Área do Objeto ∩ Área do ROI) com máscara '
      'visual e percentual no HUD; clamp de capacidade, reset diário, reconciliação após '
      'reabertura de fonte; integração visual no <i>main.py</i>.',
      'Planos 02-01 a 02-04 (4/4); <i>zona.py</i> (313 linhas), <i>config/zonas.yaml</i>; '
      '<i>tests/test_zona.py</i> (10 testes)']],
    [42 * mm, 72 * mm, 56 * mm], fs=8.2))
A(caption('Tabela 8 — Fases concluídas. Detalhamento completo dos planos em '
          '<i>.planning/phases/</i> (PLAN.md + SUMMARY.md por plano + VALIDATION.md da fase).'))

A(h2('3.2 Arquitetura do código'))
A(p('O produto é composto por seis módulos com responsabilidades estritamente separadas. Nenhum '
    'módulo de produto grava arquivo de mídia, e a separação entre <i>captura</i>, <i>rastreio</i>, '
    '<i>zonas</i> e <i>overlay</i> é o que torna a auditoria de privacidade simples e confiável.'))
A(mk_table(
    ['Módulo', 'Linhas', 'Responsabilidade', 'Papel em LGPD'],
    [['<font face="Courier">captura.py</font>', '19',
      'Abre a fonte (webcam por índice ou arquivo) e devolve o frame com <font face="Courier">capture_ts</font>.',
      'Ponto de entrada do dado volátil. Não escreve nada.'],
     ['<font face="Courier">rastreio.py</font>', '23',
      'Carrega o modelo YOLO CrowdHuman (classe 0 = corpo) e extrai caixas com o ByteTrack. '
      'Guarda apenas a classe de corpo.',
      'Restringe o modelo a corpo; ID efêmero, nunca persistido.'],
     ['<font face="Courier">zona.py</font>', '313',
      'Carrega e valida as zonas do YAML; calcula presença por polígono, interseção de área, '
      'clamp de capacidade, resets (diário/inatividade) e reconciliação de fonte.',
      'Onde o dado pessoal é convertido em número agregado.'],
     ['<font face="Courier">overlay.py</font>', '129',
      'Desenha ROIs, máscara de interseção, caixas (somente de quem toca o ROI), cards de '
      'contadores e HUD. Todas as funções desenham <i>in-place</i> no frame.',
      'Nenhuma escrita em disco — verificado por teste de varredura de API.'],
     ['<font face="Courier">main.py</font>', '124',
      'Orquestra o loop: captura → rastreio → zonas → overlay → HUD. Fixa o alvo de 5 FPS.',
      'Nenhuma chamada de persistência; nada sai do processo.'],
     ['<font face="Courier">scripts/demarcar_zona.py</font>', '263',
      'Utilitário de desenvolvimento para demarcar o ROI com o mouse e gravar as coordenadas no YAML.',
      '<b>Fora do pipeline de produção.</b> Grava apenas texto (coordenadas), nunca imagem.']],
    [34 * mm, 13 * mm, 73 * mm, 50 * mm], fs=8.0))
A(caption('Tabela 9 — Inventário de módulos do produto e respective papel na arquitetura de '
          'privacidade (privacy by design).'))

A(h2('3.3 Fluxo de processamento de um frame'))
A(p('Todo o caminho do dado, em uma iteração do loop (alvo de 5 FPS na webcam):'))
A(KeepTogether(code_block([
    'camera',
    '  |',
    '  v',
    'captura.capturar()       frame + capture_ts            [RAM, volatil]',
    '  |',
    '  v',
    'rastreio.rastrear()      YOLO corpo (classe 0)         [RAM, volatil]',
    'rastreio.extrair_caixas() (x1,y1,x2,y2,conf,id)         [RAM, efemero]',
    '  |',
    '  v',
    'zona.atualizar_ocupacao() presenca + intersecao         [RAM, agregado]',
    '                          de area por zona',
    '  |',
    '  v',
    'overlay.*                desenho in-place no frame      [RAM, volatil]',
    '  |',
    '  v',
    'cv2.imshow()             janela do operador             [tela, sem gravacao]',
    '  |',
    '  v',
    '(frame descartado -- nunca gravado)',
])))
A(spacer(4))
A(callout('Observação de privacidade sobre o loop',
          'Até a Fase 3, o único destino da informação é a tela do operador. <b>Nenhuma escrita '
          'em disco ocorre no caminho feliz</b> — e isso não depende de configuração: não existe '
          'chamada de persistência no código de produto. A partir da Fase 3, a persistência '
          'entrará por uma <b>fila em memória com escrita em lote</b> (batch writer), fora do loop '
          'de vídeo, contendo apenas métricas agregadas.',
          accent=ACCENT, bg=LIGHT))

A(h2('3.4 Ocupação por zona e a fórmula de interseção de área'))
A(p('A Fase 2 implementou, além da contagem clássica por ponto, a métrica de <b>ocupação por '
    'área</b>, que responde à pergunta central do projeto ("a ocupação por área está certa?"):'))
A(callout('Fórmula implementada — zona.py: calcular_intersecao_area_roi()',
          '<b>Interseção = Área(Objeto) ∩ Área(ROI)</b><br/><br/>'
          'A máscara binária das pessoas é cruzada com a máscara do ROI. O resultado é o percentual '
          'do ROI efetivamente coberto por corpos (exibido como <font face="Courier">AREA 12.4%</font> '
          'no HUD), a área em pixels da interseção e a área total do ROI. Essa métrica é o insumo do '
          'heatmap agregado previsto para a Fase 7.',
          accent=ACCENT, bg=LIGHT))
A(p('Durante a validação com a webcam foi corrigido um caso real de operação: o filtro de '
    'renderização exigia que o <i>pé</i> da pessoa estivesse dentro do ROI, o que escondia a '
    'caixa de detecção de pessoas sentadas ou parcialmente cortadas pelo enquadramento. A correção '
    'passou a considerar a interseção da área da pessoa com o ROI, alinhando o comportamento do '
    'overlay ao da métrica de ocupação. O comportamento é coberto por teste automatizado '
    '<font face="Courier">test_desenha_caixas_filtra_fora_do_roi</font>.'))

A(h2('3.5 Ferramenta de demarcação interativa de zonas'))
A(p('Para eliminar a edição manual de coordenadas no arquivo <font face="Courier">config/zonas.yaml</font>, '
    'foi implementado o utilitário <font face="Courier">scripts/demarcar_zona.py</font>: um '
    'demarcador por clique/arraste com alinhamento automático de arestas (<font face="Courier">a</font>), '
    'retângulo perfeito (<font face="Courier">r</font>), desfazer (<font face="Courier">u</font>), '
    'salvar (<font face="Courier">s</font>), limpar (<font face="Courier">c</font>) e sair '
    '(<font face="Courier">q</font>/ESC). <b>Ele não faz parte do pipeline de produção</b>: é '
    'ferramenta de desenvolvimento e calibração, gravando somente coordenadas em texto no YAML. '
    'Está registrado no roadmap como <i>SEED-261015</i>, com o gatilho de evolução para a Fase 5 '
    '(CRUD de zonas no dashboard).'))

A(h2('3.6 Auditoria de privacidade automatizada'))
A(p('A conformidade não depende de um parecer escrito: ela é <b>regressão de código</b>. Cada '
    'entrega roda a suíte, que falha o build se um invariante de privacidade for violado.'))
A(mk_table(
    ['Teste automatizado', 'O que ele prova', 'Alvo'],
    [['<font face="Courier">test_sem_modulos_de_face</font>',
      'Nenhum dos tokens <font face="Courier">face</font>, <font face="Courier">biometr</font>, '
      '<font face="Courier">demograf</font>, <font face="Courier">insightface</font>, '
      '<font face="Courier">facenet</font>, <font face="Courier">arcface</font>, '
      '<font face="Courier">deepface</font> aparece no código de produto nem no '
      '<font face="Courier">requirements.txt</font>.',
      'main.py, captura.py, rastreio.py, overlay.py, zona.py, requirements.txt'],
     ['<font face="Courier">test_sem_escrita_em_disco</font>',
      'Executa o pipeline real sobre o vídeo-amostra e compara o inventário de arquivos de mídia '
      '(jpg/png/mp4/avi/mkv) do repositório antes e depois: <b>zero arquivos novos</b>.',
      'Todo o repositório (exceto <font face="Courier">.git</font>)'],
     ['<font face="Courier">test_requirements_sem_contrib</font>',
      'A dependência <font face="Courier">opencv-contrib-python</font> está ausente — é ela que '
      'traria <font face="Courier">cv2.face</font>.',
      'requirements.txt'],
     ['<font face="Courier">test_sem_persistencia_ids</font> / '
      '<font face="Courier">test_ids_efemeros</font> / '
      '<font face="Courier">test_sem_escrita_de_ids</font>',
      'Os IDs do ByteTrack existem apenas em RAM e desaparecem quando a pessoa sai do quadro; '
      'nada é gravado em arquivo.',
      'Pipeline de rastreio e integração'],
     ['<font face="Courier">test_sem_apis_de_escrita</font>',
      'Nenhuma API de escrita de mídia (<font face="Courier">imwrite</font>, '
      '<font face="Courier">imsave</font>, <font face="Courier">VideoWriter</font>, '
      '<font face="Courier">tofile</font>) no módulo de overlay.',
      'overlay.py'],
     ['<font face="Courier">test_desenha_caixas_filtra_fora_do_roi</font>',
      'Pessoa fora do ROI não gera nenhum pixel desenhado; pessoa que toca o ROI é desenhada.',
      'overlay.py']],
    [50 * mm, 76 * mm, 44 * mm], fs=7.9))
A(caption('Tabela 10 — Testes que sustentam as garantias de privacidade. A lista completa dos 33 '
          'testes está no Anexo A.'))

A(h2('3.7 Inventário de dados: onde o dado nasce, onde vive e onde morre'))
A(mk_table(
    ['Dado', 'Natureza', 'Onde vive', 'Tempo de vida', 'Grava em disco?'],
    [['Frame de vídeo', 'Imagem de pessoa — dado pessoal em trânsito', 'RAM do processo',
      'Um frame (~200 ms a 5 FPS)', '<b>Não</b>'],
     ['Bounding box', 'Localização de corpo', 'RAM', 'Um frame', '<b>Não</b>'],
     ['ID de rastreamento', 'Identificador temporário intra-câmera', 'RAM '
      '(<font face="Courier">track_states</font>)', 'Poda em 60 frames (~12 s) ou ao sair do quadro',
      '<b>Não</b>'],
     ['Contagem por zona', 'Agregado', 'RAM (estado)', 'Até o reset diário ou 10 min de zona vazia',
      '<b>Não</b> (até a Fase 3)'],
     ['% de área ocupada', 'Agregado', 'RAM (estado)', 'Idem contagem', '<b>Não</b> (até a Fase 3)'],
     ['Coordenadas de zona', 'Configuração do ambiente (não dado pessoal)',
      '<font face="Courier">config/zonas.yaml</font>', 'Permanente (configuração)',
      'Sim — mas é configuração, não dado de pessoa'],
     ['Log de acesso à API', 'Registro técnico (IP, data/hora, ação)',
      'Servidor de logs (futuro)', 'Exatamente 6 meses (Marco Civil, art. 15)',
      'Sim — previsto na Fase 4, com TTL']],
    [28 * mm, 40 * mm, 36 * mm, 40 * mm, 26 * mm], fs=7.9))
A(caption('Tabela 11 — Inventário de dados. Nenhuma linha deste quadro representa dado pessoal '
          'persistido de hóspede ou visitante.'))

A(h2('3.8 Evidências de processo e rastreabilidade'))
A(p('O projeto é gerenciado por meio do framework GSD, que mantém um rastro auditável entre '
    'intenção e entrega. Para um gestor de projeto, isso significa que cada afirmação deste '
    'relatório é rastreável até um artefato:'))
A(mk_table(
    ['Artefato', 'Local', 'O que comprova'],
    [['Roadmap de 9 fases', '<i>.planning/ROADMAP.md</i>',
      'O plano completo, com metas, dependências, critérios de sucesso e rastreabilidade de requisitos'],
     ['Requisitos v1 (27)', '<i>.planning/REQUIREMENTS.md</i>',
      'Escopo formal aprovado, com seção explícita de <i>Out of Scope</i> (exclusões)'],
     ['Planos e resumos por plano', '<i>.planning/phases/01-*/</i>, <i>.planning/phases/02-*/</i>',
      'Como cada fase foi decomposta, executada e resumida (8 planos, 8 resumos)'],
     ['Contrato de validação da fase', '<i>02-VALIDATION.md</i>',
      'O mapa de verificação por tarefa, com critérios de aceite automatizados'],
     ['Verificação legal', '<i>.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md</i>',
      'Análise artigo a artigo da LGPD e do Marco Civil, com as 11 condições vinculantes'],
     ['Parecer de compliance', '<i>docs/DOCUMENTACAO_PROJETO_E_LGPD/07_*.md</i>',
      'Diagnóstico de risco e quadro de sanções, na versão original do projeto'],
     ['Plano maestro v1', '<i>docs/PLANO_V1_COMPLETO.md</i>',
      'Documento único de aprovação: requisitos + roadmap + 9 fases + invariantes legais'],
     ['Registro de depuração', '<i>.planning/debug/</i>',
      'Diagnóstico e plano de correção do filtro visual por ROI, com verificação e testes'],
     ['Sementes de roadmap', '<i>.planning/seeds/</i>',
      'Ideias validadas ainda dormentes (heatmap agregado; demarcador de zonas)'],
     ['Histórico Git', '81 commits',
      'Commits atômicos com mensagem convencional; documentação precede a implementação']],
    [38 * mm, 52 * mm, 80 * mm], fs=8.0))
A(caption('Tabela 12 — Artefatos de rastreabilidade do projeto.'))

A(PageBreak())

# =========================================================== 4. VETOS
A(h1('4. Vetos e Exclusões: o que nunca será implementado'))
A(p('Parte essencial de uma avaliação de conformidade é saber o que foi <b>descartado</b> e por quê. '
    'Os itens abaixo não estão "pendentes" — estão fora do escopo por decisão explícita, com base '
    'legal, e qualquer proposta de inclusão deve ser tratada como mudança de escopo sujeita a nova '
    'avaliação de impacto.'))
A(mk_table(
    ['Item vetado', 'Base legal do veto', 'Consequência para o hotel'],
    [['<b>Reconhecimento facial</b> e qualquer análise de biometria',
      'Art. 11 — dado sensível; nenhuma hipótese do §1º/§2º se aplica a analytics de fluxo. '
      'Multa de até R$ 50 milhões.',
      'Não é possível identificar hóspedes. Em contrapartida, o hotel não tem o passivo de dado sensível.'],
     ['<b>MTMCT / Re-ID</b> — associar a mesma pessoa entre câmeras diferentes, inclusive por '
      'silhueta ou aparência',
      'Art. 12, §2º — perfil comportamental. Decisão expressa do patrocinador do projeto.',
      'A câmera 2 nunca reconhece ninguém da câmera 1. Contagens entre câmeras não são somadas por pessoa.'],
     ['<b>Persistência de trail</b> — tabelas <font face="Courier">sessoes</font>, '
      '<font face="Courier">session_traces</font>, rotas, jornadas, embeddings',
      'Art. 12, §2º e art. 6º, II — trilha individual desnecessária à finalidade.',
      'Não existe "raio-x" do movimento de hóspedes. Não há como reconstruir a rotina de ninguém.'],
     ['<b>Heatmap por indivíduo</b> (traço de uma pessoa)',
      'Art. 12, §2º — reconstrução de rotina.',
      'O mapa de calor é de <b>densidade agregada</b> por célula e janela de tempo, sem identidade.'],
     ['<b>Gravação de vídeo, imagens ou crops</b> de clientes',
      'Art. 6º, III — desnecessário à finalidade.',
      'Não há nada a vazar de um vazamento: não há imagem armazenada.'],
     ['<b>Controle de acesso</b> (catracas, portas, liberação de quarto)',
      'Função de controle, não de analytics; fora do produto.',
      'O sistema informa, não decide sobre pessoas.'],
     ['<b>Correlação de identidade entre clientes/tenants</b>',
      'Art. 6º, I — finalidade; art. 12, §2º.',
      'Nenhum identificador de pessoa atravessa o sistema.']],
    [44 * mm, 58 * mm, 68 * mm], fs=8.0))
A(caption('Tabela 13 — Vetos permanentes do projeto (fonte: REQUIREMENTS.md, seção "Out of Scope", '
          'e COMPLIANCE-LGPD-MARCO-CIVIL.md, seção 5).'))
A(callout('Nota de consistência documental',
          'A pasta <i>docs/DOCUMENTACAO_PROJETO_E_LGPD/</i> preserva, de forma proposital, quatro '
          'documentos <b>superados</b> (04 — Face vs. Body; 05 — MTMCT; 06 — Modelagem de banco; '
          '07 — Parecer original), que descreviam o escopo inicial mais amplo. Todos eles trazem '
          'aviso de superação no cabeçalho. <b>A fonte da verdade do escopo vigente</b> é o trio: '
          '<i>docs/PLANO_V1_COMPLETO.md</i>, <i>.planning/REQUIREMENTS.md</i> e '
          '<i>.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md</i>. Recomenda-se, antes da '
          'apresentação formal, reforçar os avisos de superação nos documentos 04, 05, 06 e 07 — '
          'especialmente no 07, cuja tabela de temporalidade ainda cita snapshots de face e '
          'embeddings faciais que não existem e não serão implementados.',
          accent=WARN, bg=HexColor('#FBF3E8')))

A(PageBreak())

# =========================================================== 5. FUTURO
A(h1('5. O que será implementado: roadmap das Fases 3 a 9'))
A(p('O roadmap completo possui 9 fases. As fases 1 e 2 estão concluídas; as fases 3 a 9 são '
    'planejadas, com escopo, critérios de sucesso e marco de conformidade já definidos para cada '
    'uma. A ordem não é cronológica por conveniência: <b>a Fase 9 é um gate formal</b> — nenhum '
    'stream real com hóspedes entra antes dela.'))

A(h2('5.1 Visão geral'))
A(mk_table(
    ['Fase', 'Objetivo', 'Requisitos', 'Marco de conformidade da fase', 'Estado'],
    [['<b>3</b>', 'Persistência PostgreSQL: fila em memória + escrita em lote',
      'API-01, QUA-01',
      'Schema apenas de configuração e métricas agregadas; nenhuma tabela/coluna por pessoa; '
      'eventos de fluxo gravados sem chave de pessoa', 'A iniciar'],
     ['<b>4</b>', 'API FastAPI somente-leitura + conformidade Marco Civil',
      'API-02, API-03, API-04',
      'Endpoints sem dado por pessoa; TTL de retenção aplicado por tipo de métrica; log de acesso '
      'com IP/data/hora/ação retido por exatamente 6 meses', 'Planejada'],
     ['<b>5</b>', 'Dashboard web de ocupação e séries temporais',
      'DSH-01, DSH-02, OPS-02',
      'Ambiente reproduzível (docker-compose) com PostgreSQL + API + dashboard; separação dev/prod', 'Planejada'],
     ['<b>6</b>', 'Multi-câmera e ingestão RTSP com reconexão',
      'ING-02, OPS-01',
      'Tracker por câmera, sem qualquer associação entre câmeras; watchdog de staleness e '
      'backoff exponencial', 'Planejada'],
     ['<b>7</b>', 'Analytics de permanência (dwell) e heatmap agregado',
      'DWL-01, DWL-02, DSH-03',
      'Dwell calculado em RAM; persistidos apenas histograma/soma/n por zona×janela; heatmap de '
      'densidade agregada, sem histórico por pessoa', 'Planejada'],
     ['<b>8</b>', 'Validação de qualidade e testes automatizados',
      'QUA-02, QUA-03',
      'Suíte cobrindo as regras críticas (fila, ocupação, reconexão, dwell) e acurácia da contagem '
      'medida contra marcação manual em condição de pico', 'Planejada'],
     ['<b>9</b>', '<b>Conformidade LGPD e preparação para produção (gate)</b>',
      'PRV-01 a PRV-05, OPS-03',
      'Auditoria de código automatizada aprovada; RIPD + LIA + ROPA revisados; aviso de monitoramento '
      'e encarregado publicados; plano de resposta a incidente', 'Planejada']],
    [11 * mm, 40 * mm, 22 * mm, 72 * mm, 25 * mm], fs=8.0))
A(caption('Tabela 14 — Roadmap das fases restantes (fonte: .planning/ROADMAP.md).'))

A(h2('5.2 Fase 3 — Persistência PostgreSQL (próxima fase)'))
A(p('A Fase 3 é o ponto em que o sistema deixa de ser um instrumento de visualização e passa a '
    'produzir dado histórico. É, portanto, a fase de maior risco de conformidade do v1 — e por isso '
    'o schema é definido por restrição, não por conveniência.'))
A(mk_table(
    ['Decisão de projeto', 'Justificativa de conformidade'],
    [['Fila em memória + <i>batch writer</i> (tamanho ou tempo)',
      'Nenhuma operação de banco ocorre dentro do loop de vídeo (art. 6º, III — minimização do '
      'impacto; requisito QUA-01 de latência).'],
     ['Schema com apenas <font face="Courier">cameras</font>, <font face="Courier">zonas</font> e '
      '<font face="Courier">metricas_fluxo_zona</font>',
      'Configuração e agregados não são dados pessoais. As tabelas '
      '<font face="Courier">sessoes</font> e <font face="Courier">session_traces</font> do modelo '
      'original <b>não serão criadas</b>.'],
     ['Eventos de fluxo gravados como (zona, direção, timestamp de janela) — <b>sem track_id</b>',
      'O evento é atributo de zona, não de pessoa. Preserva a informação de fluxo (o objetivo) e '
      'elimina o vetor de identificação (art. 12, §2º).'],
     ['Idempotência por UUID de evento',
      'Reentrega de lote após interrupção não duplica contagem — integridade do indicador de '
      'negócio.'],
     ['Auditoria de schema como critério de aceite da fase',
      'Verificação automatizada de que nenhuma coluna por pessoa existe (requisito PRV-01, '
      'antecipado para a Fase 3 por ser o momento de maior risco).']],
    [58 * mm, 112 * mm], fs=8.2))
A(caption('Tabela 15 — Decisões de projeto da Fase 3 e sua base de conformidade.'))

A(h2('5.3 Fases 4 e 5 — Produto: API e dashboard'))
A(p('A Fase 4 entrega a API somente-leitura (FastAPI) que alimenta o dashboard. Do ponto de vista '
    'do Marco Civil, é aqui que nasce a possibilidade de o sistema se tornar <b>provedor de '
    'aplicação</b> (art. 15), e por isso o log de acesso com retenção de exatamente 6 meses é um '
    'critério de aceite da fase, não um extra. O TTL de retenção por tipo de métrica (art. 16) '
    'também entra aqui, no mesmo package.'))
A(p('A Fase 5 entrega o dashboard de ocupação ao vivo (WebSocket) e séries temporais, em ambiente '
    'reproduzível via <font face="Courier">docker-compose</font> (PostgreSQL + API + dashboard). '
    'O dashboard exibirá frescor da métrica para que o operador nunca interprete dado velho como '
    'sendo ao vivo — requisito que é tanto de qualidade de produto quanto de veracidade do '
    'relato ao gestor.'))

A(h2('5.4 Fases 6 e 7 — Escala e profundidade analítica'))
A(p('A Fase 6 introduz múltiplas câmeras e ingestão RTSP, com reconexão automática (backoff '
    'exponencial) e watchdog de latência. O ponto crítico de conformidade é explícito: '
    '<b>tracker por câmera, com vedação absoluta de qualquer associação entre câmeras</b> — '
    'inclusive por silhueta ou aparência. A Fase 6 também garante que derrubar um stream não '
    'corrompa contagens (sessões fechadas, ocupação reconciliada, tracker resetado).'))
A(p('A Fase 7 entrega dwell time por zona e o heatmap de <b>densidade agregada</b> (célula × '
    'janela de tempo). A semente de projeto <i>SEED-261014-szc</i> já registra a decisão de '
    'semântica: o mapa é de <b>ocupação</b> (área), e não de fluxo (ponto do pé), o que exige '
    'rasterizar a área da pessoa em grade e acumular em binário por frame — evitando inflar a '
    'métrica quando há sobreposição de pessoas. O risco principal mapeado é o <b>viés de '
    'perspectiva</b> (pessoa próxima da câmera ocupa mais células que pessoa distante); as '
    'mitigações em ordem de qualidade são homografia imagem→planta, uso apenas da base da caixa '
    'normalizada, ou aceitação e documentação explícita como "ocupação no espaço da imagem".'))

A(h2('5.5 Fases 8 e 9 — Qualidade e o gate de conformidade'))
A(p('A Fase 8 mede a acurácia da contagem contra marcação manual em condição de pico, com relatório '
    'de erro médio e faixa — é o que sustenta, tecnicamente, a afirmação de que a contagem está '
    'correta. A Fase 9 é o <b>gate</b>: a auditoria formal de conformidade e a preparação documental '
    'obrigatória antes de qualquer implantação real (detalhada na seção 7).'))
A(callout('Sequenciamento intencional',
          'A ordem do roadmap não é apenas de dependência técnica — é de <b>gestão de risco</b>. '
          'Os riscos de conformidade crescem com a superfície do sistema (mais câmeras, mais '
          'dados persistidos, mais API exposta). Por isso o gate documental vem depois de todas as '
          'fases técnicas, e a invariante <i>"nenhum stream real com hóspedes antes da Fase 9"</i> '
          'está inscrita no roadmap, no plano maestro e no REQUIREMENTS.',
          accent=ACCENT, bg=LIGHT))

A(h2('5.6 Sementes de roadmap (trabalho dormente validado)'))
A(mk_table(
    ['Semente', 'Escopo', 'Gatilho', 'Estado'],
    [['<b>SEED-261014-szc</b> — Mapa de ocupação por área',
      'Heatmap de presença (célula × janela) derivado da fórmula de interseção já implementada; '
      'modo/região/binário configuráveis por zona.',
      'Planejamento da Fase 7 (requisito DWL-02).', 'Dormante — protótipo validado'],
     ['<b>SEED-261015-demarcador-zonas-roi</b> — Demarcador interativo',
      'MVP já implementado em <i>scripts/demarcar_zona.py</i>: traçado por clique, alinhamento '
      'automático, retângulo, undo.',
      'Preparação da Fase 5 (CRUD de zonas no dashboard).', 'Dormante — MVP entregue']],
    [46 * mm, 66 * mm, 38 * mm, 20 * mm], fs=8.0))
A(caption('Tabela 16 — Sementes registradas em .planning/seeds/ e referenciadas no ROADMAP.md.'))

A(PageBreak())

# =========================================================== 6. MATRIZ
A(h1('6. Matriz de Conformidade'))
A(p('A tabela abaixo é a resposta objetiva à pergunta que motivated este relatório: '
    '<b>para cada dever legal aplicável, qual é a evidência de que o sistema o cumpre?</b> '
    'O status reflete apenas o que está <b>implementado e verificado hoje</b>; itens "previsto" '
    'constam com a fase do roadmap que os entrega.'))
A(mk_table(
    ['Dever legal', 'Como o sistema cumpre', 'Evidência', 'Status'],
    [['Art. 5º, XI e art. 12, caput — anonimização irreversível',
      'A saída é um contador agregado; nenhuma entidade individual atravessa a fronteira de saída.',
      '<i>zona.py</i> (agregação); <i>test_sem_persistencia_ids</i>', '<b>Conforme</b>'],
     ['Art. 12, §2º — vedação a perfil comportamental',
      'Sem trilhas persistidas, sem rotas, sem perfis, sem vetores de aparência, sem associação '
      'entre câmeras.',
      'Vetos da Tabela 13; <i>test_ids_efemeros</i>', '<b>Conforme</b>'],
     ['Art. 11 — dado sensível (face/biometria)',
      'Nenhum módulo de face existe; o modelo é exclusivamente de corpo (CrowdHuman).',
      '<i>test_sem_modulos_de_face</i>; <i>requirements.txt</i> sem opencv-contrib', '<b>Conforme</b>'],
     ['Art. 6º, II — adequação',
      'Coleta apenas o necessário à métrica exibida; nenhum dado sem uso no produto.',
      'Inventário da Tabela 11', '<b>Conforme</b>'],
     ['Art. 6º, III — necessidade e minimização',
      'Frames voláteis; trilhas intra-câmera de segundos; banco só com agregados (Fase 3).',
      '<i>test_sem_escrita_em_disco</i>; Fase 3', '<b>Conforme</b> (parcial na Fase 3)'],
     ['Art. 6º, IV — transparência',
      'Aviso de monitoramento nas áreas monitoradas (responsabilidade do hotel).',
      'Requisito PRV-05', '<b>Previsto — Fase 9</b>'],
     ['Art. 6º, V — segurança (medidas técnicas)',
      'ACL na API, TLS, separação dev/prod, backups criptografados.',
      'Requisito OPS-02 e PRV-05; seção 7', '<b>Previsto — Fases 4/5/9</b>'],
     ['Art. 6º, VI — não discriminação',
      'Impossível tratar uma pessoa individualmente: a saída não contém identidade.',
      'Arquitetura (Tabela 11)', '<b>Conforme</b>'],
     ['Art. 6º, VII e VIII — prevenção e responsabilização',
      'Este documento, o parecer interno, o RIPD/LIA/ROPA e o registro de operações.',
      'Seções 3.8 e 7; requisitos PRV-04', '<b>Parcial — Fase 9</b>'],
     ['Art. 7º, IX — interesse legítimo + art. 10, §3º (LIA)',
      'Base legal escolhida e registrada; LIA a produzir antes de produção.',
      'Requisito PRV-04; seção 2.3', '<b>Previsto — Fase 9</b>'],
     ['Art. 12/16 — eliminação e TTL',
      'TTL documentado e aplicado por tipo de métrica; expurgo de métricas antigas.',
      'Requisito API-03', '<b>Previsto — Fase 4</b>'],
     ['Art. 18 — direitos do titular',
      'Não há dado pessoal a responder; canal do encarregado e procedimento a documentar para o '
      'caso de incidente.',
      'Requisito PRV-05; seção 7', '<b>Previsto — Fase 9</b>'],
     ['Art. 37 — registro de operações (ROPA)',
      'Inventário de operações: frames em RAM, agregação em banco, exposição via API.',
      'Requisito PRV-04', '<b>Previsto — Fase 9</b>'],
     ['Art. 38 — relatório de impacto (RIPD)',
      'Conteúdo mínimo: tipos de dados, metodologia de coleta e segurança, medidas de mitigação.',
      'Requisito PRV-04', '<b>Previsto — Fase 9</b>'],
     ['Art. 41 e Res. CD/ANPD nº 18/2024 — encarregado',
      'Encarregado indicado, com identidade e contato divulgados publicamente, atendendo em '
      'português.',
      'Requisito PRV-05; seção 7', '<b>Previsto — Fase 9</b>'],
     ['Arts. 46 a 49 — segurança e boas práticas',
      'Plano de resposta a incidente; backups criptografados; ambiente controlado.',
      'Requisito OPS-03; seção 7', '<b>Previsto — Fases 4/9</b>'],
     ['Art. 48 — comunicação de incidente',
      'Plano documentado para comunicar à ANPD e aos titulares em caso de incidente com risco ou '
      'dano relevante.',
      'Requisito OPS-03', '<b>Previsto — Fase 9</b>'],
     ['Art. 52 — sanções',
      'Exposição eliminada por arquitetura (Tabela 7).',
      'Seções 2.5 e 3.6', '<b>Conforme</b>'],
     ['Marco Civil, art. 15 — logs de acesso por 6 meses',
      'Log mínimo (IP/data/hora/ação), sob sigilo, retenção de exatamente 6 meses, se a API for '
      'exposta.',
      'Requisito API-04', '<b>Previsto — Fase 4</b>'],
     ['Marco Civil, arts. 13 e 14',
      'Não aplicáveis — o sistema não é provedor de conexão.',
      'Tabela 6', '<b>Não aplicável</b>'],
     ['Marco Civil, art. 22 — ordem judicial',
      'Não há trilha individual a fornecer; entrega-se somente dado agregado.',
      'Tabela 6', '<b>Conforme</b>']],
    [40 * mm, 58 * mm, 42 * mm, 30 * mm], fs=7.6))
A(caption('Tabela 17 — Matriz de conformidade artigo a artigo. Status: "Conforme" = verificado em '
          'código e teste; "Previsto" = escopo aprovado e fase definida; "Parcial" = parte entregue.'))

A(PageBreak())

# =========================================================== 7. LACUNAS
A(h1('7. Lacunas, Riscos Residuais e Ações Necessárias'))
A(p('Esta é a seção de maior valor para a decisão de gestão. As lacunas abaixo <b>não são falhas de '
    'código</b>: são obrigações documentais e organizacionais que, por lei, são do controlador (o '
    'hotel). O sistema está pronto para produzi-las; o hotel precisa aprová-las e publicá-las.'))

A(h2('7.1 Lacunas antes da entrada em produção'))
A(mk_table(
    ['ID', 'Lacuna', 'Base legal', 'Fase', 'Prioridade', 'Responsável'],
    [['L-01', '<b>RIPD</b> (Relatório de Impacto à Proteção de Dados Pessoais) com tipos de dados, '
      'metodologia de coleta, segurança e mitigação', 'Art. 38 e art. 5º, XVII',
      '9', '<b>Crítica</b>', 'Controlador + Engenharia'],
     ['L-02', '<b>LIA</b> (Legitimate Interest Assessment) que sustente a base do art. 7º, IX',
      'Art. 10, §3º', '9', '<b>Crítica</b>', 'Controlador'],
     ['L-03', '<b>ROPA</b> — registro das operações de tratamento (frames em RAM, agregação em banco, '
      'exposição via API), finalidades, bases legais e retenções', 'Art. 37', '9',
      '<b>Crítica</b>', 'Controlador + Engenharia'],
     ['L-04', '<b>Encarregado (DPO)</b> indicado, com identidade e contato divulgados publicamente',
      'Art. 41; Res. CD/ANPD nº 18/2024', '9', '<b>Crítica</b>', 'Controlador'],
     ['L-05', '<b>Aviso de monitoramento</b> afixado nas áreas monitoradas, com a finalidade descrita',
      'Art. 6º, IV', '9', '<b>Crítica</b>', 'Controlador (Operação)'],
     ['L-06', '<b>TTL de retenção</b> documentado e aplicado por tipo de métrica', 'Art. 16',
      '4', 'Alta', 'Engenharia'],
     ['L-07', '<b>Log de acesso à API</b> com IP/data/hora/ação, retido exatamente 6 meses sob sigilo',
      'Marco Civil, art. 15', '4', 'Alta', 'Engenharia'],
     ['L-08', '<b>Plano de resposta a incidente</b>, com procedimento de comunicação à ANPD e aos '
      'titulares', 'Art. 48; arts. 46 e 47', '9', 'Alta', 'Controlador + Engenharia'],
     ['L-09', '<b>Ambiente separado dev/prod</b>, com controle de acesso, TLS e backups criptografados',
      'Art. 6º, V; arts. 46 e 47', '4/5', 'Alta', 'Engenharia + TI'],
     ['L-10', '<b>Auditoria automatizada de schema</b> confirmando ausência de colunas por pessoa, '
      'rodando na integração contínua', 'Art. 12, caput; art. 5º, XI', '3/9',
      'Alta', 'Engenharia'],
     ['L-11', '<b>Validação de acurácia</b> da contagem contra marcação manual em condição de pico',
      'Art. 7º, IX (necessidade e demonstração de eficácia)', '8', 'Média', 'Engenharia + Operação'],
     ['L-12', '<b>Ajuste dos avisos de superação</b> nos documentos 04, 05, 06 e 07 da pasta legal '
      '(evitar leitura divergente de escopo)', 'Boa governança documental', '—',
      'Média', 'Engenharia'],
     ['L-13', '<b>Política de privacidade e procedimento de direitos do titular</b> publicados para '
      'consulta', 'Art. 9 e art. 18', '9', 'Média', 'Controlador']],
    [11 * mm, 58 * mm, 32 * mm, 12 * mm, 17 * mm, 40 * mm], fs=7.7))
A(caption('Tabela 18 — Lacunas de conformidade. As cinco lacunas críticas são de responsabilidade '
          'do controlador e destravam a entrada em produção.'))

A(h2('7.2 Riscos residuais (aceitos de forma consciente)'))
A(mk_table(
    ['Risco', 'Probabilidade / impacto', 'Mitigação existente', 'Plano'],
    [['Oclusão em cenas densas: pessoas sobrepostas podem ser contadas de forma imprecisa',
      'Média / Médio',
      'Documentada em CONCERNS.md; validação de acurácia prevista na Fase 8',
      'Marcação manual em pico; definir o que é "quem conta"'],
     ['Viés de perspectiva no heatmap: pessoa próxima da câmera ocupa mais células',
      'Alta / Médio',
      'Decisão de semântica registrada no SEED-261014; acumulação binária por frame',
      'Homografia imagem→planta ou uso da base normalizada (Fase 7)'],
     ['Desvio de finalidade: uso das contagens para vigilância individual ou RH',
      'Baixa / <b>Alto</b>',
      'Arquitetura que não permite individualizar (Tabela 11); princípio do art. 6º, I',
      'Cláusula contratual de uso + camada 1 do RIPD'],
     ['Reidentificação por correlação de métricas agregadas com dados externos',
      'Baixa / Médio',
      'Granularidade por zona×janela, sem chave de pessoa',
      'Avaliar granularidade mínima e ruído no RIPD'],
     ['Falha de infraestrutura em produção (câmera, banco, energia) corrompendo contagens',
      'Média / Médio',
      'Reconciliação de fonte e clamp já implementados (Fase 2); reconexão com watchdog na Fase 6',
      'Fase 6 + procedimento de resposta a incidente'],
     ['Exposição indevida da API/dashboard na internet sem os logs previstos',
      'Baixa / Alto',
      'Requisito API-04 com prazo de 6 meses',
      'Definir o requisito de exposição antes da Fase 4']],
    [46 * mm, 28 * mm, 52 * mm, 44 * mm], fs=7.9))
A(caption('Tabela 19 — Riscos residuais identificados, com o tratamento já existente e o plano '
          'associado.'))

A(h2('7.3 Cronograma de conformidade'))
A(mk_table(
    ['Horizonte', 'Ações', 'Resultado'],
    [['Curto prazo (imediato)',
      'Reforçar avisos de superação nos documentos 04/05/06/07 (L-12); nomear o encarregado (L-04); '
      'definir escopo de exposição da API (L-07);',
      'Documentação sem ambiguidade e responsável legal definido.'],
     ['Médio prazo (Fases 3 a 6)',
      'Persistência apenas agregada (L-10 parcial); TTL por métrica (L-06); logs de 6 meses (L-07); '
      'ambiente dev/prod com TLS e backups (L-09);',
      'Camada de dados e de produto em conformidade verificável.'],
     ['Longo prazo (Fases 7 a 9)',
      'Validação de acurácia (L-11); RIPD, LIA, ROPA (L-01 a L-03); aviso de monitoramento (L-05); '
      'plano de incidente (L-08); política de privacidade e direitos do titular (L-13).',
      'Gate da Fase 9 aprovado — liberação para operação com hóspedes reais.']],
    [36 * mm, 92 * mm, 42 * mm], fs=8.0))
A(caption('Tabela 20 — Sequenciamento das ações de conformidade ao longo do roadmap.'))

A(PageBreak())

# =========================================================== 8. RECOMENDAÇÕES
A(h1('8. Recomendações ao Gestor de Projeto'))
A(p('As recomendações abaixo são a conclusão prática deste relatório: o que a gestão precisa decidir, '
    'aprovar ou encaminhar.'))
A(num('1', '<b>Aprovar o arcabouço técnico como conforme.</b> O sistema entregue nas Fases 1 e 2 '
         'não apresenta vetor de infração da LGPD identificável, e essa afirmação é sustentada por '
         'testes automatizados que acompanham cada entrega (seção 3.6), e não apenas por este '
         'parecer.'))
A(num('2', '<b>Autorizar formalmente o início da Fase 3</b> (persistência PostgreSQL), mantendo o '
         'princípio de que o schema só poderá conter configuração e métricas agregadas. Recomenda-se '
         'incluir no aceite da fase a auditoria automatizada de schema (L-10), antecipando o '
         'requisito PRV-01.'))
A(num('3', '<b>Designar o encarregado (DPO) e publicar o contato</b> (L-04). É item de '
         'responsabilidade do hotel e precede qualquer processamento com titulares reais; a '
         'Res. CD/ANPD nº 18/2024 e o guia orientativo de 19/12/2024 fixam o padrão de divulgação.'))
A(num('4', '<b>Definir o escopo de exposição da API/dashboard</b> antes da Fase 4: se houver '
         'exposição pela internet, dispara automaticamente a obrigatoriedade dos logs de acesso com '
         'retenção de exatamente 6 meses (Marco Civil, art. 15), com custo operacional de storage e '
         'de processo que precisa ser orçado.'))
A(num('5', '<b>Incluir no escopo da Fase 9 a produção do RIPD, do LIA e do ROPA</b> (L-01 a L-03). '
         'O material técnico necessário já está neste relatório e no parecer interno — o trabalho '
         'restante é de consolidação e aprovação jurídica, não de engenharia.'))
A(num('6', '<b>Manter a invariante de não tratar hóspedes reais antes da Fase 9.</b> As Fases 3 a 8 '
         'usam webcam, vídeos-amostra e MediaMTX local. Essa restrição é a principal barreira de '
         'risco do projeto e deve permanecer formal, inclusive no plano de atividades.'))
A(num('7', '<b>Sanear a documentação legal histórica</b> (L-12) antes da circulação externa, '
         'reforçando os avisos de superação dos documentos 04, 05, 06 e 07 — em especial a tabela de '
         'temporalidade do parecer 07, que ainda cita snapshots de face e embeddings faciais '
         'inexistentes no escopo vigente.'))
A(num('8', '<b>Adotar a auditoria automatizada como critério de aceite de toda entrega futura.</b> '
         'Os 33 testes existentes cobrem privacidade, integração, zonas e contratos; a partir da '
         'Fase 3 eles passam a incluir fila, schema, TTL e reconexão. É o que transforma a '
         'conformidade de afirmação em propriedade verificável.'))
A(num('9', '<b>Registrar formalmente a decisão de escopo e os vetos</b> (Tabela 13) na ata do '
         'projeto, para que qualquer proposta futura de reconhecimento facial, Re-ID, rastreamento '
         'entre câmeras ou heatmap individual seja tratada como <i>mudança de escopo</i> com nova '
         'avaliação de impacto, e não como evolução natural do produto.'))

A(PageBreak())

# =========================================================== 9. CONCLUSÃO
A(h1('9. Conclusão'))
A(p('O sistema de visão computacional para hotelaria, no estado atual de desenvolvimento, é '
    '<b>compatível com a Lei nº 13.709/2018 (LGPD) e com a Lei nº 12.965/2014 (Marco Civil da '
    'Internet)</b>, e o está por construção, e não por ajuste: a decisão de projeto central — '
    'produzir somente métricas agregadas, com identificadores temporários restritos à memória e '
    'descartados em segundos — é simultaneamente a decisão que torna o produto juridicamente '
    'defensável e o risco residual baixo.'))
A(p('Essa conformidade está <b>verificada por testes automatizados</b> que impedem a regressão: '
    'nenhum módulo de face, nenhuma escrita de imagem em disco, nenhum ID persistido, nenhuma '
    'associação entre câmeras. Trinta e três testes verdes constituem a evidência operacional da '
    'afirmação.'))
A(p('O que falta para a operação com hóspedes reais <b>não é engenharia</b>: são cinco documentos '
    'e controles de responsabilidade do controlador — RIPD, LIA, ROPA, encarregado publicado e aviso '
    'de monitoramento — mais TTL de retenção, logs de acesso, ambiente protegido e plano de '
    'resposta a incidente, todos já previstos no roadmap com fase e responsável definidos. O gate da '
    'Fase 9 existe justamente para separar "o sistema funciona" de "o sistema pode operar".'))
A(callout('Recomendação final',
          '<b>Autorizar a continuidade do roadmap das Fases 3 a 8 em ambiente de teste, iniciar '
          'imediatamente a produção dos documentos de conformidade de responsabilidade do '
          'controlador (RIPD, LIA, ROPA) e do processo de designação e publicação do encarregado, e '
          'manter a liberação para operação com hóspedes reais condicionada à aprovação do gate da '
          'Fase 9.</b><br/><br/>'
          'Com essa conduta, o projeto mantém o requisito de conformidade que deu origem a ele e '
          'constrói o produto de analytics sem jamais produzir uma trilha de pessoa.',
          accent=OK, bg=HexColor('#EDF5F0')))

A(PageBreak())

# =========================================================== ANEXOS
A(h1('Anexo A — Inventário da suíte de testes (33 testes)'))
A(mk_table(
    ['Arquivo', 'Testes', 'Cobertura'],
    [['<font face="Courier">tests/test_privacidade.py</font>', '3',
      'Sem módulos de face; nada escrito em disco durante a execução real do pipeline; '
      'dependência sem opencv-contrib'],
     ['<font face="Courier">tests/test_integracao.py</font>', '4',
      'Pipeline real detecta corpos; IDs efêmeros; invariantes de contagem no vídeo-amostra; '
      'sem persistência de IDs'],
     ['<font face="Courier">tests/test_zona.py</font>', '10',
      'YAML de zonas; carregamento validado; poda de tracks; interseção de área; ocupação por ROI; '
      'clamp de capacidade; reset diário; reset por zona vazia; reconciliação de fonte; '
      'desenhos retornam frame'],
     ['<font face="Courier">tests/test_overlay.py</font>', '4',
      'Desenho de caixas in-place; HUD; filtro de caixas fora do ROI; ausência de APIs de escrita'],
     ['<font face="Courier">tests/test_main.py</font>', '6',
      'Resolução de fonte (webcam/arquivo); resolução de modelo; importabilidade dos módulos'],
     ['<font face="Courier">tests/test_rastreio.py</font>', '3',
      'Extração de caixas com guarda de classe; IDs efêmeros; ausência de escrita de IDs'],
     ['<font face="Courier">tests/test_captura.py</font>', '3',
      'Abertura de vídeo-amostra; fonte inexistente não levanta erro; timestamp posterior ao frame'],
     ['<font face="Courier">tests/conftest.py</font>', '—',
      'Fixtures de modelo e vídeo-amostra, com skip explícito quando ausentes']],
    [48 * mm, 13 * mm, 109 * mm], fs=8.0))
A(caption('Tabela A1 — Suíte automatizada. Comando: ./.venv/bin/python -m pytest'))

A(h1('Anexo B — Rastreabilidade de requisitos (27 requisitos v1)'))
A(mk_table(
    ['Área', 'Requisitos', 'Fase', 'Status'],
    [['Ingestão', 'ING-01, ING-03', 'Fase 1', '<b>Concluídos</b> (ING-02 → Fase 6)'],
     ['Contagem', 'CNT-01, CNT-02, CNT-03, CNT-04', 'Fases 1 e 2', '<b>Concluídos</b>'],
     ['Permanência e fluxo', 'DWL-01, DWL-02', 'Fase 7', 'Planejados'],
     ['Dados e API', 'API-01 (Fase 3), API-02, API-03, API-04 (Fase 4)', 'Fases 3 e 4', 'Planejados'],
     ['Dashboard', 'DSH-01, DSH-02 (Fase 5), DSH-03 (Fase 7)', 'Fases 5 e 7', 'Planejados'],
     ['Privacidade', 'PRV-01 a PRV-05', 'Fase 9', 'Planejados — gate'],
     ['Qualidade', 'QUA-01 (Fase 3), QUA-02, QUA-03 (Fase 8)', 'Fases 3 e 8', 'Planejados'],
     ['Operação', 'OPS-01 (Fase 6), OPS-02 (Fase 5), OPS-03 (Fase 9)', 'Fases 5, 6 e 9', 'Planejados']],
    [34 * mm, 62 * mm, 32 * mm, 42 * mm], fs=8.0))
A(caption('Tabela B1 — Rastreabilidade requisito × fase (fonte: .planning/REQUIREMENTS.md). '
          'Cobertura verificada: 27/27 requisitos v1 mapeados, sem órfãos e sem duplicações.'))

A(h1('Anexo C — Glossário'))
A(mk_table(
    ['Termo', 'Significado no contexto deste projeto'],
    [['ROI', 'Região de Interesse — polígono que delimita uma zona monitorada do ambiente '
             '(ex.: hall, restaurante). Definido em <font face="Courier">config/zonas.yaml</font>.'],
     ['Interseção de área', 'Métrica de ocupação: percentual do ROI efetivamente coberto por '
      'corpos detectados (Área do Objeto ∩ Área do ROI).'],
     ['Capacidade', 'Número máximo de pessoas que uma zona pode reportar; o valor é limitado '
      '(clamp) para evitar distorções por falso positivo.'],
     ['ByteTrack', 'Algoritmo de rastreamento multi-objeto. Aqui usado apenas de forma efêmera e '
      'intra-câmera, para evitar dupla contagem.'],
     ['Tripwire', 'Linha virtual de passagem com detecção de entrada/saída. Mantido no código, '
      'desativado no padrão atual (foco em ocupação por área).'],
     ['Dwell time', 'Tempo de permanência de uma pessoa em uma zona. Calculado em RAM; '
      'persistido apenas como histograma agregado.'],
     ['Heatmap agregado', 'Mapa de densidade de ocupação por célula e janela de tempo, sem '
      'identidade e sem histórico por pessoa.'],
     ['ROPA', 'Registro de Operações de Tratamento — inventário do que é tratado, por quê, com qual '
      'base legal e por quanto tempo (art. 37).'],
     ['RIPD', 'Relatório de Impacto à Proteção de Dados Pessoais (art. 38).'],
     ['LIA', 'Legitimate Interest Assessment — avaliação documentada do interesse legítimo '
      '(art. 7º, IX e art. 10, §3º).'],
     ['Dwell-weighted', 'Preferência de projeto: métricas de permanência ponderadas por tempo são '
      'mais úteis ao hotel do que contagens brutas de passagem.'],
     ['Gate', 'Fase do roadmap cuja aprovação é condição para a etapa seguinte — no caso da Fase 9, '
      'para a operação com hóspedes reais.']],
    [36 * mm, 134 * mm], fs=8.0))

A(h1('Anexo D — Referências normativas'))
A(mk_table(
    ['Norma', 'Dispositivo', 'Matéria'],
    [['Lei nº 13.709/2018 (LGPD)', 'Art. 5º, VI, VII, XI, XVII',
      'Definições: controlador, operador, dado anonimizado, RIPD'],
     ['', 'Art. 6º, I a VIII', 'Princípios: finalidade, adequação, necessidade, transparência, '
      'segurança, não discriminação, prevenção, responsabilização'],
     ['', 'Art. 7º, VII e IX', 'Bases legais: proteção da vida; interesse legítimo'],
     ['', 'Art. 10, §3º', 'Relatório de impacto quando a base é o interesse legítimo'],
     ['', 'Art. 11', 'Dados sensíveis (biometria) — vetados'],
     ['', 'Art. 12, caput e §2º', 'Anonimização; perfil comportamental — eixo central do projeto'],
     ['', 'Art. 16', 'Eliminação; prazo de retenção'],
     ['', 'Art. 18', 'Direitos do titular'],
     ['', 'Art. 37', 'Registro das operações'],
     ['', 'Art. 38', 'Relatório de impacto (RIPD)'],
     ['', 'Art. 41', 'Encarregado (DPO)'],
     ['', 'Arts. 46 a 49', 'Segurança; comunicação de incidente'],
     ['', 'Art. 52', 'Sanções administrativas'],
     ['Lei nº 12.965/2014 (Marco Civil)', 'Arts. 2º, II; 7º, II; 10; 11, III; 22',
      'Privacidade; guarda de registros; minimização; ordem judicial'],
     ['', 'Arts. 13 e 14', 'Registros de conexão — não aplicáveis'],
     ['', '<b>Art. 15</b>', 'Registros de acesso a aplicações — 6 meses, sob sigilo'],
     ['ANPD', 'Res. CD/ANPD nº 18/2024; guia de 19/12/2024',
      'Encarregado; guia de definições de agentes']],
    [46 * mm, 42 * mm, 82 * mm], fs=8.0))
A(caption('Tabela D1 — Normas e dispositivos citados. A análise detalhada, com o raciocínio '
          'aplicado a cada artigo, está em .planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md.'))

A(h1('Anexo E — Artefatos técnicos do projeto'))
A(mk_table(
    ['Item', 'Detalhe'],
    [['Repositório principal', 'LTD-Parangaba/Projeto-Visao-Computacional-Hotel (organização)'],
     ['Fork de trabalho', 'jao1224/Visao-Computacional-Roi-e-tripwire (desenvolvimento)'],
     ['Branches', '<font face="Courier">main</font>, <font face="Courier">develop</font>, '
      '<font face="Courier">feat/intersecao-area-roi</font> (branch de trabalho atual)'],
     ['Linguagem e runtime', 'Python 3.14 (ambiente <font face="Courier">.venv</font>); '
      'OpenCV 5.0; Ultralytics 8.4; NumPy 2.5; PyYAML 6.0.3'],
     ['Modelo', 'YOLO treinado no CrowdHuman para detecção de corpo (classe 0 = person); '
      'pesos em <font face="Courier">resultados/best.pt</font>'],
     ['Configuração de zonas', '<font face="Courier">config/zonas.yaml</font> — câmera '
      '<font face="Courier">camera_0</font>, zona <font face="Courier">hall</font> (ROI), '
      'capacidade 50'],
     ['Execução', '<font face="Courier">./.venv/bin/python main.py [índice|arquivo]</font> — '
      'alvo de 5 FPS; tecla <font face="Courier">q</font> encerra'],
     ['Calibração de zonas', '<font face="Courier">./.venv/bin/python scripts/demarcar_zona.py 0</font>'],
     ['Testes', '<font face="Courier">./.venv/bin/python -m pytest</font> — 33 testes, ~10 s'],
     ['Documentação legal', '<font face="Courier">docs/DOCUMENTACAO_PROJETO_E_LGPD/</font> '
      '(documentos 01 a 09 + README) e <font face="Courier">docs/PLANO_V1_COMPLETO.md</font>'],
     ['Planejamento e auditoria', '<font face="Courier">.planning/</font> — ROADMAP, REQUIREMENTS, '
      'STATE, research (incluindo a verificação legal), phases, seeds, debug'],
     ['Histórico', '81 commits atômicos; documentação precede a implementação em todas as entregas']],
    [42 * mm, 128 * mm], fs=8.0))

A(spacer(6))
A(hr(ACCENT, 1.2))
A(p('<b>Fim do relatório.</b> Documento gerado a partir do estado auditável do projeto em '
    '%s. Referências internas: <font face="Courier">.planning/research/COMPLIANCE-LGPD-MARCO-CIVIL.md</font> '
    '(verificação legal), <font face="Courier">.planning/REQUIREMENTS.md</font> (escopo e exclusões), '
    '<font face="Courier">.planning/ROADMAP.md</font> (fases) e a suíte de testes automatizada do '
    'repositório.' % DATA, SMALLC))

# ---------------------------------------------------------------- build
doc = RelatorioDoc(OUT, pagesize=A4,
                   leftMargin=20 * mm, rightMargin=20 * mm,
                   topMargin=20 * mm, bottomMargin=18 * mm,
                   title='Relatório de Conformidade LGPD — Visão Computacional para Hotelaria',
                   author='Equipe de Engenharia de Visão Computacional — LTD-Parangaba',
                   subject='LGPD / Marco Civil da Internet — Visão Computacional para Hotelaria (Analytics de Fluxo)')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
doc.multiBuild(F)
print('PDF gerado em:', OUT)
