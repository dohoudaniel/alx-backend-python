from django.urls import path
from .views import MessageHistoryListView, MessageUpdateView

urlpatterns = [
    # GET /api/messages/<pk>/history/  (list)
    path('messages/<int:message_pk>/history/', MessageHistoryListView.as_view(), name='message-history'),

    # GET/PUT /api/messages/<pk>/  (update)
    path('messages/<int:pk>/', MessageUpdateView.as_view(), name='message-update'),
]

