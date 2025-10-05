from django.contrib import admin
from .models import Message, Notification, MessageHistory

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'edited', 'last_edited_at', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('edited', 'timestamp')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'verb', 'is_read', 'timestamp', 'message')
    search_fields = ('user__username', 'verb')
    list_filter = ('is_read', 'timestamp')


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'editor', 'edited_at')
    search_fields = ('message__id', 'old_content', 'editor__username')
    readonly_fields = ('old_content', 'edited_at')
