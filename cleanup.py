import psutil

def find_ffmpeg_processes():
    """Çalışan ffmpeg işlemlerini bulur."""
    ffmpeg_processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        if 'ffmpeg' in proc.info['name']:
            ffmpeg_processes.append(proc.info['pid'])
    return ffmpeg_processes

def terminate_ffmpeg_processes():
    """Tüm ffmpeg işlemlerini sonlandırır."""
    ffmpeg_pids = find_ffmpeg_processes()
    for pid in ffmpeg_pids:
        try:
            # PID kullanarak işlemi sonlandır
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=5)  # İşlemin sonlanmasını bekle
        except psutil.NoSuchProcess:
            # İşlem zaten sonlanmış olabilir
            pass
        except psutil.AccessDenied:
            # İşleme erişim izni olmayabilir
            pass
        except psutil.TimeoutExpired:
            # İşlem belirli bir süre içinde sonlanmazsa
            process.kill()