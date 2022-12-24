from flask import Flask, jsonify
from pathlib import Path
from configparser import ConfigParser

cfg = ConfigParser(interpolation=None)
cfg.read('config.ini', encoding='utf-8')
general = cfg['General']
dir_abspath = general.get('SavePath', '')
filename = general.get('JsonResultFilename', 'proxies.json')
jsonfile_abspath = f'{dir_abspath}/{filename}'

app = Flask(__name__)

@app.route('/')
def proxy_page():
    if Path(jsonfile_abspath).is_file():
        with Path(jsonfile_abspath).open('r', encoding='utf-8') as target:
            return app.response_class(
                response=target.read(),
                mimetype='application/json'
            )
    else:
        return app.response_class(
            response="{}",
            mimetype='application/json'
        )

# Release
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

# Debug
# app.run(debug=True, host='0.0.0.0', port=5000)