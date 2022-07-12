import subprocess
import pytube, time, os
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


def stream_manager(streams):
    def num_trim(s):
        res = ''
        for c in s:
            if c.isdigit(): res += c
            else: return int(res)
    
    def process_size(s):
        size = round(s / 1024, 2)
        if size < 2048: size = str(size) + " KB"
        else: size = str(round(size / 1024, 2)) + " MB"
        return size

    s, final, res = [], [], []
    for x in streams:
        x = str(x).replace(' ', ', "').replace('=', '":')
        x = eval("{" + x[10:-1] + "}")
        x['mime_type'] = x['mime_type'].split('/')[1]
        s.append(x)

    for ind, x in enumerate(s):
        if 'vcodec' in x and 'acodec' in x:
            final.append([ind, 'v', x['mime_type'], x['res'], streams[ind].filesize])
        elif 'vcodec' in x:
            final.append([ind, 'u', x['mime_type'], x['res'], streams[ind].filesize])
        else:
            final.append([ind, 'a', x['mime_type'], x['abr'], streams[ind].filesize])

    mem = dict()
    for x in final:
        if x[1] in ['v', 'u']:
            pix = num_trim(x[3])
            if pix not in mem or (mem[pix][1] == 'u' and mem[pix][4] < x[4]): mem[pix] = x
    all_qual = list(mem.keys())
    all_qual.sort(reverse=True)

    for q in all_qual: res.append(mem[q])

    mem = dict()
    for x in final:
        if x[1] == 'a': mem[num_trim(x[3])] = x
    all_qual = list(mem.keys())
    all_qual.sort(reverse=True)

    for q in all_qual: res.append(mem[q])

    for i in range(len(res)):
        res[i][4] = process_size(res[i][4])

    max_audio_size = mem[all_qual[0]][4]
    for i in range(len(res)):
        if res[i][1] == 'u':
            res[i][2] = 'mp4'
            res[i][4] = res[i][4][:-2] + "+ " + max_audio_size

    return res


@app.route('/')
def start():
    return render_template('start.html')


@app.route('/video', methods=['POST', 'GET'])
def get_video():
    if request.method == 'POST':
        global video
        global streams
        global max_audio
        link = request.form['link']
        try:
            video = pytube.YouTube(link)
        except:
            return render_template('video.html', warn=True)
        else:
            streams = stream_manager(video.streams)
            for i in streams:
                if i[1] == 'a':
                    max_audio = i[0]
                    break
            return redirect(url_for('get_stream'))
    return render_template('video.html', warn=False)


@app.route('/stream', methods=['POST', 'GET'])
def get_stream():
    if request.method == 'POST':
        global choice
        choice = request.form['stream_choice']
        return redirect(url_for('get_download'))
    return render_template('streams.html',
                           title=video.title,
                           thumb=video.thumbnail_url,
                           duration=time.strftime(
                               '%H:%M:%S', time.gmtime(video.length)),
                           streams=streams)


@app.route('/download_video', methods=['POST', 'GET'])
def get_download():
    path = ".\\static\\"
    # path = "/app/static/"
    for file in os.listdir(path):
        if file[-4:] == ".mp4": os.remove(path+file)
    name = video.streams[int(choice)].default_filename
    stream = str(video.streams[int(choice)])
    if stream.find('acodec') != -1:
        video.streams[int(choice)].download(path, name)
    else:
        name = name.replace('webm', 'mp4')
        video.streams[int(choice)].download(path, "video")
        video.streams[max_audio].download(path, "audio")
        cmd = f'ffmpeg -i {path}video -i {path}audio -c:v copy -c:a aac {path}output.mp4'
        subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.rename(rf"{path}output.mp4", rf"{path}{name}")
        os.remove(rf"{path}video")
        os.remove(rf"{path}audio")
    return render_template('download_video.html', name=name)


@app.route('/playlist')
def get_playlist():
    if request.method == 'POST':
        global video
        global streams
        global max_audio
        link = request.form['link']
        try:
            video = pytube.YouTube(link)
        except:
            return render_template('video.html', warn=True)
        else:
            streams = stream_manager(video.streams)
            for i in streams:
                if i[1] == 'a':
                    max_audio = i[0]
                    break
            return redirect(url_for('get_stream'))
    return render_template('playlist.html')


if __name__ == "__main__":
    app.run(debug=True, port=8080)
