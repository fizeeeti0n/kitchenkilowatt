from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect('home')
        else:
            messages.error(request, 'Unsuccessful registration. Invalid information.')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    """Custom logout view that handles both GET and POST, then shows the logged-out page."""
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'accounts/logged_out.html')

@login_required
def profile_view(request):
    user = request.user
    address = Address.objects.filter(user=user, is_default=True).first()
    if not address:
        address = Address.objects.filter(user=user).first()
    if not address:
        address = Address(user=user, is_default=True)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.save()

        address.full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        address.phone = user.phone_number or ''
        address.street_address = request.POST.get('street_address', address.street_address or '')
        address.city = request.POST.get('city', address.city or '')
        address.state = request.POST.get('state', address.state or '')
        address.postal_code = request.POST.get('postal_code', address.postal_code or '')
        address.country = request.POST.get('country', address.country or 'United States')
        address.is_default = True
        address.save()

        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user': user,
        'address': address
    })
