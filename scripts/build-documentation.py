from pathlib import Path
import html,markdown,re,posixpath
from urllib.parse import urlsplit,unquote
root=Path(__file__).resolve().parent.parent
pages=[('start','README.md','Überblick'),('installation','docs/INSTALLATION.md','Installation'),('neu','docs/CHANGELOG-20261021.md','Neue Ausgabe'),
       ('bedienung','docs/BEDIENUNG.md','Bedienung'),('aenderungen','docs/AENDERUNGEN.md','Alle Erweiterungen'),
       ('lizenzen','docs/LIZENZEN.md','Lizenzen'),('github','docs/GITHUB.md','GitHub'),('pruefung','docs/PRUEFSTATUS.md','Prüfstatus')]
mapping={p:'#'+key for key,p,_ in pages}
navigation=''.join(f'<a href="#{key}">{html.escape(label)}</a>' for key,_,label in pages)
sections=[]
for key,path,label in pages:
    text=(root/path).read_text(encoding='utf-8')
    body=markdown.markdown(text,extensions=['tables','fenced_code'])
    def local_link(match):
        href=html.unescape(match[1]);parts=urlsplit(href)
        if parts.scheme or parts.netloc or href.startswith('#'):return match[0]
        resolved=posixpath.normpath(posixpath.join(posixpath.dirname(path),unquote(parts.path)))
        target=mapping.get(resolved,resolved)
        if parts.fragment and not target.startswith('#'):target+='#'+parts.fragment
        return 'href="'+html.escape(target,quote=True)+'"'
    body=re.sub(r'href="([^"]+)"',local_link,body)
    body=re.sub(r'<table>(.*?)</table>',r'<div class="table-scroll"><table>\1</table></div>',body,flags=re.S)
    sections.append(f'<section id="{key}">{body}<p class="source"><a href="{path}">Textquelle: {html.escape(path)}</a> · <a href="#top">Nach oben</a></p></section>')
document='''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Music Generator – Tapa Fork: Dokumentation</title><style>
:root{color-scheme:light;--ink:#213047;--gold:#8b6225}*{box-sizing:border-box}body{margin:0;background:#f3f1ec;color:var(--ink);font:17px/1.65 system-ui,Segoe UI,sans-serif}header{background:#172438;color:#fff;padding:48px max(24px,calc((100vw - 1100px)/2))}header h1{font-size:clamp(25px,4vw,42px);line-height:1.2;margin:0 0 16px}header p{max-width:850px;margin:0}nav{display:flex;flex-wrap:wrap;gap:8px;max-width:1100px;margin:24px auto;padding:0 20px}nav a{border:1px solid #c6baa3;border-radius:7px;padding:8px 14px;background:#fff;text-decoration:none}main{max-width:1100px;margin:auto;padding:0 20px 55px}section{background:#fff;border:1px solid #ddd5c7;border-radius:12px;padding:clamp(20px,4vw,38px);margin:22px 0;scroll-margin-top:15px}h1,h2,h3{line-height:1.3}section h1{font-size:29px;color:#172438}h2{margin-top:32px;font-size:23px}h3{font-size:20px}a{color:#705017;overflow-wrap:anywhere}li{margin:7px 0}code{font:14px/1.5 Consolas,monospace;background:#f2eee6;padding:2px 4px;overflow-wrap:anywhere}pre{background:#172438;color:#fff;padding:18px;overflow:auto;border-radius:8px}pre code{background:transparent;color:inherit;white-space:pre}table{border-collapse:collapse;width:100%;font-size:15px;min-width:600px}th,td{border:1px solid #ded7cb;text-align:left;padding:12px;vertical-align:top}th{background:#f1ecdf}.table-scroll{overflow-x:auto}.source{font-size:14px;border-top:1px solid #ddd;padding-top:15px}strong{color:#172438}header strong{color:#fff}@media print{nav{display:none}body{background:white;font-size:11pt}header{padding:20px;background:white;color:#172438}section{break-before:page;border:none;padding:0}table{font-size:9pt;min-width:0}pre{white-space:pre-wrap}.source{display:none}}
</style></head><body id="top"><header><h1>Music Generator – Tapa Fork</h1><p>Transparenter Windows-Installationskandidat · Preview 2026.10.21<br>Einrichtung durch Doppelklick auf <strong>Install.bat</strong>. Große Komponenten werden aus den dokumentierten Quellen nachgeladen.</p></header><nav>'''+navigation+'</nav><main>'+''.join(sections)+'</main></body></html>'
(root/'DOKUMENTATION.html').write_text(document,encoding='utf-8')
print('Offline documentation generated:',len(document),'characters')
