from flask import Flask, send_from_directory, request, jsonify, Response
from voronoi_engine import generate_preview_geometry, generate_voronoi
import traceback

app = Flask(__name__, static_folder="static")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/preview", methods=["POST"])
def preview():
    try:
        params = request.get_json(force=True) or {}
        shapes = generate_preview_geometry(params)
        return jsonify({"shapes": shapes})
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


@app.route("/download", methods=["POST"])
def download():
    try:
        params = request.get_json(force=True) or {}
        dxf_bytes = generate_voronoi(params)
        return Response(
            dxf_bytes,
            mimetype="application/dxf",
            headers={
                "Content-Disposition": "attachment; filename=voronoi.dxf",
                "Content-Length": str(len(dxf_bytes)),
            },
        )
    except Exception:
        return jsonify({"error": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
