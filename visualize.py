import os
from PIL import Image, ImageDraw, ImageFont

def create_playlist_image(songs, current_song_title, output_path):
    # Arka plan motor resmi
    background_image_path = 'C:\\Users\\Hisham\\Desktop\\Projeler\\DC bot\\Biso\\chopper.jpg'
    background = Image.open(background_image_path)

    # Şeffaf filtre oluşturma
    overlay = Image.new('RGBA', background.size, (0, 0, 0, 150))  # Siyah şeffaf filtre
    background.paste(overlay, (0, 0), overlay)

    # Yazı fontları
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        song_font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        title_font = ImageFont.load_default()
        song_font = ImageFont.load_default()

    draw = ImageDraw.Draw(background)

    # Başlık yazısını ekleme
    title_text = "ŞARKILAR"
    title_text_size = draw.textbbox((0, 0), title_text, font=title_font)  # Güncellenmiş yöntem
    title_position = ((background.width - (title_text_size[2] - title_text_size[0])) // 2, 30)
    draw.text(title_position, title_text, font=title_font, fill="white")

    # Şarkı listesini ekleme
    y_offset = 120
    for song in songs:
        song_text = f"{song['title']} - {song['artist']}"
        if song['title'] == current_song_title:
            song_text = f"🎵 {song_text}"
        draw.text((50, y_offset), song_text, font=song_font, fill="white")
        y_offset += 50

    # Şarkı bitişi tik emojisi ekleme
    if current_song_title:
        draw.text((50, y_offset), f"✅ {current_song_title} bitti", font=song_font, fill="white")

    # Resmi kaydetme
    try:
        background.save(output_path)
        print(f"Resim başarıyla kaydedildi: {output_path}")
    except IOError as e:
        print(f"Resim kaydedilirken hata oluştu: {e}")

# Örnek kullanım
songs = [
    {'title': 'Şarkı 1', 'artist': 'Sanatçı 1'},
    {'title': 'Şarkı 2', 'artist': 'Sanatçı 2'},
    {'title': 'Şarkı 3', 'artist': 'Sanatçı 3'},
]

current_song = 'Şarkı 2'
output_path = 'C:\\Users\\Hisham\\Desktop\\Projeler\\DC bot\\Biso\\playlist_image.png'
create_playlist_image(songs, current_song, output_path)
