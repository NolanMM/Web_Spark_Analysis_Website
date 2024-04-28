from datetime import datetime, timedelta

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import re
import requests

from Services.DataCollector.Youtube_Data_Collector import YouTubeDataCollector

url_sample = "https://www.youtube.com/"


class PysparkModule:
    chanel_id = ""
    channel_name = ""
    number_of_videos = 0

    def __init__(self, channel_name):
        self.channel_name = channel_name
        self.spark = SparkSession.builder.appName("PysparkModule").getOrCreate()

    def get_channel_id(self):
        url_request = url_sample + self.channel_name
        response = requests.get(url_request)
        if response.status_code == 200:
            data = response.text
            match = re.search(r'"key":"browse_id","value":"([^"]+)"', data)
            if match:
                value = match.group(1)
                self.chanel_id = value
            else:
                self.chanel_id = None
        return self.chanel_id

    def collect_data(self):
        youtube_collector = YouTubeDataCollector(self.chanel_id)
        channel_stats = youtube_collector.get_channel_stats()
        playlist_id = youtube_collector.get_playlist_id(channel_stats)
        video_list = youtube_collector.get_video_list(playlist_id)
        number_of_videos = len(video_list)
        self.number_of_videos = number_of_videos
        video_data = youtube_collector.get_video_details(video_list)
        transformed_data_ = self.transform_data(video_data)
        return transformed_data_

    def transform_data(self, video_data):
        df = self.spark.createDataFrame(video_data)
        df = df.withColumn("VideoID", F.monotonically_increasing_id()) \
            .withColumn("ViewCount", df["views_count"].cast("int")) \
            .withColumn("LikeCount", df["likes_count"].cast("int")) \
            .withColumn("DislikesCount", df["dislikes_count"].cast("int")) \
            .withColumn("CommentsCount", df["comments_count"].cast("int")) \
            .withColumn("AdditionalInformation", F.concat(F.lit("Additional Info "), F.col("VideoID")))

        total_views = df.agg(F.sum("ViewCount")).collect()[0][0]
        total_likes = df.agg(F.sum("LikeCount")).collect()[0][0]
        total_dislikes = df.agg(F.sum("DislikesCount")).collect()[0][0]
        total_engagement = df.agg(F.sum("CommentsCount")).collect()[0][0]
        df = df.withColumn("published", F.to_date("published"))
        monthly_data = df.where(F.col("published") >= F.date_sub(F.current_date(), 365)) \
            .groupBy(F.month("published").alias("month")) \
            .agg(F.sum("ViewCount").alias("views"),
                 F.sum("LikeCount").alias("likes"),
                 F.sum("DislikesCount").alias("dislikes"),
                 F.sum("CommentsCount").alias("engagement")) \
            .orderBy("month") \
            .collect()

        labels = [datetime.now().replace(month=month).strftime('%B') for month in range(1, 13)]
        views = [row["views"] for row in monthly_data]
        likes = [row["likes"] for row in monthly_data]
        dislikes = [row["dislikes"] for row in monthly_data]
        engagement = [row["engagement"] for row in monthly_data]

        data = {
            'table_data': df.collect(),
            'TotalViews': total_views,
            'TotalLikes': total_likes,
            'TotalDislikes': total_dislikes,
            'TotalEngagement': total_engagement,
            'labels': labels,
            'views': views,
            'likes': likes,
            'dislikes': dislikes,
            'engagement': engagement
        }

        return data

    def get_monthly_data(self, video_data):
        monthly_data = {month: {'views': 0, 'likes': 0, 'dislikes': 0, 'engagement': 0} for month in range(1, 13)}
        one_year_ago = datetime.now() - timedelta(days=365)

        for video in video_data:
            published_date = datetime.strptime(video['published'], "%Y-%m-%dT%H:%M:%SZ")
            if published_date >= one_year_ago:
                month = published_date.month
                # Convert view_count, like_count, dislikes_count, comments_count to int
                view_count = int(video['views_count'])
                likes_count = int(video['likes_count'])
                dislikes_count = int(video['dislikes_count'])
                comments_count = int(video['comments_count'])
                monthly_data[month]['views'] += view_count
                monthly_data[month]['likes'] += likes_count
                monthly_data[month]['dislikes'] += dislikes_count
                monthly_data[month]['engagement'] += comments_count

        labels = [datetime.now().replace(month=month).strftime('%B') for month in range(1, 13)]
        views = [monthly_data[month]['views'] for month in range(1, 13)]
        likes = [monthly_data[month]['likes'] for month in range(1, 13)]
        dislikes = [monthly_data[month]['dislikes'] for month in range(1, 13)]
        engagement = [monthly_data[month]['engagement'] for month in range(1, 13)]

        return {
            'labels': labels,
            'views': views,
            'likes': likes,
            'dislikes': dislikes,
            'engagement': engagement
        }

    def stop(self):
        self.spark.stop()


if __name__ == "__main__":
    # Create start time
    start_time = datetime.now()
    pyspark_module = PysparkModule("@Optimus96")
    channel_id = pyspark_module.get_channel_id()
    transformed_data = pyspark_module.collect_data()
    print(transformed_data)
    pyspark_module.stop()
    end_time = datetime.now()
    # print processing time
    print("Processing time: ", end_time - start_time)

