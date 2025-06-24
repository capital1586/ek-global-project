# news/models.py
from django.db import models
from django.utils import timezone

class News(models.Model):
    news_id = models.IntegerField(unique=True, primary_key=True) # Assuming NewsID is the unique identifier
    headline = models.CharField(max_length=255)
    news_content = models.TextField(blank=True, null=True)
    news_link = models.URLField(max_length=500, blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    news_date = models.DateTimeField(null=True, blank=True, db_index=True) # Index for ordering
    tags = models.CharField(max_length=255, blank=True, null=True) # Store as string, parse in template/view if needed
    description = models.TextField(blank=True, null=True)
    categories = models.CharField(max_length=255, blank=True, null=True)
    author_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-news_date'] # Default ordering
        verbose_name_plural = "News"

    def __str__(self):
        return self.headline

    def get_tags_list(self):
        """ Returns tags as a list, splitting by comma or space. """
        if not self.tags:
            return []
        # Try splitting by comma first, then space if no commas found
        if ',' in self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        else:
            return [tag.strip() for tag in self.tags.split() if tag.strip()] # Splits by whitespace