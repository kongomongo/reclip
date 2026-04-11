import os
import uuid
import glob
import json
import subprocess
import threading
import time
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

jobs = {}


def run_download(job_id, url, format_choice, format_id):
    job = jobs[job_id]
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    cmd = ["yt-dlp", "--no-playlist", "-o", out_template]

    if format_choice == "audio":
        cmd += ["-x", "--audio-format", "mp3"]
    elif format_id:
        cmd += ["-f", f"{format_id}+bestaudio/best", "--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]

    cmd.append(url)

    process = None
    output_lines = []          # <-- NEW: collect all output for error extraction

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,   # merge everything so we never miss progress
            text=True,
            bufsize=1
        )

        job["progress"] = 0
        job["total_size"] = None

        last_update = time.time()
        start_time = time.time()

        while True:
            line = process.stdout.readline()
            if not line:
                break

            output_lines.append(line)          # save for later error parsing

            current_time = time.time()

            # === No-progress kill (60 seconds of silence) ===
            if current_time - last_update > 60:
                process.kill()
                job["status"] = "error"
                job["error"] = "No progress received for 1 minute"
                break

            # === Safety hard timeout (5 min total) ===
            if current_time - start_time > 300:
                process.kill()
                job["status"] = "error"
                job["error"] = "Download timed out (5 min limit)"
                break

            last_update = current_time

            # === Parse progress + filesize ===
            if '[download]' in line and '%' in line:
                try:
                    parts = line.split()
                    # percentage
                    for p in parts:
                        if '%' in p:
                            perc_str = p.rstrip('%')
                            job["progress"] = int(float(perc_str))
                            break
                    # total size (right after "of")
                    if 'of' in parts:
                        idx = parts.index('of') + 1
                        if idx < len(parts):
                            job["total_size"] = parts[idx]
                except (ValueError, IndexError):
                    pass

        # Process finished normally
        returncode = process.wait()

        if job.get("status") == "error":
            return  # already set by timeout/no-progress

        if returncode != 0:
            job["status"] = "error"
            # Restore original behavior: take the last meaningful error line
            error_msg = "Download failed."
            for line in reversed(output_lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('[download]'):
                    error_msg += stripped
                    break
            job["error"] = error_msg
            return

        # === Post-download file handling (unchanged) ===
        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
        if not files:
            job["status"] = "error"
            job["error"] = "Download completed but no file was found"
            return

        if format_choice == "audio":
            target = [f for f in files if f.endswith(".mp3")]
            chosen = target[0] if target else files[0]
        else:
            target = [f for f in files if f.endswith(".mp4")]
            chosen = target[0] if target else files[0]

        for f in files:
            if f != chosen:
                try:
                    os.remove(f)
                except OSError:
                    pass

        job["status"] = "done"
        job["file"] = chosen
        ext = os.path.splitext(chosen)[1]
        title = job.get("title", "").strip()
        # Sanitize title for filename
        if title:
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()[:20].strip()
            job["filename"] = f"{safe_title}{ext}" if safe_title else os.path.basename(chosen)
        else:
            job["filename"] = os.path.basename(chosen)

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
    finally:
        if process and process.poll() is None:
            process.kill()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cmd = ["yt-dlp", "--no-playlist", "-j", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip().split("\n")[-1]}), 400

        info = json.loads(result.stdout)

        # Build quality options — keep best format per resolution
        best_by_height = {}
        for f in info.get("formats", []):
            height = f.get("height")
            if height and f.get("vcodec", "none") != "none":
                tbr = f.get("tbr") or 0
                if height not in best_by_height or tbr > (best_by_height[height].get("tbr") or 0):
                    best_by_height[height] = f

        formats = []
        for height, f in best_by_height.items():
            formats.append({
                "id": f["format_id"],
                "label": f"{height}p",
                "height": height,
            })
        formats.sort(key=lambda x: x["height"], reverse=True)

        return jsonify({
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "formats": formats,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timed out fetching video info"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    title = data.get("title", "")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    job_id = uuid.uuid4().hex[:10]
    jobs[job_id] = {
        "status": "downloading",
        "url": url,
        "title": title,
        "progress": 0,
        "total_size": None
    }

    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({
        "status": job["status"],
        "error": job.get("error"),
        "filename": job.get("filename"),
        "progress": job.get("progress") if job["status"] == "downloading" else None,
        "total_size": job.get("total_size") if job["status"] == "downloading" else None
    })


@app.route("/api/file/<job_id>")
def download_file(job_id):
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "File not ready"}), 404
    return send_file(job["file"], as_attachment=True, download_name=job["filename"])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8899))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port)
