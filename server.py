from json import load
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse


PAGES_DIR = Path('config/pages')

DEFAULT_PAGE_CONFIG = {
    'posts': 5
}

config = {
    'name': 'Name',
    'title': 'Title',
    'company': 'Company',
    'color': '#662E6C',
    'rels': [],
    'links': []
}

# read template file in
template = ''
with open('template.html', 'r') as f:
    template = f.read()

# read global config file in
config_file = PAGES_DIR / 'config.json'
if config_file.exists():
    with open(config_file, 'r') as f:
        config |= load(f)

# populate template
rels = ''.join([f'<a rel="me" href="{link}"></a>' for link in config['rels']])

links = ''
for section in config['links']:
    if links:
        links += '<span class="link-cat"></span>'

    for name in section:
        links += f'<span class="link"><a href="{section[name]}">{name}</a></span>\n'

template = template.replace('[NAME]', config['name']).replace('[TITLE]', config['title']).replace('[COMPANY]', config['company']).replace('[COLOR]', config['color']).replace('[RELS]', rels).replace('[LINKS]', links)


def get_page_config(page_dir: Path):
    """Reads the config in the given directory and XORs it with the defaults."""
    config = DEFAULT_PAGE_CONFIG.copy()
    config_file = page_dir / 'config.json'
    if config_file.exists():
        with open(config_file, 'r') as f:
            config |= load(f)

    return config


def build_page(name: str, date='', post='', index=0):
    """Populates the page template with a given page or post."""
    body = ''

    # one directory per page
    page_dir = PAGES_DIR / name
    if not page_dir.exists():
        body = build_post(name, f'Page "{name}" not found', [])
    else:
        config = get_page_config(page_dir)

        # create a post for each file, up to 5
        post_files = sorted(list(page_dir.glob('*.post')))
        if index * config['posts'] < len(post_files):
            posts = []
            for post_file in list(reversed(post_files))[index * config['posts']:]:
                try:
                    meta, content = read_post(post_file)
                    if (not date or ('date' in meta and meta['date'] == date)) and (not post or ('title' in meta and meta['title'] == post)):
                        p_date = meta['date'] if 'date' in meta else ''
                        p_link = meta['link'] if 'link' in meta else ''
                        gallery = meta['type'] == 'gallery' if 'type' in meta else False
                        posts.append(build_post(name, meta['title'], content, p_date, p_link, gallery))
                except:
                    pass

                # finish looping after 5 posts
                if len(posts) == config['posts']:
                    break

            body = ''.join(posts)
        else:
            body = build_post(name, 'No posts found', [])

        if not date and not post:
            previous = f'<a href="/?page={name}&index={index - 1}" class="nav-button">Previous</a>' if index > 0 else ''
            next = f'<a href="/?page={name}&index={index + 1}" class="nav-button">Next</a>' if len(post_files) > (index + 1) * config['posts'] else ''
            body += f'<center>{previous}{next}</center>'

    # place the posts in the page template
    return template.replace('[BODY]', body)


def read_post(post_file: Path):
    """Reads in a post file and generates post HTML."""
    meta = {}
    content = []

    with open(post_file, 'r') as f:
        # above --- is metadata, below is content
        contents = f.read().split('---')
        for pair in contents[0].strip().split('\n'):
            index = pair.index(':')
            meta[pair[:index]] = pair[index+1:].strip()

        content = contents[1].strip().split('\n')

    return meta, content


def build_post(page: str, title: str, content: list[str], date='', link='', gallery=False):
    """Generates the HTML of a post from the given parameters."""
    # create HTML for optional link(s)
    link_el = '<br>'.join([f'<a href="{l}">{l}</a>' for l in link.split(',')]) if link else ''

    # create HTML for optional date
    if date:
        date_el = f'<a class="card_title" href="?page={page}&date={date}">Posted on: {date}</a>'
        date_param = f'&date={date}'

        # add break between link and date
        if link_el:
            link_el = '<br>' + link_el
    else:
        date_el = ''
        date_param = ''

    if not gallery:
        # put two breaks between each paragraph
        body = ' '.join([line if line else '<br><br>' for line in content])
    else:
        # assume each line is a path to an image
        body = ''.join([f'<img src="{url}">' for url in content])

    return f'<div class="card">\
    <div class="post-header">\
        <span class="post-left">\
            <h1 class="post-title">\
                <a class="card_title" href="?page={page}{date_param}&title={title}">{title}</a>\
            </h1>\
            <p class="post-date">\
                <i>\
                    {date_el}\
                </i>\
            </p>\
        </span>\
        <span class="post-right">\
            <p class="post-links">\
                <i>\
                    {link_el}\
                </i>\
            </p>\
        </span>\
    </div>\
    <p class="post-content">{body}</p>\
</div>'


# create an instance of FastAPI
app = FastAPI()

# serve the index, builds each page from query parameters
@app.get('/', response_class=HTMLResponse)
async def index(page: str = 'home', date: str = '', title: str = '', index: int = 0):
    return build_page(page, date, title, index)

@app.get('/styles.css', response_class=FileResponse)
async def styles():
    return 'styles.css'

@app.get('/{file_path:path}', response_class=FileResponse)
async def assets(file_path):
    return f'config/assets/{file_path}'
