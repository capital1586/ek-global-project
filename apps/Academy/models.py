from django.db import models
from django.utils import timezone

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.URLField(blank=True, null=True, help_text="URL to the course image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class LearningOutcome(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_outcomes')
    outcome = models.CharField(max_length=255)
    
    def __str__(self):
        return self.outcome

class Video(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos', null=True, blank=True)
    title = models.CharField(max_length=200)
    youtube_id = models.CharField(max_length=20, help_text="The YouTube video ID")
    description = models.TextField()
    published_date = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
    @property
    def youtube_url(self):
        return f"https://www.youtube.com/watch?v={self.youtube_id}"
    
    @property
    def embed_url(self):
        return f"https://www.youtube.com/embed/{self.youtube_id}"

class NewsArticle(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    source = models.CharField(max_length=100)
    url = models.URLField()
    published_date = models.DateTimeField(default=timezone.now)
    image_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.title

class Benefit(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, help_text="Font Awesome icon class", blank=True)
    
    def __str__(self):
        return self.title
