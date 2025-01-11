from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from item.models import Item

from .forms import ConversationMessageForm
from .models import Conversation, ConversationMessage

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer # type: ignore

import logging

from django.http import JsonResponse

# Create your views here.

@login_required
def new_conversation(request, item_pk):
    item = get_object_or_404(Item, pk=item_pk)

    if item.created_by == request.user:
        return redirect('dashboard:index')
    
    conversations = Conversation.objects.filter(item=item).filter(members__in=[request.user.id])

    if conversations:
        return redirect('conversation:detail', pk=conversations.first().id)

    if request.method == 'POST':
        form = ConversationMessageForm(request.POST)

        if form.is_valid():
            conversation = Conversation.objects.create(item=item)
            conversation.members.add(request.user)
            conversation.members.add(item.created_by)
            conversation.save()

            conversation_message = form.save(commit=False)
            conversation_message.conversation = conversation
            conversation_message.created_by = request.user
            conversation_message.save()

            return redirect('item:detail', pk=item_pk)
    else:
        form = ConversationMessageForm()

    return render(request, 'conversation/new.html', {
        'form': form
    })

@login_required
def inbox(request):
    conversations = Conversation.objects.filter(members__in=[request.user.id])

    return render(request, 'conversation/inbox.html', {
        'conversations': conversations
    })

# @login_required
# def detail(request, pk):
#     conversation = Conversation.objects.filter(members__in=[request.user.id]).get(pk=pk)

#     if request.method == 'POST':
#         form = ConversationMessageForm(request.POST)

#         if form.is_valid():
#             conversation_message = form.save(commit=False)
#             conversation_message.conversation = conversation
#             conversation_message.created_by = request.user
#             conversation_message.save()

#             conversation.save()

#             return redirect('conversation:detail', pk=pk)
#     else:
#         form = ConversationMessageForm()

#     return render(request, 'conversation/detail.html', {
#         'conversation': conversation,
#         'form': form
#     })

logger = logging.getLogger(__name__)

# @login_required
# def detail(request, pk):
#     logger.debug("Entering detail view")
#     conversation = get_object_or_404(Conversation, members__in=[request.user.id], pk=pk)
#     logger.debug("Fetched conversation: %s", conversation)

#     if request.method == 'POST':
#         logger.debug("POST request")
#         form = ConversationMessageForm(request.POST)
#         logger.debug("Form data: %s", request.POST)

#         if form.is_valid():
#             logger.debug("Form is valid")
#             conversation_message = form.save(commit=False)
#             conversation_message.conversation = conversation
#             conversation_message.created_by = request.user
#             conversation_message.save()
#             logger.info("Message saved successfully: %s", conversation_message.content)

#             # Send message through WebSocket
#             channel_layer = get_channel_layer()
#             async_to_sync(channel_layer.group_send)(
#                 f'chat_{pk}',
#                 {
#                     'type': 'chat_message',
#                     'message': conversation_message.content,
#                     'username': conversation_message.created_by.username,
#                 }
#             )
#             logger.info("Message sent to WebSocket: %s", conversation_message.content)

#             return redirect('conversation:detail', pk=pk)
#         else:
#             logger.error("Form is not valid: %s", form.errors)
#     else:
#         logger.debug("GET request")
#         form = ConversationMessageForm()

#     return render(request, 'conversation/detail.html', {
#         'conversation': conversation,
#         'form': form
#     })

@login_required
def detail(request, pk):
    conversation = get_object_or_404(Conversation, members__in=[request.user.id], pk=pk)

    if request.method == 'POST':
        form = ConversationMessageForm(request.POST)
        if form.is_valid():
            conversation_message = form.save(commit=False)
            conversation_message.conversation = conversation
            conversation_message.created_by = request.user
            conversation_message.save()
            logger.info("Message saved successfully")

            # Send message through WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{pk}',
                {
                    'type': 'chat_message',
                    'message': conversation_message.content,
                    'username': conversation_message.created_by.username,
                }
            )

            # Return JSON response for AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': conversation_message.content,
                    'username': conversation_message.created_by.username,
                })

            return redirect('conversation:detail', pk=pk)
        else:
            logger.error("Form is not valid")
    else:
        form = ConversationMessageForm()

    return render(request, 'conversation/detail.html', {
        'conversation': conversation,
        'form': form,
    })