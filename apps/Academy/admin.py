from django.contrib import admin
from .models import Course, LearningOutcome, Video, NewsArticle, Benefit

class LearningOutcomeInline(admin.TabularInline):
    model = LearningOutcome
    extra = 1

class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    readonly_fields = ('youtube_url',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    inlines = [LearningOutcomeInline, VideoInline]

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'youtube_id', 'published_date')
    list_filter = ('course', 'published_date')
    search_fields = ('title', 'description', 'youtube_id')
    readonly_fields = ('youtube_url', 'embed_url')

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'source', 'published_date')
    list_filter = ('source', 'published_date')
    search_fields = ('title', 'content', 'source')

@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon')
    search_fields = ('title', 'description')
