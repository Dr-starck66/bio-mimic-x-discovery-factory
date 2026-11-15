from pathlib import Path
import html
import mistune
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle

for label, font in [('Astra','DejaVuSans.ttf'),('AstraBold','DejaVuSans-Bold.ttf'),('AstraOblique','DejaVuSans-Oblique.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(label, '/usr/share/fonts/truetype/dejavu/'+font))
pdfmetrics.registerFontFamily('Astra',normal='Astra',bold='AstraBold',italic='AstraOblique',boldItalic='AstraBold')
W,H=A4
margin=19*mm
sty={
 'h1':ParagraphStyle('h1',fontName='AstraBold',fontSize=15,leading=21,spaceAfter=12,textColor=HexColor('#123657')),
 'h2':ParagraphStyle('h2',fontName='AstraBold',fontSize=12,leading=17,spaceBefore=12,spaceAfter=7,textColor=HexColor('#123657')),
 'h3':ParagraphStyle('h3',fontName='AstraBold',fontSize=10.2,leading=15,spaceBefore=9,spaceAfter=5,textColor=HexColor('#123657')),
 'p':ParagraphStyle('p',fontName='Astra',fontSize=8.7,leading=13.3,spaceAfter=7,wordWrap='CJK'),
 'li':ParagraphStyle('li',fontName='Astra',fontSize=8.4,leading=12.7,leftIndent=14,firstLineIndent=-8,spaceAfter=3,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='Astra',fontSize=7.0,leading=10,wordWrap='CJK'),
 'code':ParagraphStyle('code',fontName='Mono',fontSize=6.8,leading=10,leftIndent=10,wordWrap='CJK')
}
def inline(nodes):
    out=[]
    for n in nodes or []:
        typ=n['type']
        child=inline(n.get('children'))
        if typ in ('text','codespan','inline_html'):
            raw=html.escape(n.get('raw',''))
            out.append('<font name="Mono" size="7.5">'+raw+'</font>' if typ=='codespan' else raw)
        elif typ=='strong':out.append('<b>'+child+'</b>')
        elif typ=='emphasis':out.append('<i>'+child+'</i>')
        elif typ=='link':
            target=html.escape(n.get('attrs',{}).get('url',''),quote=True)
            out.append('<link href="'+target+'"><font color="#165ca3">'+child+'</font></link>' if target.startswith('https://') else child)
        elif typ in ('linebreak','softbreak'):out.append(' ')
        elif typ=='strikethrough':out.append(child)
        else:out.append(child or html.escape(n.get('raw','')))
    return ''.join(out)
story=[]
def add(n):
    typ=n['type']
    if typ=='heading':
        key='h'+str(n.get('attrs',{}).get('level',3))
        story.append(Paragraph(inline(n.get('children')),sty.get(key,sty['h3'])))
    elif typ in ('paragraph','block_text'):
        story.append(Paragraph(inline(n.get('children')),sty['p']))
    elif typ=='list':
        for item in n.get('children',[]):
            for c in item.get('children',[]):
                story.append(Paragraph('• '+inline(c.get('children')),sty['li']))
    elif typ=='table':
        rows=[]
        for section in n.get('children',[]):
            rs=[section] if section['type']=='table_head' else section.get('children',[])
            for row in rs:
                rows.append([Paragraph(inline(cell.get('children')),sty['cell']) for cell in row.get('children',[])])
        if rows:
            cols=max(map(len,rows))
            rows=[r+[Paragraph('',sty['cell'])]*(cols-len(r)) for r in rows]
            widths=[(W-2*margin)/cols]*cols
            t=LongTable(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e9f0f7')),('GRID',(0,0),(-1,-1),0.3,HexColor('#cad6e1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            story.extend([t,Spacer(1,8)])
    elif typ=='block_code':
        for line in n.get('raw','').splitlines():
            story.append(Paragraph('<font name="Mono" size="7">'+html.escape(line)+'</font>',sty['code']))
    elif typ=='block_quote':
        for c in n.get('children',[]):add(c)
    elif typ=='thematic_break':story.append(Spacer(1,8))

source=Path('preprint.md').read_text(encoding='utf-8')
tree=mistune.create_markdown(renderer='ast',plugins=['table','strikethrough'])(source)
for n in tree:add(n)

def footer(can,doc):
    can.saveState()
    can.setStrokeColor(HexColor('#b8c8d7'))
    can.line(margin,16*mm,W-margin,16*mm)
    can.setFont('Astra',6.8)
    can.drawString(margin,11*mm,'ASTRA Ω Research | Dr Starck | Preprint - CC BY 4.0')
    can.drawRightString(W-margin,11*mm,'Page '+str(doc.page))
    can.restoreState()

doc=SimpleDocTemplate('preprint.pdf',pagesize=A4,leftMargin=margin,rightMargin=margin,topMargin=20*mm,bottomMargin=22*mm,title=source.splitlines()[0].lstrip('# ').strip(),author='Dr Starck',subject='ASTRA Ω Research preprint, not peer reviewed',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print('RENDER_PASS',Path('preprint.pdf').stat().st_size)
