from datetime import date
import ffmpeg
import csv
import random
import os



csv_file = "auto-video/quotes.csv"
start_row = 1

#function taht genrates random 4 digits
def generate_random_digits():
    return random.randint(1000, 9999)

video_id = generate_random_digits()

def generate_random_quote(csv_file, start_row):
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        quotes = list(reader)
    
    if len(quotes) == 0:
        return "No quotes available."
    
    if not (0 <= start_row < len(quotes)):
        return "Invalid start row."
    
    end_row = len(quotes) - 1
    random_quote = random.choice(quotes[start_row:end_row+1])  # Adjust the range
    book = random_quote[0]
    chapter = random_quote[1]
    page = random_quote[2]
    quote = random_quote[3]

    formatted_quote = f'"{quote}" - {book} {chapter}:{page}'
    return formatted_quote

def get_random_mp4_file(folder_path):
    mp4_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.mp4')]
    if not mp4_files:
        return None
    return os.path.join(folder_path, random.choice(mp4_files))

def overlay_text_on_video(input_video_path, output_video_path, text):
    (
        ffmpeg
        .input(input_video_path)
        .filter('drawtext', text=text, fontsize=40, fontcolor='white', x='(w-text_w)/2', y='(h-text_h)/2', boxborderw=5, font='Aharoni-Bold')
        # .output(output_video_path, vcodec='libx264', crf=20, preset='faster', movflags='faststart')
        .output(output_video_path, vcodec='libx264', acodec='copy', crf=20, preset='faster', movflags='faststart')
        .run()
    )

def wrapped_text(text, max_line_length=30):
    words = text.split()
    lines = []
    current_line = words[0]
    for word in words[1:]:
        if len(current_line) + len(word) + 1 <= max_line_length:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return "\n\n".join(lines)

if __name__ == "__main__":
    quote = generate_random_quote(csv_file, start_row)
    wrapped_quote = wrapped_text(quote)
    print(quote)
    video_folder_path = "auto-video/input"
    output_video_path = f"auto-video/output/output{video_id}.mp4"
    print(f"Output video path: {output_video_path}")
    input_video_path = get_random_mp4_file(video_folder_path)
    if input_video_path:
        try:
            overlay_text_on_video(input_video_path, output_video_path, text=wrapped_quote)
            print("Overlay complete.")
        except Exception as e:
            print(f"Error: {e}")
            
    else:
        print("No MP4 files found in the folder.")



