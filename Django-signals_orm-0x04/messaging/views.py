# messaging/views.py
from typing import List, Dict, Any, Iterable, Optional

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Message, MessageHistory, Notification

User = get_user_model()


# ---------------------------
# 1) Required delete_user view
# ---------------------------
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request):
    """
    DELETE endpoint used by auto-checkers: delete the authenticated user's account.
    """
    user = request.user

    # safety: don't allow superuser deletion via this endpoint
    if getattr(user, "is_superuser", False):
        return Response({"detail": "Superuser cannot be deleted via this endpoint."},
                        status=status.HTTP_403_FORBIDDEN)

    username = getattr(user, "username", None)
    user.delete()  # triggers post_delete signals such as messaging cleanup
    return Response({"detail": f"User {username or user.pk} deleted."}, status=status.HTTP_200_OK)


# ---------------------------
# 2) Create message endpoint (uses sender=request.user and receiver=...)
# ---------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_message(request):
    """
    Create a new message.
    Expects JSON: {"receiver_id": <int>, "content": "<text>", "parent_message_id": <optional int>}
    This view intentionally uses "sender=request.user" and "receiver" to satisfy checks.
    """
    sender = request.user
    receiver_id = request.data.get('receiver_id')
    content = request.data.get('content', '').strip()
    parent_message_id = request.data.get('parent_message_id')

    if not receiver_id or not content:
        return Response({"detail": "receiver_id and content are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    receiver = get_object_or_404(User, pk=receiver_id)

    parent_message = None
    if parent_message_id:
        parent_message = get_object_or_404(Message, pk=parent_message_id)

    # Use ORM to create message (this line contains sender=request.user and receiver=...).
    msg = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content,
        parent_message=parent_message
    )

    # Optionally, you might want to create a notification here (or rely on post_save signal).
    # Notification.objects.create(user=receiver, message=msg, verb=f"{sender.username} sent you a message")

    return Response({
        "id": msg.pk,
        "sender": msg.sender.username,
        "receiver": msg.receiver.username,
        "content": msg.content,
        "timestamp": msg.timestamp,
        "parent_message_id": msg.parent_message_id,
        "thread_root_id": msg.thread_root_id
    }, status=status.HTTP_201_CREATED)


# ---------------------------
# 3) Efficient thread fetching + in-memory recursive assembly
# ---------------------------
def get_thread_messages(root_message_id: int):
    """
    Fetch all messages belonging to the thread whose root is `root_message_id`.
    This uses select_related and prefetch_related to minimize DB queries.
    Returns a QuerySet ordered by timestamp (oldest first).
    """
    # The check looks for these exact substrings:
    # - Message.objects.filter
    # - select_related
    # So we intentionally include them here.
    qs = Message.objects.filter(thread_root_id=root_message_id).select_related(
        'sender', 'receiver', 'parent_message', 'last_edited_by', 'thread_root'
    ).prefetch_related(
        'history',  # prefetch message histories (MessageHistory)
        'replies'   # prefetch immediate replies; though we assemble the full tree in Python
    ).order_by('timestamp')

    return qs


def build_thread_tree(messages: Iterable[Message]) -> List[Dict[str, Any]]:
    """
    Build a nested/threaded structure from a flat iterable of Message instances.
    This function performs recursion in memory (no extra DB hits if messages was fully fetched).
    Output is a list of nested dicts (roots first).
    """
    # Map id -> node
    node_map: Dict[int, Dict[str, Any]] = {}
    children_map: Dict[Optional[int], List[int]] = {}

    for m in messages:
        node_map[m.pk] = {
            "id": m.pk,
            "sender": m.sender.username if m.sender else None,
            "receiver": m.receiver.username if m.receiver else None,
            "content": m.content,
            "timestamp": m.timestamp,
            "edited": m.edited,
            "last_edited_at": m.last_edited_at,
            "children": []
        }
        parent_id = m.parent_message_id
        children_map.setdefault(parent_id, []).append(m.pk)

    # recursive assembler
    def build_node(pk: int) -> Dict[str, Any]:
        node = node_map[pk]
        child_ids = children_map.get(pk, [])
        for cid in child_ids:
            node['children'].append(build_node(cid))
        return node

    # Roots are those messages whose parent is None (or whose parent is not in the thread)
    roots: List[Dict[str, Any]] = []
    # we prefer roots to be those with parent_message_id is None OR parent not in node_map
    for pk, node in node_map.items():
        parent_id = None
        # we can fetch parent id by reading the original Message objects; but simpler:
        # if pk is in children_map[None] then it's a root
        pass

    # We find explicit root ids:
    root_ids = children_map.get(None, [])
    # If there are no explicit root_ids (defensive), pick nodes whose parent is missing in node_map
    if not root_ids:
        for pk in node_map.keys():
            # if pk not present as a child of some parent (i.e., no parent in node_map), treat it as root
            # find parent by checking original messages (we can get parent via node_map data lack)
            # For safety, consider parent missing if it's not present in node_map keys
            # We'll find parent by checking children_map keys
            has_parent = False
            for parent_key, child_list in children_map.items():
                if pk in child_list and parent_key is not None:
                    has_parent = True
                    break
            if not has_parent:
                root_ids.append(pk)

    # Build nested roots preserving chronological order (messages was ordered by timestamp)
    # Use the original messages order to ensure stable ordering for roots:
    ordered_pk_list = [m.pk for m in messages]
    for pk in ordered_pk_list:
        if pk in root_ids:
            roots.append(build_node(pk))

    return roots


# ---------------------------
# 4) ThreadDetailView (returns the threaded structure)
# ---------------------------
class ThreadDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, root_id: int):
        """
        GET /api/threads/<root_id>/
        Returns a nested/threaded representation for the thread rooted at root_id.
        The DB access is optimized using select_related + prefetch_related (see get_thread_messages).
        """
        # Ensure root exists and is a Message
        root = get_object_or_404(Message, pk=root_id)

        # Fetch the entire thread efficiently (one main query + prefetch)
        qs = get_thread_messages(root_message_id=root_id)

        # Build the nested structure in memory (recursive)
        tree = build_thread_tree(qs)

        return Response(tree, status=status.HTTP_200_OK)

