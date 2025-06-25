from django.urls import path
from .views import ThreadListView, ThreadDetailView, SendMessageView

urlpatterns = [
    path('all/', ThreadListView.as_view(), name='list-threads'),
    path('thread/<uuid:thread_id>/', ThreadDetailView.as_view(), name='thread-detail'),
    path('<uuid:user_id>/send/', SendMessageView.as_view(), name='send-message'),
]