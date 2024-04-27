from googleapiclient.discovery import build

API_KEY = 'AIzaSyBWOLedv4Zen3fwsR79NMn30Yus_VzLDbc'


class YouTubeDataCollector:
    def __init__(self, channel_id, api_key=API_KEY):
        self.channel_id = channel_id
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_channel_stats(self):
        request = self.youtube.channels().list(part='snippet,contentDetails,statistics', id=self.channel_id)
        response = request.execute()
        return response['items']

    def get_video_list(self, playlist_id):
        video_list = []
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=50
        )
        next_page = True
        while next_page:
            response = request.execute()
            data = response['items']

            for video in data:
                video_id = video['contentDetails']['videoId']
                if video_id not in video_list:
                    video_list.append(video_id)

            if 'nextPageToken' in response:
                next_page = True
                request = self.youtube.playlistItems().list(
                    part="snippet,contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=response['nextPageToken']
                )
            else:
                next_page = False

        return video_list

    def get_video_details(self, video_list):
        stats_list = []

        for i in range(0, len(video_list), 50):
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_list[i:i + 50]
            )
            response = request.execute()

            for video in response['items']:
                title = video['snippet']['title']
                published = video['snippet']['publishedAt']
                description = video['snippet']['description']
                tag_count = len(video['snippet'].get('tags', []))
                views_count = video['statistics'].get('viewCount', 0)
                dislikes_count = video['statistics'].get('dislikeCount', 0)
                likes_count = video['statistics'].get('likeCount', 0)
                comments_count = video['statistics'].get('commentCount', 0)

                stats_dictionary = dict(
                    title=title,
                    published=published,
                    description=description,
                    tag_count=tag_count,
                    views_count=views_count,
                    dislikes_count=dislikes_count,
                    likes_count=likes_count,
                    comments_count=comments_count
                )

                stats_list.append(stats_dictionary)

        return stats_list

    def get_playlist_id(self, channel_stats):
        playlist_id = channel_stats[0]['contentDetails']['relatedPlaylists']['uploads']
        return playlist_id
