import csv
import random
import os
import json
import openai
import ffmpeg

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from googleapiclient.http import MediaFileUpload




csv_file = "auto-video/quotes.csv"
start_row = 1
video_id = random.randint(1000, 9999)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

_data = {"web":{"client_id":CLIENT_ID,"project_id":"essential-rider-383902","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":CLIENT_SECRET}}


with open('auto-video/client_secret.json', 'w') as outfile:
    json.dump(_data, outfile)



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

def get_random_mp3_file(folder_path):
    mp3_files = [file for file in os.listdir(folder_path) if file.lower().endswith('.mp3')]
    if not mp3_files:
        return None
    return os.path.join(folder_path, random.choice(mp3_files))

def overlay_text_on_video(input_video_path, output_video_path,input_audio_path, text):
    (
        ffmpeg
        .input(input_video_path)
        .filter('drawtext', text=text, fontsize=60, fontcolor='white', x='(w-text_w)/2', y='(h-text_h)/2', borderw=3, bordercolor='black')
        .output('temp_video.mp4', vcodec='libx264', crf=20, preset='faster', movflags='faststart', pix_fmt='yuv420p')
        .run()
    )
    (
        ffmpeg
        .output(ffmpeg.input('temp_video.mp4'), ffmpeg.input(input_audio_path), output_video_path, shortest=None,vcodec='libx264', crf=20, preset='faster', movflags='faststart', pix_fmt='yuv420p')
        .run()
    )
    # os.remove('temp_video.mp4')
    


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

def generate_openai_description(title):
    openai.api_key = os.environ.get("OPENAI_KEY")
    prompt = f"Give me a catch close to click bait title and description for a youtube video about this quote: {title} \n \n Only respond with the title and description in json format"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )
    generated_description = json.loads(response.choices[0].text)
    return {
        "title": generated_description["title"],
        "description": generated_description["description"]
    }

def upload_to_youtube(title, description, file):

    scopes = ["https://www.googleapis.com/auth/youtube.upload"]


    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = 'auto-video/client_secret.json'

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
          "snippet": {
            "categoryId": "37",
            "description": description,
            "title": title,
            "channelId": "UC_7huW78i_4c723OTYFi_CQ"
          },
          "status": {
            "privacyStatus": "public",
            "madeForKids": False
          }
        },
        
        # TODO: For this request to work, you must replace "YOUR_FILE"
        #       with a pointer to the actual file you are uploading.
        media_body=MediaFileUpload(file)
    )
    response = request.execute()

    print(response)

    
        

if __name__ == "__main__":

    quote = generate_random_quote(csv_file, start_row)
    wrapped_quote = wrapped_text(quote)
    video_folder_path = "auto-video/input"
    output_video_path = f"auto-video/output/output{video_id}.mp4"
    input_video_path = get_random_mp4_file(video_folder_path)
    input_audio_path = get_random_mp3_file(video_folder_path)


    try:
        overlay_text_on_video(input_video_path, output_video_path,input_audio_path, text=wrapped_quote)
        print("Overlay complete.")
        print("Quote: ", quote)
        generated_info = generate_openai_description(quote)
        print(generated_info['title'])
        print(generated_info['description'])
    
    except Exception as e:
        print(e)
        print("Error occurred while overlaying text on video.")
        os.remove('temp_video.mp4')
    else:
        print("Video created successfully.")
        print("Uploading to YouTube...")
        try:
            pass
            # upload_to_youtube(title=generated_info['title'], description=generated_info['description'], file=output_video_path)
            # print("Upload complete.")
        except Exception as e:
            print(e)
            print("Error occurred while uploading video to YouTube.")
            os.remove('temp_video.mp4')
        else:
            print("Video uploaded successfully.")
            os.remove('temp_video.mp4')
            os.remove(output_video_path)
            print("Files removed.")
            


