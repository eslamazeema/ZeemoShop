from django.contrib import admin
from .models import Product, Offer, Category

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    ordering = ('name',)

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'category__name')
    list_filter = ('category', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 10

class OfferAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'discount')
    search_fields = ('code',)
    list_filter = ('discount',)
    ordering = ('-discount',)
    list_per_page = 10

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Offer, OfferAdmin)

# Register your models here. 