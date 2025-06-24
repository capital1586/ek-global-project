from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import requests
import json
import os
import re
import googleapiclient.discovery
from datetime import timedelta
from .models import Course, Video, NewsArticle, Benefit
from .utils import create_mock_data

def index(request):
    # Create mock data if needed
    if Course.objects.count() == 0 or Video.objects.count() == 0:
        create_mock_data()
    
    # Get all courses
    courses = Course.objects.all().prefetch_related('learning_outcomes', 'videos')
    
    # Get featured videos
    featured_videos = Video.objects.filter(course__isnull=False).order_by('-published_date')[:6]
    
    # Get latest news
    news = NewsArticle.objects.order_by('-published_date')[:4]
    
    # Get benefits
    benefits = Benefit.objects.all()
    
    # Fetch the latest YouTube videos if not in cache
    youtube_videos = get_youtube_videos()
    
    context = {
        'courses': courses,
        'featured_videos': featured_videos,
        'youtube_videos': youtube_videos,
        'news': news,
        'benefits': benefits,
    }
    
    return render(request, 'Academy/index.html', context)

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    videos = course.videos.all().order_by('-published_date')
    learning_outcomes = course.learning_outcomes.all()
    
    context = {
        'course': course,
        'videos': videos,
        'learning_outcomes': learning_outcomes,
    }
    
    return render(request, 'Academy/course_detail.html', context)

def video_detail(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    related_videos = Video.objects.filter(course=video.course).exclude(id=video.id).order_by('-published_date')[:5]
    
    context = {
        'video': video,
        'related_videos': related_videos,
    }
    
    return render(request, 'Academy/video_detail.html', context)

def get_youtube_videos():
    """Fetch latest videos from YouTube channel and cache them"""
    cache_key = 'youtube_videos'
    cached_videos = cache.get(cache_key)
    
    if cached_videos:
        return cached_videos
    
    try:
        # Try to use YouTube Data API if the API key is available
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if api_key:
            youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
            
            # Get channel uploads
            channel_response = youtube.channels().list(
                part='contentDetails',
                forUsername='ekglobalcapital4400',
                maxResults=1
            ).execute()
            
            if not channel_response['items']:
                # Try with channel ID if username doesn't work
                channel_response = youtube.channels().list(
                    part='contentDetails',
                    id='UCrLmA_vhB8kRkr_6e6mBVjw',  # EK Global Capital channel ID
                    maxResults=1
                ).execute()
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from the uploads playlist
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=10
            ).execute()
            
            videos = []
            for item in playlist_response['items']:
                snippet = item['snippet']
                video_id = snippet['resourceId']['videoId']
                
                # Check if we already have this video in the database
                existing_video = Video.objects.filter(youtube_id=video_id).first()
                if not existing_video:
                    # Create a new Video object
                    video = Video(
                        title=snippet['title'],
                        description=snippet['description'],
                        youtube_id=video_id,
                        published_date=snippet.get('publishedAt', timezone.now())
                    )
                    video.save()
                
                # Add to the response list
                videos.append({
                    'id': video_id,
                    'title': snippet['title'],
                    'description': snippet['description'],
                    'thumbnail': snippet['thumbnails']['high']['url'],
                    'published_at': snippet.get('publishedAt', '')
                })
                
            # Cache the results for 1 hour
            cache.set(cache_key, videos, 60*60)
            return videos
            
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        # If API fails, use the stored videos in the database
        db_videos = Video.objects.all().order_by('-published_date')[:10]
        videos = []
        for video in db_videos:
            videos.append({
                'id': video.youtube_id,
                'title': video.title,
                'description': video.description,
                'thumbnail': f"https://img.youtube.com/vi/{video.youtube_id}/hqdefault.jpg",
                'published_at': video.published_date.isoformat()
            })
        
        # Cache the results for 1 hour
        cache.set(cache_key, videos, 60*60)
        return videos

def fetch_latest_news():
    """Fetch latest financial news from a news API"""
    cache_key = 'latest_news'
    cached_news = cache.get(cache_key)
    
    if cached_news:
        return cached_news
    
    try:
        # Try to use News API if the API key is available
        api_key = os.environ.get('NEWS_API_KEY')
        if api_key:
            url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={api_key}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                for article in articles[:10]:  # Process the top 10 articles
                    # Check if we already have this article by matching the title or URL
                    title = article.get('title', '')
                    url = article.get('url', '')
                    
                    if not title or not url:
                        continue
                    
                    existing_article = NewsArticle.objects.filter(title=title).first()
                    if not existing_article:
                        # Create a new NewsArticle object
                        news_article = NewsArticle(
                            title=title,
                            content=article.get('description', ''),
                            source=article.get('source', {}).get('name', 'Unknown'),
                            url=url,
                            published_date=article.get('publishedAt', timezone.now()),
                            image_url=article.get('urlToImage', '')
                        )
                        news_article.save()
                
                # Return the latest news from the database
                latest_news = NewsArticle.objects.order_by('-published_date')[:8]
                
                # Cache the results for 1 hour
                cache.set(cache_key, latest_news, 60*60)
                return latest_news
                
    except Exception as e:
        print(f"Error fetching news: {e}")
        
    # Return latest news from the database if API fails
    return NewsArticle.objects.order_by('-published_date')[:8]
