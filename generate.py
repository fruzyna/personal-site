from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse

def generate_page(name: str, index=0, post=''):
    page_dir = Path('pages') / name
    if not page_dir.exists():
        return

    template = ''
    with open('index.html', 'r') as f:
        template = f.read()

    print(post if post else '*.post')
    post_files = list(page_dir.glob(post if post else '*.post'))
    start = min(index * 5, len(post_files) - 1)
    end = min((index + 1) * 5, len(post_files))
    posts = [generate_post(post_file, name) for post_file in post_files[start:end]]

    return template.replace('BODY', ''.join(posts))


def generate_post(post_file: Path, name: str):
    meta = {}
    content = []
    with open(post_file, 'r') as f:
        contents = f.read().split('---')
        for pair in contents[0].strip().split('\n'):
            index = pair.index(':')
            meta[pair[:index]] = pair[index+1:].strip()

        content = contents[1].strip().split('\n')

    link = f'<br>Source: <a href="{meta['link']}">{meta['link']}</a>' if 'link' in meta else ''
    body = '<br><br>'.join(content)
    return f'<div class="card">\
<h1 class="post-title">\
    <a class="card_title" href="?page={name}&date={meta["date"]}&title={meta["title"]}">{meta["title"]}</a>\
</h1>\
<p class="post-date">\
    <i>\
        <a class="card_title" href="?page={name}&date={meta["date"]}">Posted on: {meta["date"]}</a>\
        {link}\
    </i>\
</p>\
<p id="{post_file.name}" class="post-content">{body}</p>\
</div>'

# create an instance of FastAPI
app = FastAPI()

@app.get('/', response_class=HTMLResponse)
async def index(request: Request, page: str = 'home'):
    return generate_page(page)

@app.get('/{file_path}', response_class=FileResponse)
async def other(file_path):
    return file_path

@app.get('/assets/{file_path}', response_class=FileResponse)
async def assets(file_path):
    return f'assets/{file_path}'
