from django.contrib import admin
from .models import Product, Order, OrderItem, Wishlist


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "price",
        "stock",
        "created_at",
    )
    search_fields = ("name", "category")
    list_filter = ("category",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "customer_name",
        "phone",
        "total_amount",
        "created_at",
    )
    search_fields = (
        "customer_name",
        "phone",
        "user__username",
    )
    inlines = [OrderItemInline]


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product",
        "created_at",
    )
    search_fields = (
        "user__username",
        "product__name",
    )