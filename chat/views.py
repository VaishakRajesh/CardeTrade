"""
chat/views.py

Provides an API endpoint for the AI-powered chatbot assistant.
Users send messages and receive AI-generated responses with
optional database context (listings, batches, orders, etc.).
"""

import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .services.chatbot import SYSTEM_PROMPT, get_db_context, call_openrouter, format_response


@method_decorator(login_required, name='dispatch')
# API endpoint that accepts a user message and returns an AI-generated response with DB context
class ChatBotAPIView(View):
    # Parse the incoming message, build the prompt with DB context, and return the AI reply
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            message = data.get('message', '').strip()
        except (json.JSONDecodeError, AttributeError):
            message = request.POST.get('message', '').strip()

        if not message:
            return JsonResponse({'response': 'Please enter a message.'})

        now = timezone.now()
        system_prompt = SYSTEM_PROMPT.format(current_date=now.strftime('%B %d, %Y'))
        db_context = get_db_context(request.user, message)

        messages_list = [
            {'role': 'system', 'content': system_prompt},
        ]
        if db_context:
            messages_list.append({
                'role': 'system',
                'content': f'The following data has been fetched from the database to answer the user\'s question:\n\n{db_context}'
            })
        messages_list.append({'role': 'user', 'content': message})

        raw_response = call_openrouter(messages_list)
        response_text = format_response(raw_response)

        return JsonResponse({'response': response_text})
