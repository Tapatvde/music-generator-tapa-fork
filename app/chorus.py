"""Section tags describe lyrics, not timestamps. Alignment supplies the latter."""
import re
import unicodedata

ALIGNMENT_VERSION = 'mms-chorus-v1'


def lyric_sections(text):
    sections=[];current={'tag':'untagged','chorus':False,'lines':[]}
    for part in re.split(r'(\[[^\]\n]+\])', text or ''):
        if part.startswith('[') and part.endswith(']'):
            if current['lines']:sections.append(current)
            tag=part[1:-1].strip().lower()
            is_chorus=bool(re.match(r'^(?:final\s+)?(?:chorus|refrain)(?:\b|$)',tag))
            current={'tag':tag,'chorus':is_chorus,'lines':[]}
        else:
            current['lines'].extend(line.strip() for line in part.splitlines() if line.strip())
    if current['lines']:sections.append(current)
    return sections


def selected_lyrics(song):
    import json
    meta=song.get('result_meta') or '{}'
    meta=json.loads(meta) if isinstance(meta,str) else meta
    return (meta.get('lyrics') or song.get('lyrics') or '').strip()


def alignment_words(text):
    text=unicodedata.normalize('NFKD',text.lower().replace('ß','ss').replace('’',"'"))
    text=''.join(c for c in text if not unicodedata.combining(c))
    if re.search(r'[^\x00-\x7f]',text) or re.search(r'\d',text):
        raise ValueError('Der lokale Refrainabgleich benötigt lateinische Schrift und ausgeschriebene Zahlen.')
    return re.findall(r"[a-z]+(?:'[a-z]+)*",text)


def validate_auto_lyrics(text, require_chorus=True):
    sections=lyric_sections(text)
    choruses=[s for s in sections if s['chorus']]
    if require_chorus and not choruses:
        raise ValueError('Für die Automatik fehlen [chorus]-Abschnitte mit Text in den Lyrics.')
    count=sum(len(alignment_words(line)) for s in sections for line in s['lines'])
    if count<3 or count>3000:
        raise ValueError('Der Refrainabgleich benötigt 3 bis 3000 ausgeschriebene Wörter.')
    return sections


def section_kind(tag):
    if re.match(r'^(?:verse|strophe)(?:\b|$)',tag):return 'verse'
    if re.match(r'^(?:final\s+)?(?:chorus|refrain)(?:\b|$)',tag):return 'chorus'
    return 'other'


def section_catalog(text):
    counts={};result=[]
    for index,section in enumerate(lyric_sections(text)):
        kind=section_kind(section['tag']);counts[kind]=counts.get(kind,0)+1
        result.append({'section':index,'tag':section['tag'],'kind':kind,
                       'number':counts[kind],'first_line':section['lines'][0]})
    return result


def chorus_regions(sections, aligned_lines, duration, all_sections=False):
    """Reject unsupported text/time matches; never spread tags over song length."""
    result=[];rejected=[]
    for index, section in enumerate(sections):
        if not all_sections and not section['chorus']:continue
        lines=[line for line in aligned_lines if line['section']==index]
        words=[w for line in lines for w in line['words']]
        reason=None
        if not words or len(lines)!=len(section['lines']):reason='unvollständiger Textabgleich'
        elif sum(w['score'] for w in words)/len(words)<.2:reason='zu geringe Zuverlässigkeit'
        elif sum(w['score']<.1 for w in words)/len(words)>.35:reason='zu viele unsichere Wörter'
        elif any(line['end']-line['start']>max(12.,len(line['words'])*1.5) for line in lines):reason='unplausible Zeilendauer'
        elif any(b['start']-a['end']>6 for a,b in zip(lines,lines[1:])):reason='zu große Lücke im Refrain'
        elif words[-1]['end']-words[0]['start']<.5:reason='zu kurzer Textabgleich'
        if reason:
            rejected.append({'section':index,'tag':section['tag'],'reason':reason});continue
        next_line=next((line for line in aligned_lines if line['section']>index),None)
        start=max(0.,words[0]['start']-.12)
        end=min(duration,words[-1]['end']+.3,next_line['start']-.04 if next_line else duration)
        if end-start<.5:
            rejected.append({'section':index,'tag':section['tag'],'reason':'Zeitbereich kollidiert mit nächstem Abschnitt'});continue
        if result and start<result[-1]['end']:start=result[-1]['end']
        if end-start<.5:
            rejected.append({'section':index,'tag':section['tag'],'reason':'überlappender Zeitbereich'});continue
        result.append({'start':round(start,3),'end':round(end,3),'section':index,'tag':section['tag'],
                       'score':round(sum(w['score'] for w in words)/len(words),3)})
    return result,rejected
