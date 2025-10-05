from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Message, MessageHistory
from .serializers import MessageHistorySerializer, MessageSerializer

class MessageHistoryListView(generics.ListAPIView):
    """
    List edit history for a given message id (pass message pk as query param or in URL).
    """
    serializer_class = MessageHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Expect message id in URL kwargs or ?message_id=<id>
        message_id = self.kwargs.get('message_pk') or self.request.query_params.get('message_id')
        return MessageHistory.objects.filter(message_id=message_id).order_by('-edited_at')


class MessageUpdateView(generics.RetrieveUpdateAPIView):
    """
    Example update view: when saving edits, we attach request.user to the instance
    as a transient attribute so the pre_save signal can record the editor.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        instance = serializer.instance
        # attach transient attribute used by the signal
        instance._editor = self.request.user
        serializer.save()

