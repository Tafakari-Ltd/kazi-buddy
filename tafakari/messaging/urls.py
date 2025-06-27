from django.urls import path
from .views import ThreadListView, ThreadDetailView, SendMessageView, StartThreadView, MessagingView,MessageEditView,MessageDeleteView,DeleteThreadView,DeleteAllMessagesInThreadView,DeleteAllMessagesByUserView,DeleteAllMessagesView,DeleteAllThreadsByUserView,DeleteAllThreadsForTestingView

urlpatterns = [
    path('all/', ThreadListView.as_view(), name='list-threads'),
    path('thread/<uuid:thread_id>/', ThreadDetailView.as_view(), name='thread-detail'),
    path('<uuid:user_id>/send/', SendMessageView.as_view(), name='send-message'),
    #for testing purposes
    path('', MessagingView.as_view(), name='messaging-home'),
    path('<uuid:message_id>/edit/', MessageEditView.as_view(), name='edit-message'),
    path('<uuid:message_id>/delete/', MessageDeleteView.as_view(), name='delete-message'),
    path('delete-all/', DeleteAllThreadsForTestingView.as_view(), name='delete-all-threads'),
    path('delete-thread/<uuid:thread_id>/', DeleteThreadView.as_view(), name='delete-thread'),
    path('delete-all-messages-in-thread/<uuid:thread_id>/', DeleteAllMessagesInThreadView.as_view(), name='delete-all-messages-in-thread'),
    path('delete-all-messages-by-user/<uuid:user_id>/', DeleteAllMessagesByUserView.as_view(), name='delete-all-messages-by-user'),
    path('delete-all-messages/', DeleteAllMessagesView.as_view(), name='delete-all-messages'),
    path('delete-all-threads-by-user/<uuid:user_id>/', DeleteAllThreadsByUserView.as_view(), name='delete-all-threads-by-user'),
    path('start-thread/', StartThreadView.as_view()),
    

]