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
        link = request.form['link']
        video = pytube.YouTube(link)
        streams = stream_manager(video.streams)
        return redirect(url_for('get_stream'))
    return render_template('video.html')


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
    name = video.streams[int(choice)].default_filename
    video.streams[int(choice)].download(".\\static")
    return render_template('download_video.html', name=name)


@app.route('/playlist')
def get_playlist():
    return render_template('playlist.html')


if __name__ == "__main__":
    # app.run(debug=True, port=8080)
    app.run(debug=True, port=process.env.PORT)
