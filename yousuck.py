import subprocess
import pytube, time, os
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)


def video_stream_manager(streams):
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


def playlist_stream_manager(playlist):
    n = playlist.length
    print(n)
    all_videos = playlist.videos
    print(all_videos)
    print(len(all_videos))
    res = []
    for i in range(len(all_videos)):
        print(i)
        vid = all_videos[i]
        res.append([i+1,
                    vid.thumbnail_url,
                    vid.title,
                    time.strftime('%H:%M:%S', time.gmtime(vid.length))])
    return res


@app.route('/')
def start():
    return render_template('index.html')


@app.route('/video_link', methods=['POST', 'GET'])
def get_video_link():
    if request.method == 'POST':
        global video_obj
        global video_streams
        global Video_max_audio
        link = request.form['video_link']
        try:
            video_obj = pytube.YouTube(link)
        except:
            return render_template('video_link.html', warn=True)
        else:
            video_streams = video_stream_manager(video_obj.streams)
            for i in video_streams:
                if i[1] == 'a':
                    Video_max_audio = i[0]
                    break
            return redirect(url_for('get_video_streams'))
    return render_template('video_link.html', warn=False)


@app.route('/video_streams', methods=['POST', 'GET'])
def get_video_streams():
    if request.method == 'POST':
        global video_stream_choice
        video_stream_choice = request.form['stream_choice']
        return redirect(url_for('get_video_download'))
    return render_template('video_streams.html',
                           title=video_obj.title,
                           thumb=video_obj.thumbnail_url,
                           duration=time.strftime(
                               '%H:%M:%S', time.gmtime(video_obj.length)),
                           streams=video_streams)


@app.route('/video_download', methods=['POST', 'GET'])
def get_video_download():
    path = "./static/"
    for file in os.listdir(path):
        if file[-4:] == ".mp4": os.remove(path+file)
    name = video_obj.streams[int(video_stream_choice)].default_filename
    stream = str(video_obj.streams[int(video_stream_choice)])
    if stream.find('acodec') != -1:
        video_obj.streams[int(video_stream_choice)].download(path, name)
    else:
        name = name.replace('webm', 'mp4')
        video_obj.streams[int(video_stream_choice)].download(path, "video")
        video_obj.streams[Video_max_audio].download(path, "audio")
        cmd = f'ffmpeg -i {path}video -i {path}audio -c:v copy -c:a aac {path}output.mp4'
        subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.rename(rf"{path}output.mp4", rf"{path}{name}")
        os.remove(rf"{path}video")
        os.remove(rf"{path}audio")
    return render_template('video_download.html', name=name)


@app.route('/playlist_link', methods=['POST', 'GET'])
def get_playlist_link():
    if request.method == 'POST':
        global playlist_obj
        global playlist_videos
        link = request.form['playlist_link']
        try:
            playlist_obj = pytube.Playlist(link)
            if not playlist_obj: raise Exception('Fraud URL')
        except:
            return render_template('playlist_link.html', warn=True)
        else:
            playlist_videos = playlist_stream_manager(playlist_obj)
            print(playlist_videos)
            return redirect(url_for('get_playlist_streams'))
    return render_template('playlist_link.html')


@app.route('/playlist_streams', methods=['POST', 'GET'])
def get_playlist_streams():
    return render_template('playlist_streams.html', streams=playlist_videos, length=len(playlist_videos))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
