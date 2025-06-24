from django.db import models
from django.urls import reverse

# Create your models here.

class News(models.Model):
    headline = models.CharField(max_length=255)
    news_content = models.TextField()
    news_link = models.URLField()
    image_url = models.URLField()
    news_date = models.DateTimeField()
    tags = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    categories = models.CharField(max_length=100)
    news_id = models.IntegerField(unique=True)
    author_name = models.CharField(max_length=100)
    source_domain = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-news_date']
        verbose_name_plural = 'News'

    def __str__(self):
        return self.headline

    def get_absolute_url(self):
        """Return the URL for the news detail page."""
        return reverse('news:news_detail', args=[str(self.news_id)])

    def get_categories_list(self):
        """Return list of categories from comma-separated string."""
        if not self.categories:
            return []
        return [cat.strip().title() for cat in self.categories.split(',') if cat.strip()]
