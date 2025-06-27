from django.urls import path
from .views import ThreadListView, ThreadDetailView, SendMessageView, MessagingView,MessageEditView,MessageDeleteView,DeleteAllThreadsView,DeleteThreadView

urlpatterns = [
    path('all/', ThreadListView.as_view(), name='list-threads'),
    path('thread/<uuid:thread_id>/', ThreadDetailView.as_view(), name='thread-detail'),
    path('<uuid:user_id>/send/', SendMessageView.as_view(), name='send-message'),
    #for testing purposes
    path('', MessagingView.as_view(), name='messaging-home'),
    path('<uuid:message_id>/edit/', MessageEditView.as_view(), name='edit-message'),
    path('<uuid:message_id>/delete/', MessageDeleteView.as_view(), name='delete-message'),
    path('delete-all/', DeleteAllThreadsView.as_view(), name='delete-all-threads'),
    path('delete-thread/<uuid:thread_id>/', DeleteThreadView.as_view(), name='delete-thread'),
    
]