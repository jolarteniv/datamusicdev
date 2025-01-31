from flask import Flask, send_file
import os

app = Flask(__name__)
output_file = '${efs_mount_point}/event_log.txt'

@app.route('/')
def get_event_log():
    if os.path.exists(output_file):
        return send_file(output_file, as_attachment=False)
    else:
        return "No hay eventos procesados."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)