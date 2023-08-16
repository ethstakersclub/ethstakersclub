from django.shortcuts import render, redirect
from users.forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from api.util import get_validator_limit
import json
import re


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Handle CAPTCHA validation here (e.g., using reCAPTCHA)
            # If the CAPTCHA validation fails, return an error or redirect back to the registration page.

            form.save()
            return redirect('registration_success')
    else:
        form = RegistrationForm()
    return render(request, 'registration.html', {'form': form})


@login_required
def save_watched_validators(request):
    try:
        data = json.loads(request.body)
        validator_ids = data.get('validator_ids', [])

        if len(validator_ids) > get_validator_limit(request):
            return JsonResponse({'status': 'error', 'message': 'Too many validators added.'})

        public_keys_pattern = re.compile(r'^(0x)?[0-9a-fA-F]{96}$')

        # Check if all values are positive integers
        for validator_id in validator_ids:
            if not public_keys_pattern.match(str(validator_id)) and (not isinstance(validator_id, int) or validator_id <= 0):
                return JsonResponse({'status': 'error', 'message': 'Invalid validator ID provided.'})

        # Remove duplicate values
        unique_array = list(set(validator_ids))

        request.user.profile.watched_validators = ','.join(str(x) for x in unique_array)
        request.user.profile.save()

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data provided.'})