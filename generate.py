import csv
import os
from collections import defaultdict

KLEUREN = {
    '1': '#d9c043',
    '2': '#fe6836',
    '3': '#56aadf',
    '4': '#ab58e3',
    '5': '#4bd7da',
}

PAGINAS = {
    '1': 'stikstof.html',
    '2': 'klimaat.html',
    '3': 'routes.html',
    '4': 'stad.html',
    '5': 'overig.html',
}

def is_video(filename):
    return filename.lower().endswith(('.mp4', '.webm', '.mov'))

def parse_list(val):
    return [f.strip() for f in val.split(',') if f.strip()] if val.strip() else []

def parse_teksten(val):
    return [t.strip() for t in val.split('|')] if val.strip() else []

def nav_html():
    return '''<nav>
  <a class="nav-name" href="index.html">Tim Tensen</a>
  <ul class="nav-links">
    <li><a href="index.html">Werk</a></li>
    <li><a href="over.html">Over</a></li>
    <li><a href="mailto:tim@timtensen.nl">Contact</a></li>
  </ul>
</nav>'''

def gallery_js():
    return '''<script>
  function initGallery(gallery, withText) {
    const items = gallery.querySelectorAll('.gallery-item');
    const prevBtn = gallery.querySelector('.prev');
    const nextBtn = gallery.querySelector('.next');
    const captionEl = gallery.querySelector('.gallery-caption');
    const counterEl = gallery.querySelector('.gallery-counter');
    const progress = gallery.querySelector('.gallery-progress');
    let current = 0;
    const total = items.length;

    function stopAllVideos() {
      items.forEach(item => {
        const v = item.querySelector('video');
        if (v) { v.pause(); v.currentTime = 0; }
      });
      if (progress) progress.style.width = '0%';
    }

    function animateTextIn(item) {
      if (!withText) return;
      const txt = item.querySelector('.slide-text');
      if (!txt) return;
      txt.classList.remove('exit-up', 'visible');
      requestAnimationFrame(() => requestAnimationFrame(() => txt.classList.add('visible')));
    }

    function animateTextOut(item, callback) {
      if (!withText) { callback(); return; }
      const txt = item.querySelector('.slide-text');
      if (!txt) { callback(); return; }
      txt.classList.remove('visible');
      txt.classList.add('exit-up');
      setTimeout(callback, 320);
    }

    function startVideo(item) {
      const video = item.querySelector('video');
      if (!video) { if (progress) progress.style.width = '0%'; return; }
      video.loop = item.dataset.loop === 'true';
      video.currentTime = 0;
      video.play().catch(() => {});
      video.addEventListener('timeupdate', function onTime() {
        if (!video.duration) return;
        if (progress) progress.style.width = (video.currentTime / video.duration * 100) + '%';
        if (video.ended) {
          video.removeEventListener('timeupdate', onTime);
          if (progress) progress.style.width = '100%';
        }
      });
    }

    function goTo(index) {
      const next = (index + total) % total;
      if (next === current) return;
      const previous = current;
      animateTextOut(items[previous], () => {
        stopAllVideos();
        items[previous].classList.remove('active');
        current = next;
        items[current].classList.add('active');
        if (captionEl) captionEl.textContent = items[current].dataset.caption || '';
        if (counterEl) counterEl.textContent = (current + 1) + ' / ' + total;
        prevBtn.classList.toggle('hidden', current === 0);
        nextBtn.classList.toggle('hidden', current === total - 1);
        animateTextIn(items[current]);
        startVideo(items[current]);
      });
    }

    prevBtn.addEventListener('click', () => goTo(current - 1));
    nextBtn.addEventListener('click', () => goTo(current + 1));

    // Init
    items[0].classList.add('active');
    prevBtn.classList.add('hidden');
    nextBtn.classList.toggle('hidden', total <= 1);
    if (captionEl) captionEl.textContent = items[0].dataset.caption || '';
    if (counterEl) counterEl.textContent = '1 / ' + total;
    animateTextIn(items[0]);
    startVideo(items[0]);
  }

  document.querySelectorAll('.gallery-plain').forEach(g => initGallery(g, false));
  document.querySelectorAll('.gallery-tekstvak').forEach(g => initGallery(g, true));
</script>'''

def arrow_btns():
    return '''        <div class="gallery-nav">
          <button class="gallery-btn prev hidden" aria-label="Vorige">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="11,3 5,9 11,15"/></svg>
          </button>
          <button class="gallery-btn next" aria-label="Volgende">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="7,3 13,9 7,15"/></svg>
          </button>
        </div>'''

def media_tag_inline(filename):
    """Voor losse images/videos onder elkaar."""
    if is_video(filename):
        return f'<video src="images/{filename}" autoplay loop muted playsinline></video>'
    else:
        alt = filename.rsplit('.', 1)[0].replace('_', ' ')
        return f'<img src="images/{filename}" alt="{alt}">'

def gallery_item_html(filename, caption, tekstvak_tekst, index):
    active = ' active' if index == 0 else ''
    loop = 'true' if index == 0 else 'false'
    if is_video(filename):
        tag = f'<video src="images/{filename}" muted playsinline preload="auto"></video>'
        badge = '<div class="video-badge">animatie</div>\n        '
    else:
        alt = filename.rsplit('.', 1)[0].replace('_', ' ')
        tag = f'<img src="images/{filename}" alt="{alt}">'
        badge = ''
    tekstvak = f'\n        <div class="slide-text">{tekstvak_tekst}</div>' if tekstvak_tekst else ''
    return f'''      <div class="gallery-item{active}" data-caption="{caption}" data-loop="{loop}">
        {badge}{tag}{tekstvak}
      </div>'''

def losse_images_html(files, teksten):
    blocks = []
    for i, f in enumerate(files):
        caption = teksten[i] if i < len(teksten) else f.rsplit('.', 1)[0].replace('_', ' ')
        tag = media_tag_inline(f)
        blocks.append(f'''  <div class="media-blok">
    <div class="media-frame">{tag}</div>
    <p class="media-caption">{caption}</p>
  </div>''')
    return '\n'.join(blocks)

def flourish_html(url, caption=''):
    if not url.strip():
        return ''
    return f'''  <div class="media-blok">
    <div class="media-frame" style="padding: 0.5rem; box-shadow: 6px 6px 14px rgba(0,0,0,0.32);">
      <div class="flourish-embed" data-src="{url.strip()}">
        <script src="https://public.flourish.studio/resources/embed.js"></script>
        <noscript><img src="https://public.flourish.studio/{url.strip()}/thumbnail" width="100%" alt="visualization" /></noscript>
      </div>
    </div>
    <p class="media-caption">{caption}</p>
  </div>'''

def gallery_html(files, teksten, tekstvak_teksten, gallery_id, with_text):
    cls = 'gallery-tekstvak' if with_text else 'gallery-plain'
    items_html = []
    for i, f in enumerate(files):
        caption = teksten[i] if i < len(teksten) else f.rsplit('.', 1)[0].replace('_', ' ')
        tekstvak = tekstvak_teksten[i] if with_text and i < len(tekstvak_teksten) else ''
        items_html.append(gallery_item_html(f, caption, tekstvak, i))

    total = len(files)
    first_caption = teksten[0] if teksten else (files[0].rsplit('.', 1)[0].replace('_', ' ') if files else '')

    footer = f'''      <div class="gallery-footer">
        <span class="gallery-caption">{first_caption}</span>
        <span class="gallery-counter">1 / {total}</span>
      </div>''' if with_text else ''

    caption_html = f'    <p class="media-caption">{first_caption}</p>' if not with_text and teksten else ''

    return f'''  <div class="media-blok">
    <div class="media-frame">
    <div class="gallery {cls}" id="{gallery_id}">
      <div class="gallery-stage">
{chr(10).join(items_html)}
        <div class="gallery-progress"></div>
{arrow_btns()}
      </div>
{footer}
    </div>
    </div>
{caption_html}
  </div>'''

def case_html(row, gallery_counter):
    titel = row['case']
    opdrachtgever = row['opdrachtgever']
    naam_images   = parse_list(row.get('naam_images', ''))
    naam_gallery  = parse_list(row.get('naam_gallery', ''))
    naam_gmt      = parse_list(row.get('naam_gallery_met_tekstvak', ''))
    tekst_images  = parse_teksten(row.get('tekst_images', ''))
    tekst_gallery = parse_teksten(row.get('tekst_gallery', ''))
    tekst_gmt     = parse_teksten(row.get('tekst_gallery_met_tekstvak', ''))
    flourish_url  = row.get('flourish_url', '').strip()
    flourish_cap  = row.get('tekst_flourish', '').strip()

    content = []
    tekst_case = row.get('tekst_case', '').strip()
    if tekst_case:
        content.append(f'  <p class="case-tekst">{tekst_case}</p>')
        
    if naam_images:
        content.append(losse_images_html(naam_images, tekst_images))

    if naam_gallery:
        gid = f'gallery-{gallery_counter[0]}'
        gallery_counter[0] += 1
        content.append(gallery_html(naam_gallery, tekst_gallery, [], gid, with_text=False))

    if naam_gmt:
        gid = f'gallery-{gallery_counter[0]}'
        gallery_counter[0] += 1
        content.append(gallery_html(naam_gmt, tekst_gmt, tekst_gmt, gid, with_text=True))

    if flourish_url:
        content.append(flourish_html(flourish_url, flourish_cap))

    return f'''<div class="case">
  <div class="case-header">
    <div class="case-opdrachtgever">{opdrachtgever}</div>
    <h2 class="case-titel">{titel}</h2>
  </div>
{chr(10).join(content)}
</div>'''

def generate_page(nr, naam, cases, accent):
    cases_html = '\n\n'.join(cases)
    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{naam.capitalize()} — Tim Tensen</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="shared.css">
  <style>:root {{ --accent: {accent}; }}</style>
</head>
<body>

{nav_html()}

<main>

  <div class="hoofdstuk-header">
    <a class="terug" href="index.html">← Alle hoofdstukken</a>
    <div class="accent-lijn"></div>
    <h1>{naam.capitalize()}</h1>
  </div>

{cases_html}

</main>

<footer>
  <p>© 2025 Tim Tensen</p>
  <a href="mailto:tim@timtensen.nl">tim@timtensen.nl</a>
</footer>

{gallery_js()}

</body>
</html>'''

# ── RUN ──
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'website.csv')

rows = []
with open(csv_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

hoofdstukken = defaultdict(list)
for row in rows:
    nr = row['hoofdstuknr'].strip()
    if nr:
        hoofdstukken[nr].append(row)

output_dir = script_dir

for nr, cases_rows in sorted(hoofdstukken.items()):
    naam = cases_rows[0]['hoofdstuknaam'].strip()
    accent = KLEUREN.get(nr, '#888884')
    filename = PAGINAS.get(nr, f'hoofdstuk{nr}.html')
    gallery_counter = [1]
    cases = [case_html(row, gallery_counter) for row in cases_rows]
    html = generate_page(nr, naam, cases, accent)
    path = os.path.join(output_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Gegenereerd: {filename}')

print('Klaar.')
