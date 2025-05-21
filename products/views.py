from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
import json
from decimal import Decimal

from .models import Product, Cart, Favorite, Category


# Create your views here.
def index(request):
    products = Product.objects.all()
    favorites = []
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
    return render(request, 'products/index.html', {
        'products': products,
        'favorites': favorites
    })
    

def new_product(request):
    return HttpResponse("Hello, world. You're at the new product page.")    

@login_required
@require_POST
def add_to_cart(request, product_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)
        
        if quantity <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Quantity must be greater than 0'
            })
        
        if quantity > product.stock:
            return JsonResponse({
                'status': 'error',
                'message': 'Not enough stock available'
            })
        
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Not enough stock available'
                })
            cart_item.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Product added to cart successfully'
        })
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid quantity value'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Item removed from cart successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
@require_POST
def update_cart(request, item_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        
        if quantity <= 0:
            return JsonResponse({
                'status': 'error',
                'message': 'Quantity must be greater than 0'
            })
        
        if quantity > cart_item.product.stock:
            return JsonResponse({
                'status': 'error',
                'message': 'Not enough stock available'
            })
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Cart updated successfully'
        })
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid quantity value'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    tax = total_price * Decimal('0.1')  # 10% tax
    total_with_tax = total_price + tax
    
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'tax': tax,
        'total_with_tax': total_with_tax
    })

@login_required
@require_POST
def toggle_favorite(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            favorite.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Product removed from favorites'
            })
        
        return JsonResponse({
            'status': 'success',
            'message': 'Product added to favorites'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required
def view_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('product')
    return render(request, 'products/favorites.html', {
        'favorites': favorites
    })

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'products/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'products/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'products/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'products/register.html')
        
        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('home')
    
    return render(request, 'products/register.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('home')

def product_list(request):
    # Get all categories for the filter
    categories = Category.objects.all()
    
    # Get the selected category from the query parameters
    category_id = request.GET.get('category')
    
    # Base queryset
    products = Product.objects.all()
    
    # Apply category filter if a category is selected
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Get user's favorites if authenticated
    favorites = []
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user).values_list('product_id', flat=True)
    
    return render(request, 'products/product_list.html', {
        'products': products,
        'favorites': favorites,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None
    })

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'products/categories.html', {
        'categories': categories
    })
        