import io
from PIL import Image, ImageDraw, ImageFont

class Visualizer:
    def __init__(self):
        self.background_path = 'C:/Users/Hisham/Desktop/Projeler/Upgraded music bot/assets/chopper.jpg'
        self.title_font_path = 'C:/Users/Hisham/Desktop/Projeler/Upgraded music bot/assets/pirata.ttf'
        self.song_font_path = 'C:/Users/Hisham/Desktop/Projeler/Upgraded music bot/assets/pirata.ttf'
        self.items_per_page = 5

    async def generate_queue_image(self, user_queue, page=1):
        background = Image.open(self.background_path).convert('RGBA')
        img_width, img_height = background.size

        base_width = 800
        width_percent = base_width / float(img_width)
        height_size = int(float(img_height) * width_percent)
        background = background.resize((base_width, height_size), Image.LANCZOS)

        try:
            title_font = ImageFont.truetype(self.title_font_path, 50)
            song_font = ImageFont.truetype(self.song_font_path, 40)
        except IOError:
            title_font = ImageFont.load_default()
            song_font = ImageFont.load_default()

        draw = ImageDraw.Draw(background)

        start_index = (page - 1) * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(user_queue))

        current_y = 200

        for index, song in enumerate(user_queue[start_index:end_index]):
            status_image = "pending.png"
            if song.get('status') == 'playing':
                status_image = "playing.png"
            elif song.get('status') == 'completed':
                status_image = "completed.png"

            status_img = Image.open(f"C:/Users/Hisham/Desktop/Projeler/Upgraded music bot/assets/{status_image}").convert("RGBA")
            emoji_size = status_img.size

            song_text = f"{start_index + index + 1}. {song['title']}"

            text_bbox = draw.textbbox((0, 0), song_text, font=song_font)
            song_text_width = text_bbox[2] - text_bbox[0]
            song_text_height = text_bbox[3] - text_bbox[1]
            table_width = song_text_width + 20
            table_height = song_text_height + 20
            table_x = 20
            table_y = current_y

            table = Image.new('RGBA', (table_width + emoji_size[0], table_height), (0, 0, 0, 150))
            draw_table = ImageDraw.Draw(table)
            shadow_offset = 2
            shadow_color = (0, 0, 0, 128)
            draw_table.text((10 + shadow_offset + emoji_size[0] + 5, 10 + shadow_offset), song_text, font=song_font, fill=shadow_color)
            draw_table.text((10 + 5, 10), song_text, font=song_font, fill=(255, 255, 255))

            background.paste(table, (table_x + emoji_size[0], table_y), table)
            background.paste(status_img, (table_x, table_y), status_img)

            current_y += table_height + 10

        buffer = io.BytesIO()
        background.save(buffer, format='PNG', optimize=True, quality=30)
        buffer.seek(0)
        return buffer
