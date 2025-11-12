from flask import Flask, render_template_string, jsonify, request
import os
import base64
import mimetypes
import threading
import time
import copy
import random
from typing import Dict

app = Flask(__name__)

var_name_to_ref: Dict[str, object] = dict()



HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Nested Dict Debug Viewer</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 1rem; }
    ul { list-style-type: none; margin-left: 1rem; padding-left: 1rem; border-left: 1px dotted #ddd; }
    /* Lines between items inside the tree */
    #tree ul li { border-bottom: 1px solid #e6e6e6; padding: 0.35rem 0; margin-bottom: 0.25rem; }
    #tree ul li:last-child { border-bottom: none; margin-bottom: 0; }
    .key { font-weight: bold; margin-right: 0.25rem; }
    .value { color: #064; }
    .collapsed > ul { display: none; }
    .toggle { cursor: pointer; color: #06c; margin-right: 0.5rem; }
    .container { max-width: 1000px; }
    /* Image preview styling */
    .img-preview { max-width: 420px; max-height: 320px; display: block; margin-top: 0.25rem; border: 1px solid #ddd; padding: 2px; background: #fff; }
    .img-caption { font-size: 0.85rem; color: #666; margin-top: 0.25rem; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Nested Dict Debug Viewer</h1>

    <div id="tree">
      {{ tree_html|safe }}
    </div>
  </div>

  <script>
    document.addEventListener('click', function (e) {
      if (e.target.classList.contains('toggle')) {
        var node = e.target.closest('.node');
        if (node) node.classList.toggle('collapsed');
      }
    });
  </script>
</body>
</html>
"""


def render_nested(obj, key=""):
    """Recursively render a Python object (dict/list/scalar) to nested HTML lists.

    Special-case: when a string value begins with 'data:image/png;base64,', render an <img>
    preview instead of raw text.
    """
    def esc(s):
        # escape for HTML text content
        return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def esc_attr(s):
        # escape for HTML attribute values (minimal)
        return str(s).replace('&', '&amp;').replace('"', '&quot;').replace("'", '&#x27;')

    # handle strings first (so startswith is only called on strings)
    if isinstance(obj, str):
        # 1) embedded base64 data URLs for images: data:<mime>;base64,...
        if obj.startswith('data:') and ';base64,' in obj:
            try:
                header, _ = obj.split(',', 1)
                # header looks like 'data:image/png;base64' -> mime becomes 'image/png'
                mime = header[5:].split(';', 1)[0] or ''
            except Exception:
                mime = ''
            if mime.startswith('image/'):
                src = esc_attr(obj)
                caption = esc(mime + ' (base64)')
                alt = esc_attr('embedded ' + mime)
                return f'<div class="img-container"><img class="img-preview" src="{src}" alt="{alt}" /><div class="img-caption">{caption}</div></div>'

        # 2) remote image URLs (http/https) — simple heuristic by extension
        lower = obj.lower()
        if lower.startswith(('http://', 'https://')):
            for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'):
                if lower.split('?')[0].endswith(ext):
                    src = esc_attr(obj)
                    return f'<div class="img-container"><img class="img-preview" src="{src}" alt="remote image" /><div class="img-caption">Remote image URL</div></div>'

        # 3) local file path: if it exists and is an image, inline it as a data URL
        try:
            if os.path.isfile(obj):
                data_url = file_to_data_url(obj)
                if data_url:
                    src = esc_attr(data_url)
                    fname = esc(os.path.basename(obj))
                    alt = esc_attr(fname)
                    return f'<div class="img-container"><img class="img-preview" src="{src}" alt="{alt}" /><div class="img-caption">Local file: {fname}</div></div>'
        except Exception:
            # if anything goes wrong with filesystem checks, fall back to plain text
            pass

        # regular string (non-image)
        return f"<span class=\"value\">{esc(obj)}</span>"

    if isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            items.append(f"<li><span class=\"key\">{esc(k)}</span>: {render_nested(v, k)}</li>")
        return f"<div class=\"node\"><span class=\"toggle\">[+/-]</span><ul>{''.join(items)}</ul></div>"
    elif isinstance(obj, list):
        items = []
        for i, v in enumerate(obj):
            items.append(f"<li><span class=\"key\">[{i}]</span> {render_nested(v, str(i))}</li>")
        return f"<div class=\"node\"><span class=\"toggle\">[+/-]</span><ul>{''.join(items)}</ul></div>"
    else:
        # non-string scalars: escape for safe HTML
        return f"<span class=\"value\">{esc(obj)}</span>"


@app.route('/')
def index():
    var_name = request.args.get('key', None)
    if var_name and var_name in var_name_to_ref:
        tree_html = render_nested(var_name_to_ref[var_name])
    else:
        tree_html = "No variable selected or variable not found."
        tree_html += "<h2>Available Variables:</h2>"
        for name in var_name_to_ref.keys():
            tree_html += f'<div><a href="/?key={name}">{name}</a></div>'

    return render_template_string(HTML_TEMPLATE, tree_html=tree_html)

def start_server_in_thread(host='0.0.0.0', port=5000):
    """Start the Flask app in a background daemon thread and return the Thread object.

    Notes:
    - debug and the reloader must be disabled when running in a background thread.
    - the thread is created as a daemon so it will stop when the main program exits.
    """
    def run():
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    t = threading.Thread(target=run, daemon=True, name='flask-server-thread')
    t.start()
    return t

def register_variable(name: str, ref: object, service_url: str = "0.0.0.0:5000"):
    """Register a variable by name for inspection in the web UI."""
    var_name_to_ref[name] = ref
    print(f"Registered variable '{name}' for inspection at {service_url}/?key={name}")

if __name__ == '__main__':
    # Start the Flask server in a background thread
    port_use = 5000
    server_thread: threading.Thread = None
    while port_use < 10000:
        try:
            server_thread = start_server_in_thread(host='0.0.0.0', port=port_use)
            break
        except OSError as e:
            print(f"Unable to start server on port {port_use}, trying another: {e}")
            port_use += random.randint(1, 100)
            time.sleep(0.5)

    service_url = f'http://0.0.0.0:{port_use}'
    # monitor_thread = start_monitor_in_thread(
    #     var_getter=lambda: SAMPLE_NESTED,
    #     interval=2.0,
    #     on_change=lambda prev, cur: print('SAMPLE_NESTED changed!', prev, '->', cur)
    # )

    print('Flask server started in background on http://0.0.0.0:{used_port}')


    # ================== TEST SAMPLE DATA ==================
    def file_to_data_url(filepath):
        """Return a data URL (base64) for the given file, or empty string if missing/unsupported."""
        if not os.path.isfile(filepath):
            return ''
        mime, _ = mimetypes.guess_type(filepath)
        if not mime or not mime.startswith('image/'):
            return ''
        try:
            with open(filepath, 'rb') as fh:
                data = fh.read()
            b64 = base64.b64encode(data).decode('ascii')
            return f'data:{mime};base64,{b64}'
        except Exception:
            return ''

    # compute paths relative to this file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    JPG_PATH = os.path.join(BASE_DIR, 'test_image.jpg')
    PNG_PATH = os.path.join(BASE_DIR, 'test_image.png')

    # these will be empty strings if the files are not present
    _raw_jpg = file_to_data_url(JPG_PATH)
    _raw_png = file_to_data_url(PNG_PATH)
    # use a visible placeholder if missing
    test_jpg_base64 = _raw_jpg if _raw_jpg else '[missing: test_image.jpg]'
    test_png_base64 = _raw_png if _raw_png else '[missing: test_image.png]'

    # Sample nested dictionary to display
    SAMPLE_NESTED = {
        "name": "root",
        "count": 0,
        "test_jpg": test_jpg_base64,
        "test_png": test_png_base64,
        "sample_png": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVQImWNgYAAAAAMAAWgmWQ0AAAAASUVORK5CYII=",
        "children": [
            {"name": "child1", "value": 1},
            {
                "name": "child2",
                "children": [
                    {"name": "grandchild1", "value": "a"},
                    {"name": "grandchild2", "value": "b"}
                ]
            },
            {"name": "child3", "dict": {"a": 10, "b": [1, 2, {"x": "y"}]}}
        ],
        "meta": {"created": "2025-11-12", "tags": ["demo", "debug"]}
    }

    register_variable('SAMPLE_NESTED', SAMPLE_NESTED, service_url=service_url)

    try:
        while True:
            time.sleep(1)
            SAMPLE_NESTED['count'] += 1  # example modification to trigger monitor
    except KeyboardInterrupt:
        print('\nShutting down (KeyboardInterrupt).')
