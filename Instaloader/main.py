import os
import re
import asyncio
import shutil
from instaloader import instaloader , Profile
from Config import INSTA_USERNAME, INSTA_PASSWORD
from pyrogram import Client, filters
from .database.users_sql import get_info


@Client.on_message(filters.private & ~filters.regex(r'^/'))
async def main(_, msg):
    if 'instagram.com' not in msg.text:
        return
    status = await msg.reply('Please Wait...', quote=True)
    pattern = re.compile(r'^(https?:[/][/])?(www\.)?instagram.com[/](p|reel|tv|stories)[/]([A-Za-z0-9-_]+)')
    matches = pattern.search(msg.text)
    type_link = matches.group(3)
    if type_link == 'stories':
        pattern_link = re.compile(r'^(https?:[/][/])?(www\.)?instagram.com[/](p|reel|tv|stories)[/]([A-Za-z0-9-_]+)[/]([A-Za-z0-9-_]+)')
        matches_link = pattern_link.search(str(msg.text))
        p_user = matches_link.group(4)
        p_id = matches_link.group(5)
        username, password = await get_info(msg.from_user.id)
        if not username:
            username = INSTA_USERNAME
            password = INSTA_PASSWORD
        
        L = instaloader.Instaloader() 
        L.login(user=username,passwd=password)
        profilee = Profile.from_username(L.context,p_user)

        pattern = re.compile(r'^<Profile ([A-Za-z0-9-_]+) [(]([A-Za-z0-9-_]+)[)]>')
        matches = pattern.search(str(profilee))
        #p_user = matches.group(1)
        p_ids = matches.group(2)

        #stories = 
        id_int = int(p_ids)
        for story in L.get_stories(userids=[id_int]):
        # story is a Story object
        #print(story)
            for items in story.get_items():
                # item is a StoryItem object
                pattern2 = re.compile(r'^<StoryItem ([A-Za-z0-9-_]+)>')
                mat = pattern2.search(str(items))
                media_id = mat.group(1)
                print(media_id)
                
                if media_id == p_id :
                    f = L.download_storyitem(items, ':stories')
                    pattern_link = re.compile(r'^:stories[/]([A-Za-z0-9-_]+).(jpg|mp4)')
                    matches_link = pattern_link.search(str(f))
                    p_user = matches_link.group(1)
                    p_id = matches_link.group(2)
                    ps = p_user+p_id
                    path = f":stories/{ps}"
                    photos, videos, caption = post_prep(path)
                    if photos:
                        for photo in photos:
                            await msg.reply_photo(photo)
                    if videos:
                        for video in videos:
                            await msg.reply_video(video)
                    #print(f)
                    break
    
    try:
        matches = pattern.search(msg.text)
        post_id = matches.group(4)
        username, password = await get_info(msg.from_user.id)
        if not username:
            username = INSTA_USERNAME
            password = INSTA_PASSWORD
        if username and password:
            command = f"instaloader --no-metadata-json -l {username} -p {password} -- -{post_id}"
        else:
            command = f"instaloader --no-metadata-json -- -{post_id}"
        proc = await asyncio.subprocess.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if "wrong password" in str(stderr).lower():
            raise Exception('Wrong Instagram Password.')
        path = f"-{post_id}"
        photos, videos, caption = post_prep(path)
        if not photos and not videos:
            await status.delete()
            await msg.reply("No Such Instagram Post Exists.")
            return
        if len(photos+videos) == 1:
            if caption:
                caption += "\n\nBy @masoudartwork"
            else:
                caption = "By @masoudartwork"
            if photos:
                for photo in photos:
                    await msg.reply_photo(photo, caption)
            if videos:
                for video in videos:
                    await msg.reply_video(video, caption)
        else:
            if photos:
                for photo in photos:
                    await msg.reply_photo(photo)
            if videos:
                for video in videos:
                    await msg.reply_video(video)
            if caption:
                await msg.reply(f"**POST CAPTION : **\n\n{caption} \n\nBy @masoudartwork")
        await status.delete()
        shutil.rmtree(path)
    except AttributeError:
        await status.delete()
        await msg.reply(error)


error = """
Please send me a valid instagram post link.
It must be like one of the given below
**Note** : To get profile picture of a account use "`/profile_pic instagram-username`". Link won't work.
"""


def post_prep(path):
    if not os.path.isdir(path):
        return None, None, None
    files = os.listdir(path)
    photos = []
    videos = []
    caption = ""
    for file in files:
        if file.endswith(".jpg"):
            photos.append(path+'/'+file)
        if file.endswith(".mp4"):
            videos.append(path+'/'+file)
        if file.endswith(".txt"):
            with open(f"{path}/{file}") as f:
                caption = f.read()
    return photos, videos, caption
