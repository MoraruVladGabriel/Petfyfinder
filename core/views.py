from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

from item.models import Category, Item

from .models import Profile

from .forms import SignupForm

# Create your views here.

def index(request):
    items = Item.objects.filter(is_adopted=False)[0:6]
    categories = Category.objects.all()
    return render(request, 'core/index.html', {
        'categories': categories,
        'items': items,
    })

# def signup(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)

#         if form.is_valid():
#             form.save()

#             return redirect('/login/')
#     else:
#         form = SignupForm()

#     return render(request, 'core/signup.html', {
#         'form': form
#     })

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Creează și salvează profilul direct în vizualizare
            location = form.cleaned_data.get('user_location')
            Profile.objects.create(user=user, location=location)
            
            return redirect('/login/')  # Redirect to a success page.
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def contact(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        message = request.POST['message']

        send_mail(
            f"New Contact Message from {name}",
            message,
            email,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )

        messages.success(request, 'Thank you for your message. We will get back to you shortly.')
        return redirect('core:contact')
    
    return render(request, 'core/contact.html')

def about(request):
    return render(request, 'core/about.html')

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')

def terms_of_use(request):
    return render(request, 'core/term_of_use.html')

@login_required
def profile(request):
    return render(request, 'core/profile.html', {'profile': request.user.profile})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        user = request.user
        profile = user.profile
        user.username = request.POST['username']
        user.email = request.POST['email']
        profile.location = request.POST['location']
        user.save()
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('core:profile')

    return render(request, 'core/profile_edit.html', {'profile': request.user.profile})
